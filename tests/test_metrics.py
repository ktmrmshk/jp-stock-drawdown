from __future__ import annotations

import datetime

import pandas as pd
import pytest

from jp_stock_drawdown.errors import NoDataError
from jp_stock_drawdown.metrics import compute_stats


def _frame(dates: list[datetime.date], closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": closes,
            "High": closes,
            "Low": closes,
            "Close": closes,
            "Volume": [1000] * len(closes),
        },
        index=pd.DatetimeIndex(dates),
    )


class TestComputeStats:
    def test_ac10_golden(self):
        dates = [datetime.date(2026, 1, d) for d in (1, 2, 3, 4, 5)]
        stats = compute_stats(_frame(dates, [100, 120, 110, 130, 90]))
        assert stats.highest_price == 130.0
        assert stats.lowest_price == 90.0
        assert stats.current_price == 90.0
        assert stats.drawdown_pct == -30.7692
        assert stats.highest_date == datetime.date(2026, 1, 4)
        assert stats.lowest_date == datetime.date(2026, 1, 5)
        assert stats.as_of == datetime.date(2026, 1, 5)
        assert stats.highest_days_ago == 1
        assert stats.lowest_days_ago == 0

    def test_sample_history_golden_tail(self, sample_history_df):
        stats = compute_stats(sample_history_df.tail(5))
        assert stats.highest_price == 130.0
        assert stats.lowest_price == 90.0
        assert stats.current_price == 90.0
        assert stats.drawdown_pct == -30.7692
        assert stats.highest_days_ago == 1
        assert stats.lowest_days_ago == 0

    def test_ac11_nan_dropped(self):
        dates = [datetime.date(2026, 1, d) for d in (1, 2, 3, 4, 5)]
        stats = compute_stats(_frame(dates, [100, float("nan"), 110, 130, 90]))
        assert stats.highest_price == 130.0
        assert stats.lowest_price == 90.0
        assert stats.current_price == 90.0

    def test_ac12_empty(self):
        df = pd.DataFrame({"Close": []})
        with pytest.raises(NoDataError):
            compute_stats(df)

    def test_ac13_single_row(self):
        df = _frame([datetime.date(2026, 1, 5)], [150])
        stats = compute_stats(df)
        assert stats.highest_price == 150.0
        assert stats.lowest_price == 150.0
        assert stats.current_price == 150.0
        assert stats.drawdown_pct == 0.0
        assert stats.as_of == datetime.date(2026, 1, 5)
        assert stats.highest_date == datetime.date(2026, 1, 5)
        assert stats.lowest_date == datetime.date(2026, 1, 5)
        assert stats.highest_days_ago == 0
        assert stats.lowest_days_ago == 0

    def test_ac13b_highest_is_latest(self):
        dates = [datetime.date(2026, 1, 1), datetime.date(2026, 1, 5)]
        stats = compute_stats(_frame(dates, [100, 130]))
        assert stats.highest_date == datetime.date(2026, 1, 5)
        assert stats.highest_days_ago == 0
        assert stats.lowest_days_ago == 4

    def test_drawdown_positive_clamped_to_zero(self):
        dates = [datetime.date(2026, 1, 1), datetime.date(2026, 1, 2)]
        stats = compute_stats(_frame(dates, [100.0, 100.0000001]))
        assert stats.drawdown_pct == 0.0
