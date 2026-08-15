from __future__ import annotations

import datetime
import json

from jp_stock_drawdown.formatter import format_json, format_table
from jp_stock_drawdown.model import DrawdownReport, ErrorEntry, QuoteResult, QuoteStats


def _stats() -> QuoteStats:
    return QuoteStats(
        as_of=datetime.date(2026, 8, 14),
        highest_price=3200.0,
        lowest_price=1500.0,
        current_price=2890.5,
        drawdown_pct=-9.6719,
        highest_date=datetime.date(2025, 1, 15),
        lowest_date=datetime.date(2024, 8, 5),
        highest_days_ago=576,
        lowest_days_ago=739,
    )


def _quote(ticker="7203", symbol="7203.T", name="Toyota Motor Corp.") -> QuoteResult:
    return QuoteResult(
        ticker=ticker,
        symbol=symbol,
        name=name,
        currency="JPY",
        stats=_stats(),
        data_start=datetime.date(2013, 1, 1),
        data_end=datetime.date(2026, 8, 14),
    )


def _report(quotes=(), errors=()) -> DrawdownReport:
    return DrawdownReport(
        command="quote",
        generated_at=datetime.date(2026, 8, 15),
        period_specified="max",
        period_start=datetime.date(2013, 1, 1),
        period_end=datetime.date(2026, 8, 14),
        quotes=list(quotes),
        errors=list(errors),
    )


_JAPANESE = {chr(code) for code in range(0x3040, 0x30FF + 1)} | {
    chr(code) for code in range(0x4E00, 0x9FFF + 1)
}


class TestFormatTable:
    def test_ac14_headers_and_cells(self):
        out = format_table(_report(quotes=[_quote()]))
        for header in (
            "Symbol", "Name", "Current", "AsOf", "High", "HighDate",
            "HighAgo", "Low", "LowDate", "LowAgo", "Drawdown",
        ):
            assert header in out
        assert "7203.T" in out
        assert "Toyota Motor Corp." in out
        assert "2,890.50" in out
        assert "3,200.00" in out
        assert "1,500.00" in out
        assert "2026-08-14" in out
        assert "2025-01-15" in out
        assert "576d ago" in out
        assert "739d ago" in out
        assert "-9.7%" in out

    def test_no_name_uses_dash(self):
        out = format_table(_report(quotes=[_quote(name=None)]))
        assert "-" in out.splitlines()[1]

    def test_no_japanese(self):
        out = format_table(_report(quotes=[_quote()]))
        assert not any(ch in _JAPANESE for ch in out)

    def test_empty_report_headers_only(self):
        out = format_table(_report())
        assert "Symbol" in out
        assert len(out.splitlines()) == 1


class TestFormatJson:
    def test_ac15_schema(self):
        doc = json.loads(format_json(_report(quotes=[_quote()])))
        assert doc["command"] == "quote"
        assert doc["generated_at"] == "2026-08-15"
        assert doc["period"] == {
            "specified": "max",
            "start": "2013-01-01",
            "end": "2026-08-14",
        }
        quote = doc["quotes"][0]
        assert quote["ticker"] == "7203"
        assert quote["symbol"] == "7203.T"
        assert quote["name"] == "Toyota Motor Corp."
        assert quote["currency"] == "JPY"
        assert quote["as_of"] == "2026-08-14"
        assert quote["current_price"] == 2890.5
        assert quote["highest_price"] == 3200.0
        assert quote["lowest_price"] == 1500.0
        assert quote["drawdown_pct"] == -9.6719
        assert isinstance(quote["drawdown_pct"], float)
        assert isinstance(quote["highest_days_ago"], int)
        assert isinstance(quote["lowest_days_ago"], int)
        assert quote["highest_date"] == "2025-01-15"
        assert quote["highest_days_ago"] == 576
        assert quote["lowest_date"] == "2024-08-05"
        assert quote["lowest_days_ago"] == 739
        assert doc["errors"] == []

    def test_quotes_key_present_when_empty(self):
        doc = json.loads(format_json(_report()))
        assert doc["quotes"] == []
        assert doc["errors"] == []

    def test_ac16_multiple_quotes_keep_order(self):
        report = _report(quotes=[_quote(ticker="7203", symbol="7203.T"), _quote(ticker="6758", symbol="6758.T")])
        doc = json.loads(format_json(report))
        assert len(doc["quotes"]) == 2
        assert [q["ticker"] for q in doc["quotes"]] == ["7203", "6758"]

    def test_errors_listed(self):
        error = ErrorEntry(ticker="0000", error="no_data", message="no data for 0000.T")
        doc = json.loads(format_json(_report(quotes=[_quote()], errors=[error])))
        assert doc["errors"] == [
            {"ticker": "0000", "error": "no_data", "message": "no data for 0000.T"}
        ]

    def test_name_null_when_missing(self):
        doc = json.loads(format_json(_report(quotes=[_quote(name=None)])))
        assert doc["quotes"][0]["name"] is None
