from __future__ import annotations

import json

from jp_stock_drawdown.model import DrawdownReport

_TABLE_HEADERS = [
    "Symbol",
    "Name",
    "Current",
    "AsOf",
    "High",
    "HighDate",
    "HighAgo",
    "Low",
    "LowDate",
    "LowAgo",
    "Drawdown",
]


def format_table(report: DrawdownReport) -> str:
    rows = []
    for quote in report.quotes:
        stats = quote.stats
        rows.append(
            [
                quote.symbol,
                quote.name or "-",
                f"{stats.current_price:,.2f}",
                stats.as_of.isoformat(),
                f"{stats.highest_price:,.2f}",
                stats.highest_date.isoformat(),
                f"{stats.highest_days_ago}d ago",
                f"{stats.lowest_price:,.2f}",
                stats.lowest_date.isoformat(),
                f"{stats.lowest_days_ago}d ago",
                f"{stats.drawdown_pct:.1f}%",
            ]
        )
    widths = [len(header) for header in _TABLE_HEADERS]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    lines = [_pad_row(_TABLE_HEADERS, widths)]
    lines.extend(_pad_row(row, widths) for row in rows)
    return "\n".join(lines) + "\n"


def _pad_row(cells: list[str], widths: list[int]) -> str:
    return "  ".join(cell.ljust(widths[index]) for index, cell in enumerate(cells)).rstrip()


def format_json(report: DrawdownReport) -> str:
    doc = {
        "command": report.command,
        "generated_at": report.generated_at.isoformat(),
        "period": {
            "specified": report.period_specified,
            "start": _iso_or_none(report.period_start),
            "end": _iso_or_none(report.period_end),
        },
        "quotes": [_quote_to_dict(quote) for quote in report.quotes],
        "errors": [
            {"ticker": error.ticker, "error": error.error, "message": error.message}
            for error in report.errors
        ],
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def _quote_to_dict(quote) -> dict:
    stats = quote.stats
    return {
        "ticker": quote.ticker,
        "symbol": quote.symbol,
        "name": quote.name,
        "currency": quote.currency,
        "as_of": stats.as_of.isoformat(),
        "current_price": stats.current_price,
        "highest_price": stats.highest_price,
        "lowest_price": stats.lowest_price,
        "drawdown_pct": stats.drawdown_pct,
        "highest_date": stats.highest_date.isoformat(),
        "highest_days_ago": stats.highest_days_ago,
        "lowest_date": stats.lowest_date.isoformat(),
        "lowest_days_ago": stats.lowest_days_ago,
    }


def _iso_or_none(value) -> str | None:
    return value.isoformat() if value else None
