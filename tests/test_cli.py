from __future__ import annotations

import datetime
import json

import pandas as pd
import pytest

from jp_stock_drawdown import cli
from jp_stock_drawdown.errors import DataFetchError, NoDataError

_TABLE_HEADERS = (
    "Symbol", "Name", "Current", "AsOf", "High", "HighDate",
    "HighAgo", "Low", "LowDate", "LowAgo", "Drawdown",
)


def _golden_df() -> pd.DataFrame:
    dates = pd.DatetimeIndex([datetime.date(2026, 1, d) for d in (1, 2, 3, 4, 5)])
    closes = [100.0, 120.0, 110.0, 130.0, 90.0]
    return pd.DataFrame(
        {"Open": closes, "High": closes, "Low": closes, "Close": closes, "Volume": [1000] * 5},
        index=dates,
    )


def _install_fake_fetch(monkeypatch, sample_history_df, failures=None):
    failures = failures or {}

    def _fetch(symbol, **kwargs):
        kind = failures.get(symbol)
        if kind == "no_data":
            raise NoDataError(f"no data for {symbol} (symbol may be invalid or delisted)")
        if kind == "fetch_failed":
            raise DataFetchError(f"failed to fetch history for {symbol}: boom")
        if kind == "rate_limited":
            raise DataFetchError(f"rate limited while fetching {symbol}: boom", rate_limited=True)
        return sample_history_df.copy(), "Toyota Motor Corp."

    monkeypatch.setattr(cli, "fetch_history", _fetch)
    monkeypatch.setattr(cli, "_SLEEP_BETWEEN_TICKERS", 0)


class TestLifecycle:
    def test_ac01_main_help(self, capsys):
        assert cli.main(["--help"]) == 0
        out = capsys.readouterr().out
        assert "quote" in out
        assert "skill" in out

    def test_ac01_quote_help(self, capsys):
        assert cli.main(["quote", "--help"]) == 0
        out = capsys.readouterr().out
        for option in ("--format", "--period", "--start", "--end", "-o", "--output", "--no-name", "--verbose"):
            assert option in out

    def test_ac02_version(self, capsys):
        assert cli.main(["-V"]) == 0
        assert capsys.readouterr().out.strip() == f"jp-stock-drawdown {cli.__version__}"

    def test_ac02_version_long(self, capsys):
        assert cli.main(["--version"]) == 0
        assert capsys.readouterr().out.strip() == f"jp-stock-drawdown {cli.__version__}"


class TestArgumentValidation:
    @pytest.mark.parametrize("bad", ["abc", "12345"])
    def test_ac06_invalid_ticker(self, bad, capsys):
        assert cli.main(["quote", bad]) == 2
        assert bad in capsys.readouterr().err

    def test_ac07_no_tickers(self):
        assert cli.main(["quote"]) == 2

    def test_ac08_invalid_period(self):
        assert cli.main(["quote", "7203", "--period", "3y"]) == 2

    def test_ac09_invalid_date(self):
        assert cli.main(["quote", "7203", "--start", "2024-13-01"]) == 2

    def test_ac09_start_after_end(self, capsys):
        assert cli.main(["quote", "7203", "--start", "2025-01-01", "--end", "2024-01-01"]) == 2
        assert "start" in capsys.readouterr().err


