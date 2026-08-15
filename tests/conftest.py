from __future__ import annotations

import os

import pandas as pd
import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def sample_history_df() -> pd.DataFrame:
    path = os.path.join(FIXTURES_DIR, "sample_history.csv")
    return pd.read_csv(path, index_col=0, parse_dates=True)
