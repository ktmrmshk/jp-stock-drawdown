from __future__ import annotations

import argparse
import datetime
import sys
import time
import traceback

from jp_stock_drawdown import __version__
from jp_stock_drawdown.errors import (
    DataFetchError,
    JpStockDrawdownError,
    NoDataError,
    UsageError,
)
from jp_stock_drawdown.fetcher import fetch_history, normalize_symbol
from jp_stock_drawdown.formatter import format_json, format_table
from jp_stock_drawdown.metrics import compute_stats, to_date
from jp_stock_drawdown.model import DrawdownReport, ErrorEntry, QuoteResult
from jp_stock_drawdown.skill import install_skill

PERIOD_CHOICES = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"]
_COMMANDS = {"quote", "skill"}
_GLOBAL_FLAGS = {"-h", "--help", "-V", "--version"}
_SLEEP_BETWEEN_TICKERS = 0.5


def _parse_date(value: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid date: '{value}' (expect yyyy-mm-dd)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jp-dd",
        description="Japanese stock price drawdown analyzer",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"jp-stock-drawdown {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command")

    quote = subparsers.add_parser(
        "quote",
        help="Show highest/lowest/current price and drawdown %%",
    )
    quote.add_argument(
        "tickers",
        nargs="+",
        metavar="tickers",
        help="4-digit Japanese stock code (e.g. 7203) or Yahoo symbol (e.g. 7203.T)",
    )
    quote.add_argument(
        "--period",
        choices=PERIOD_CHOICES,
        default="max",
        help="History period (default: %(default)s)",
    )
    quote.add_argument(
        "--start",
        type=_parse_date,
        metavar="YYYY-MM-DD",
        help="Fetch start date (yyyy-mm-dd)",
    )
    quote.add_argument(
        "--end",
        type=_parse_date,
        metavar="YYYY-MM-DD",
        help="Fetch end date (yyyy-mm-dd)",
    )
    quote.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format (default: %(default)s)",
    )
    quote.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help="Write output to FILE instead of stdout",
    )
    quote.add_argument(
        "--no-name",
        action="store_true",
        help="Skip company name lookup (faster)",
    )
    quote.add_argument(
        "--verbose",
        action="store_true",
        help="Print diagnostics to stderr",
    )

    skill = subparsers.add_parser("skill", help="Manage the agent skill (install)")
    skill_subparsers = skill.add_subparsers(dest="skill_command")
    install = skill_subparsers.add_parser("install", help="Install the agent skill to a directory")
    install.add_argument(
        "--dir",
        default="~/.config/opencode/skills",
        help="Base skill directory (default: %(default)s)",
    )
    install.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing file",
    )
    return parser


def _inject_default_command(argv: list[str]) -> list[str]:
    if not argv:
        return ["quote"]
    if argv[0] in _GLOBAL_FLAGS:
        return argv
    if argv[0] not in _COMMANDS:
        return ["quote"] + argv
    return argv


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    argv = _inject_default_command(argv)
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)
    try:
        if args.command == "quote":
            return _run_quote(args)
        if args.command == "skill":
            return _run_skill(args)
        raise UsageError("missing command")
    except JpStockDrawdownError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # noqa: BLE001 - top-level catch-all per SPEC 06
        if getattr(args, "verbose", False):
            traceback.print_exc()
        print(f"error: unexpected error: {exc}", file=sys.stderr)
        return 1


def _run_quote(args: argparse.Namespace) -> int:
    if args.start and args.end and args.start > args.end:
        raise UsageError("--start must be on or before --end")
    pairs = [(ticker, normalize_symbol(ticker)) for ticker in args.tickers]
    use_dates = args.start is not None or args.end is not None

    results: list[QuoteResult] = []
    errors: list[ErrorEntry] = []
    for index, (ticker, symbol) in enumerate(pairs):
        if index > 0:
            time.sleep(_SLEEP_BETWEEN_TICKERS)
        try:
            df, name = fetch_history(
                symbol,
                period=None if use_dates else args.period,
                start=args.start,
                end=args.end,
                fetch_name=not args.no_name,
                verbose=args.verbose,
            )
            stats = compute_stats(df)
            closes = df["Close"].dropna()
            results.append(
                QuoteResult(
                    ticker=ticker,
                    symbol=symbol,
                    name=name,
                    currency="JPY",
                    stats=stats,
                    data_start=to_date(closes.index[0]),
                    data_end=to_date(closes.index[-1]),
                )
            )
        except NoDataError as exc:
            errors.append(ErrorEntry(ticker=ticker, error="no_data", message=str(exc)))
        except DataFetchError as exc:
            error_kind = "rate_limited" if exc.rate_limited else "fetch_failed"
            errors.append(ErrorEntry(ticker=ticker, error=error_kind, message=str(exc)))

    report = DrawdownReport(
        command="quote",
        generated_at=datetime.date.today(),  # noqa: DTZ011 - date-only, no tz in output
        period_specified=args.period,
        period_start=min((q.data_start for q in results), default=None),
        period_end=max((q.data_end for q in results), default=None),
        quotes=results,
        errors=errors,
    )

    if args.format == "json":
        write_output(format_json(report), args.output)
    elif results:
        write_output(format_table(report), args.output)

    if args.format != "json":
        for error in errors:
            print(f"error: {error.message}", file=sys.stderr)

    return _exit_code(results, errors)


def _exit_code(results: list[QuoteResult], errors: list[ErrorEntry]) -> int:
    if results:
        return 0
    if any(error.error in ("fetch_failed", "rate_limited") for error in errors):
        return DataFetchError.exit_code
    if errors:
        return NoDataError.exit_code
    return 0


def _run_skill(args: argparse.Namespace) -> int:
    if args.skill_command != "install":
        raise UsageError("missing subcommand for 'skill' (expected 'install')")
    dest = install_skill(args.dir, args.force)
    print(f"Installed skill 'jp-stock-drawdown' to {dest}")
    return 0


def write_output(text: str, output_file: str | None = None) -> None:
    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as handle:
                handle.write(text)
        except OSError as exc:
            raise JpStockDrawdownError(f"failed to write output to {output_file}: {exc}") from exc
    else:
        sys.stdout.write(text)