class TestQuote:
    def test_ac03_default_command(self, monkeypatch, capsys, sample_history_df):
        _install_fake_fetch(monkeypatch, sample_history_df)
        assert cli.main(["7203"]) == 0
        assert "7203.T" in capsys.readouterr().out

    def test_ac14_table(self, monkeypatch, capsys, sample_history_df):
        _install_fake_fetch(monkeypatch, sample_history_df)
        assert cli.main(["quote", "7203"]) == 0
        out = capsys.readouterr().out
        for header in _TABLE_HEADERS:
            assert header in out
        assert "-30.8%" in out
        assert "d ago" in out
        assert not any("\u3040" <= ch <= "\u30ff" or "\u4e00" <= ch <= "\u9fff" for ch in out)

    def test_ac15_json(self, monkeypatch, capsys, sample_history_df):
        _install_fake_fetch(monkeypatch, sample_history_df)
        assert cli.main(["quote", "7203", "--format", "json"]) == 0
        doc = json.loads(capsys.readouterr().out)
        quote = doc["quotes"][0]
        assert doc["command"] == "quote"
        assert quote["symbol"] == "7203.T"
        assert quote["ticker"] == "7203"
        assert isinstance(quote["drawdown_pct"], float)
        assert isinstance(quote["highest_days_ago"], int)
        assert isinstance(quote["lowest_days_ago"], int)
        assert quote["as_of"] == "2026-01-07"
        assert "quotes" in doc

    def test_ac16_multiple_tickers_order(self, monkeypatch, capsys, sample_history_df):
        _install_fake_fetch(monkeypatch, sample_history_df)
        assert cli.main(["quote", "7203", "6758", "--format", "json"]) == 0
        doc = json.loads(capsys.readouterr().out)
        assert len(doc["quotes"]) == 2
        assert [q["ticker"] for q in doc["quotes"]] == ["7203", "6758"]

    def test_ac17_file_output(self, monkeypatch, capsys, tmp_path, sample_history_df):
        _install_fake_fetch(monkeypatch, sample_history_df)
        outfile = tmp_path / "result.json"
        assert cli.main(["quote", "7203", "--format", "json", "-o", str(outfile)]) == 0
        assert outfile.exists()
        file_doc = json.loads(outfile.read_text())
        assert cli.main(["quote", "7203", "--format", "json"]) == 0
        assert file_doc == json.loads(capsys.readouterr().out)


class TestErrorHandling:
    def test_ac18_partial_failure(self, monkeypatch, capsys, sample_history_df):
        _install_fake_fetch(monkeypatch, sample_history_df, failures={"0000.T": "no_data"})
        assert cli.main(["quote", "7203", "0000", "--format", "json"]) == 0
        doc = json.loads(capsys.readouterr().out)
        assert [q["ticker"] for q in doc["quotes"]] == ["7203"]
        assert doc["errors"] == [
            {"ticker": "0000", "error": "no_data", "message": "no data for 0000.T (symbol may be invalid or delisted)"}
        ]

    def test_ac18_partial_table_reports_stderr(self, monkeypatch, capsys, sample_history_df):
        _install_fake_fetch(monkeypatch, sample_history_df, failures={"0000.T": "no_data"})
        assert cli.main(["quote", "7203", "0000"]) == 0
        captured = capsys.readouterr()
        assert "7203.T" in captured.out
        assert "no data for 0000.T" in captured.err

    def test_ac19_all_no_data_json(self, monkeypatch, capsys, sample_history_df):
        _install_fake_fetch(monkeypatch, sample_history_df, failures={"0000.T": "no_data"})
        assert cli.main(["quote", "0000", "--format", "json"]) == 4
        doc = json.loads(capsys.readouterr().out)
        assert doc["quotes"] == []
        assert doc["errors"][0]["error"] == "no_data"

    def test_ac19_all_no_data_table(self, monkeypatch, capsys, sample_history_df):
        _install_fake_fetch(monkeypatch, sample_history_df, failures={"0000.T": "no_data"})
        assert cli.main(["quote", "0000"]) == 4
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "no data for 0000.T" in captured.err

    def test_ac20_fetch_failure(self, monkeypatch, capsys, sample_history_df):
        _install_fake_fetch(monkeypatch, sample_history_df, failures={"7203.T": "fetch_failed"})
        assert cli.main(["quote", "7203"]) == 3
        assert "7203" in capsys.readouterr().err

    def test_rate_limited(self, monkeypatch, capsys, sample_history_df):
        _install_fake_fetch(monkeypatch, sample_history_df, failures={"7203.T": "rate_limited"})
        assert cli.main(["quote", "7203", "--format", "json"]) == 3
        doc = json.loads(capsys.readouterr().out)
        assert doc["errors"][0]["error"] == "rate_limited"

    def test_mixed_no_data_and_fetch_is_3(self, monkeypatch, capsys, sample_history_df):
        _install_fake_fetch(
            monkeypatch,
            sample_history_df,
            failures={"0000.T": "no_data", "9999.T": "fetch_failed"},
        )
        assert cli.main(["quote", "0000", "9999", "--format", "json"]) == 3
