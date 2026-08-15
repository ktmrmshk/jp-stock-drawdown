from __future__ import annotations

import datetime

import pandas as pd
import pytest
from yfinance.exceptions import YFRateLimitError

from jp_stock_drawdown import fetcher
from jp_stock_drawdown.errors import DataFetchError, NoDataError, UsageError


class FakeTicker:
    def __init__(self, df, info=None, errors=None):
        self._df = df
        self._errors = list(errors or [])
        self.history_calls = []
        if info is not None:
            self.info = info

    def history(self, **kwargs):
        self.history_calls.append(kwargs)
        if self._errors:
            raise self._errors.pop(0)
        return self._df.copy()


class FailingInfoTicker(FakeTicker):
    @property
    def info(self):
        raise RuntimeError("info lookup failed")


def _install(monkeypatch, ticker):
    monkeypatch.setattr(fetcher.yf, "Ticker", lambda symbol: ticker)
    monkeypatch.setattr(fetcher, "RETRY_DELAY", 0)
    return ticker


class TestNormalizeSymbol:
    def test_ac04_four_digit(self):
        assert fetcher.normalize_symbol("7203") == "7203.T"

    def test_ac05_suffixed_kept(self):
        assert fetcher.normalize_symbol("7203.T") == "7203.T"
        assert fetcher.normalize_symbol("9984.OS") == "9984.OS"
        assert fetcher.normalize_symbol("7203.N") == "7203.N"

    @pytest.mark.parametrize("bad", ["abc", "12345", "7203.XX", "7203.x", "7203.9999"])
    def test_invalid_raises_usage_error(self, bad):
        with pytest.raises(UsageError):
            fetcher.normalize_symbol(bad)


class TestFetchHistory:
    def test_success(self, monkeypatch, sample_history_df):
        fake = _install(monkeypatch, FakeTicker(sample_history_df, info={"longName": "Toyota Motor Corp."}))
        df, name = fetcher.fetch_history("7203.T", period="1y")
        assert df.equals(sample_history_df)
        assert name == "Toyota Motor Corp."
        assert fake.history_calls[0]["auto_adjust"] is False
        assert fake.history_calls[0]["period"] == "1y"

    def test_start_end_takes_priority(self, monkeypatch, sample_history_df):
        fake = _install(monkeypatch, FakeTicker(sample_history_df))
        start = datetime.date(2025, 1, 1)
        end = datetime.date(2026, 1, 1)
        fetcher.fetch_history("7203.T", start=start, end=end)
        call = fake.history_calls[0]
        assert "period" not in call
        assert call["start"] == start
        assert call["end"] == end

    def test_default_period_is_max(self, monkeypatch, sample_history_df):
        fake = _install(monkeypatch, FakeTicker(sample_history_df))
        fetcher.fetch_history("7203.T")
        assert fake.history_calls[0]["period"] == "max"

    def test_no_name_skips_lookup(self, monkeypatch, sample_history_df):
        _install(monkeypatch, FakeTicker(sample_history_df, info={"longName": "X"}))
        df, name = fetcher.fetch_history("7203.T", fetch_name=False)
        assert name is None
        assert not df.empty

    def test_name_failure_ignored(self, monkeypatch, sample_history_df):
        _install(monkeypatch, FailingInfoTicker(sample_history_df))
        df, name = fetcher.fetch_history("7203.T")
        assert name is None
        assert not df.empty

    def test_empty_raises_no_data(self, monkeypatch):
        _install(monkeypatch, FakeTicker(pd.DataFrame()))
        with pytest.raises(NoDataError):
            fetcher.fetch_history("7203.T")

    def test_rate_limit_retries_once_then_succeeds(self, monkeypatch, sample_history_df):
        fake = _install(
            monkeypatch,
            FakeTicker(sample_history_df, errors=[YFRateLimitError()]),
        )
        df, _name = fetcher.fetch_history("7203.T")
        assert len(fake.history_calls) == 2
        assert not df.empty

    def test_rate_limit_exhausted(self, monkeypatch, sample_history_df):
        fake = _install(
            monkeypatch,
            FakeTicker(sample_history_df, errors=[YFRateLimitError(), YFRateLimitError()]),
        )
        with pytest.raises(DataFetchError) as excinfo:
            fetcher.fetch_history("7203.T")
        assert excinfo.value.rate_limited is True
        assert "rate limited" in str(excinfo.value)
        assert len(fake.history_calls) == 2

    def test_generic_error_no_retry(self, monkeypatch):
        fake = _install(monkeypatch, FakeTicker(pd.DataFrame(), errors=[ValueError("boom")]))
        with pytest.raises(DataFetchError) as excinfo:
            fetcher.fetch_history("7203.T")
        assert excinfo.value.rate_limited is False
        assert len(fake.history_calls) == 1
