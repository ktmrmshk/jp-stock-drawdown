from __future__ import annotations

import re
import sys
import time

import yfinance as yf
from yfinance.exceptions import YFRateLimitError

from jp_stock_drawdown.errors import DataFetchError, NoDataError, UsageError

_DIGITS4 = re.compile(r"^\d{4}$")
_SUFFIXED = re.compile(r"^\d{4}\.(T|N|F|S|OS)$")
RETRY_DELAY = 0.5
MAX_ATTEMPTS = 2


def normalize_symbol(ticker: str) -> str:
    if _DIGITS4.match(ticker):
        return f"{ticker}.T"
    if _SUFFIXED.match(ticker):
        return ticker
    raise UsageError(f"invalid ticker: '{ticker}' (expect 4-digit code or symbol like 7203.T)")


def fetch_history(
    symbol: str,
    *,
    period: str | None = None,
    start=None,
    end=None,
    fetch_name: bool = True,
    verbose: bool = False,
) -> tuple:
    if verbose:
        print(f"fetching {symbol} (period={period}, start={start}, end={end})", file=sys.stderr)
    started = time.monotonic()
    try:
        ticker = yf.Ticker(symbol)
    except Exception as exc:
        raise DataFetchError(f"failed to initialize {symbol}: {exc}") from exc

    kwargs = {"auto_adjust": False}
    if start is not None or end is not None:
        if start is not None:
            kwargs["start"] = start
        if end is not None:
            kwargs["end"] = end
    else:
        kwargs["period"] = period or "max"

    df = _history_with_retry(ticker, symbol, kwargs)
    if df is None or df.empty:
        raise NoDataError(f"no data for {symbol} (symbol may be invalid or delisted)")

    name = _fetch_name(ticker, symbol) if fetch_name else None
    if verbose:
        elapsed = time.monotonic() - started
        print(f"got {len(df)} rows for {symbol} in {elapsed:.2f}s", file=sys.stderr)
    return df, name


def _history_with_retry(ticker, symbol: str, kwargs: dict):
    last_error: BaseException | None = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            return ticker.history(**kwargs)
        except YFRateLimitError as exc:
            last_error = exc
            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY)
                continue
            raise DataFetchError(f"rate limited while fetching {symbol}: {exc}", rate_limited=True) from exc
        except Exception as exc:
            raise DataFetchError(f"failed to fetch history for {symbol}: {exc}") from exc
    raise DataFetchError(f"failed to fetch history for {symbol}: {last_error}")


def _fetch_name(ticker, symbol: str) -> str | None:
    try:
        info = ticker.info
        if not isinstance(info, dict):
            return None
        name = info.get("longName") or info.get("shortName") or info.get("name")
        return name if isinstance(name, str) and name.strip() else None
    except Exception:  # noqa: BLE001 - best-effort name lookup
        return None
