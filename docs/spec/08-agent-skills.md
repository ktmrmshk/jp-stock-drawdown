# SPEC 08: Agent Skill Specification

- Status: Approved
- Target version: v1.0.0

## 1. Purpose

Provide an agent skill (`SKILL.md`) so that LLM agents can use the `jp-dd` CLI correctly. The skill lets an agent understand the correct commands, how to interpret the JSON output, and how to handle errors.

## 2. Skill Overview

| Item | Value |
|------|-------|
| Skill name | `jp-stock-drawdown` |
| Skill file | `SKILL.md` |
| Target CLI | `jp-dd` |
| Language | **English** (all skill content is written in English, matching the CLI) |
| Install method | `jp-dd skill install` (see SPEC 02) |
| Source of truth | `src/jp_stock_drawdown/data/skill/SKILL.md` (packaged inside the package) |
| Trigger | Questions/requests about Japanese stock prices, all-time highs/lows, or drawdown of listed companies |

> The skill is **packaged inside the Python package** and installed into the agent runtime directory via the CLI command `jp-dd skill install`. There is no manual copy step.
>
> Default install destination: `~/.config/opencode/skills/jp-stock-drawdown/SKILL.md` (overridable with `--dir`).

## 3. SKILL.md Structure (including frontmatter)

### 3.1 Frontmatter

```yaml
---
name: jp-stock-drawdown
description: Usage guide for the jp-dd CLI, a Japanese stock price drawdown analyzer.
  Use when asked about Japanese stock prices, all-time highs/lows, current price,
  or drawdown of listed companies (e.g. Toyota, 7203, Sony).
  Examples: "check Toyota's drawdown", "what are the high and current price of 7203".
---
```

### 3.2 Required body sections (written in English)

1. **Overview**: what the CLI does.
2. **Setup (before running)**:
   - Repository: `~/agent_sandbox/jp-stock-drawdown`
   - Run: `uv run jp-dd ...` (assumes `uv sync` has been run)
   - If not synced: `cd ~/agent_sandbox/jp-stock-drawdown && uv sync`
   - Remote usage: `uvx --from git+https://github.com/OWNER/jp-stock-drawdown jp-dd ...`
3. **Basic invocation**:
   - `uv run jp-dd quote 7203` → human-readable table
   - `uv run jp-dd quote 7203 --format json` → **use this form in agent workflows**
   - `uv run jp-dd quote 7203 6758 --format json --period 5y`
4. **Interpreting JSON output**:
   - `quotes[]` holds successful results
   - `errors[]` holds failed tickers (report them; do not silently ignore)
   - `drawdown_pct` is negative (e.g. `-30.0` means 30% below the peak)
   - `current_price` is the closing price as of `as_of`
   - `highest_date` / `lowest_date` are the dates when the high/low occurred; `highest_days_ago` / `lowest_days_ago` are calendar days since the latest data date
   - All dates use `yyyy-mm-dd` format
5. **Ticker conventions**:
   - Japanese tickers: 4-digit code or `.T` suffix (e.g. `7203`, `7203.T`)
   - 6-digit security codes (ETFs, indices, funds) are likely unsupported
6. **Error handling**:
   - exit 2: argument error → fix the invocation
   - exit 3: network / rate limit → wait and retry
   - exit 4: no data → verify the ticker code
7. **Practical tips**:
   - Always fetch with `--format json` and format the table yourself
   - Use `--period 5y` (instead of full history) for faster responses
   - Use `--no-name` to skip company name lookup for speed
   - Respect rate limits: leave a gap between consecutive multi-ticker runs

## 4. Acceptance Criteria (AC)

### AC-S01: Skill loads correctly
```
Given `SKILL.md` exists at the install destination
When an agent loads the skill
Then frontmatter `name` and `description` parse correctly
And the frontmatter `name` equals "jp-stock-drawdown"
```

### AC-S02: Skill instructions are runnable
```
Given the commands in the "Basic invocation" section of SKILL.md
When each command is executed (network available)
Then it succeeds (`--format json` returns valid JSON with exit code 0)
```

### AC-S03: JSON interpretation is accurate
```
Given SKILL.md contains JSON explanation
When the content is reviewed
Then it states: drawdown_pct is negative, errors[] must be reported,
     and as_of is the date of current_price
And all dates use yyyy-mm-dd format
```

### AC-S04: Skill content is in English
```
Given the packaged `SKILL.md` (`src/jp_stock_drawdown/data/skill/SKILL.md`)
When the content is checked
Then the body contains no Japanese characters
```

### AC-S05: `skill install` installs the skill
```
Given a temp dir as `--dir` target
When `jp-dd skill install --dir <tmp>` is executed
Then exit code 0
And `<tmp>/jp-stock-drawdown/SKILL.md` is created
And its content equals the packaged SKILL.md
And stdout contains `Installed skill 'jp-stock-drawdown' to <path>`
```

### AC-S06: `skill install` refuses to overwrite without `--force`
```
Given `SKILL.md` already exists at the destination
When `jp-dd skill install --dir <tmp>` is executed (no --force)
Then exit code 1
And the existing file is NOT modified
And an English error message is printed to stderr

Given the same state
When `jp-dd skill install --dir <tmp> --force` is executed
Then exit code 0 and the file is overwritten
```

## 5. Implementation Notes

- The **source of truth** is `src/jp_stock_drawdown/data/skill/SKILL.md` (packaged). All changes are made there and tracked in git.
- Installation is always performed through `jp-dd skill install`; there is no manual copy.
- The packaged file must be included as package data (see SPEC 01 §3.2) and read via `importlib.resources` so `skill install` works from any run method (`uv run` / `uvx --from .` / `uvx --from <git>`).
