from __future__ import annotations

import datetime

import pandas as pd

from jp_stock_drawdown.errors import NoDataError
from jp_stock_drawdown.model import QuoteStats

DRAWDOWN_PRECISION = 4


def to_date(ts: object) -> datetime.date:
    return pd.Timestamp(ts).date()


def compute_stats(df: pd.DataFrame) -> QuoteStats:
    if df.empty:
        raise NoDataError("no price data available")
    if "Close" not in df.columns:
        raise NoDataError("missing 'Close' column in price data")
    closes = df["Close"].dropna()
    if closes.empty:
        raise NoDataError("no closing price data available")
    highest = float(closes.max())
    lowest = float(closes.min())
    current = float(closes.iloc[-1])
    if highest == 0:
        raise NoDataError("highest price is zero; cannot compute drawdown")
    drawdown = round((current - highest) / highest * 100, DRAWDOWN_PRECISION)
    if drawdown > 0:
        drawdown = 0.0
    as_of = to_date(closes.index[-1])
    highest_date = to_date(closes.idxmax())
    lowest_date = to_date(closes.idxmin())
    return QuoteStats(
        as_of=as_of,
        highest_price=highest,
        lowest_price=lowest,
        current_price=current,
        drawdown_pct=drawdown,
        highest_date=highest_date,
        lowest_date=lowest_date,
        highest_days_ago=(as_of - highest_date).days,
        lowest_days_ago=(as_of - lowest_date).days,
    )
