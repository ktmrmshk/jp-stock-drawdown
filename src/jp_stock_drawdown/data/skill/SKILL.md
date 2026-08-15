---
name: jp-stock-drawdown
description: Usage guide for the jp-dd CLI, a Japanese stock price drawdown analyzer.
  Use when asked about Japanese stock prices, all-time highs/lows, current price,
  or drawdown of listed companies (e.g. Toyota, 7203, Sony).
  Examples: "check Toyota's drawdown", "what are the high and current price of 7203".
---

# jp-stock-drawdown

## 1. Overview

`jp-dd` fetches Japanese stock price history (via Yahoo Finance / yfinance) and reports the
highest price, lowest price, current price, and current drawdown percentage over a chosen period.
Use it whenever a user asks about the price or drawdown of a Japanese listed company.

## 2. Setup (before running)

- Repository: `~/agent_sandbox/jp-stock-drawdown`
- Run with: `uv run jp-dd ...` (assumes `uv sync` has been run)
- If the project has not been synced yet:
  `cd ~/agent_sandbox/jp-stock-drawdown && uv sync`
- Remote usage (after publishing):
  `uvx --from git+https://github.com/OWNER/jp-stock-drawdown jp-dd ...`

## 3. Basic invocation

- `uv run jp-dd quote 7203` -> human-readable table
- `uv run jp-dd quote 7203 --format json` -> **use this form in agent workflows**
- `uv run jp-dd quote 7203 6758 --format json --period 5y`
- `uv run jp-dd 7203` -> same as `quote 7203` (quote is the default command)

## 4. Interpreting JSON output

- `quotes[]` holds successful results; `errors[]` holds failed tickers. Report failures; do not silently ignore them.
- `drawdown_pct` is negative (e.g. `-30.0` means 30% below the peak).
- `current_price` is the closing price as of `as_of`.
- `highest_date` / `lowest_date` are the dates when the high/low occurred.
- `highest_days_ago` / `lowest_days_ago` are calendar days since the latest data date.
- All dates use `yyyy-mm-dd` format.

## 5. Ticker conventions

- Japanese tickers: 4-digit code or `.T` suffix (e.g. `7203`, `7203.T`).
- 6-digit security codes (ETFs, indices, funds) are likely unsupported.

## 6. Error handling

- exit 2: argument error -> fix the invocation.
- exit 3: network / rate limit -> wait and retry.
- exit 4: no data -> verify the ticker code.

## 7. Practical tips

- Always fetch with `--format json` and format the table yourself.
- Use `--period 5y` (instead of full history) for faster responses.
- Use `--no-name` to skip company name lookup for speed.
- Respect rate limits: leave a gap between consecutive multi-ticker runs.
