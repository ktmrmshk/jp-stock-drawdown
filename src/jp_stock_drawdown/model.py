from __future__ import annotations

import datetime
from dataclasses import dataclass, field


@dataclass
class QuoteStats:
    as_of: datetime.date
    highest_price: float
    lowest_price: float
    current_price: float
    drawdown_pct: float
    highest_date: datetime.date
    lowest_date: datetime.date
    highest_days_ago: int
    lowest_days_ago: int


@dataclass
class QuoteResult:
    ticker: str
    symbol: str
    name: str | None
    currency: str
    stats: QuoteStats
    data_start: datetime.date
    data_end: datetime.date


@dataclass
class ErrorEntry:
    ticker: str
    error: str
    message: str


@dataclass
class DrawdownReport:
    command: str
    generated_at: datetime.date
    period_specified: str
    period_start: datetime.date | None
    period_end: datetime.date | None
    quotes: list[QuoteResult] = field(default_factory=list)
    errors: list[ErrorEntry] = field(default_factory=list)
