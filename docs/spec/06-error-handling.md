# SPEC 06: エラー処理・終了コード

- ステータス: Approved
- 対象バージョン: v1.0.0

## 1. 終了コード一覧

| コード | 意味 | 発生条件 |
|-------|------|---------|
| 0 | 成功 | 1銘柄以上が正常に取得・出力された |
| 1 | 汎用エラー | 出力先ファイル書き込み失敗など予期しないエラー |
| 2 | 使用法エラー | 引数・オプションの形式不正（argparseの標準挙動） |
| 3 | データソースエラー | ネットワーク断・タイムアウト・レート制限 |
| 4 | データなし | 全銘柄でデータが取得できない / 履歴が空 |

## 2. 例外モデル（`errors.py`）

```python
class JpStockDrawdownError(Exception):      # 基底
    exit_code = 1

class UsageError(JpStockDrawdownError):     # exit 2
    exit_code = 2

class DataFetchError(JpStockDrawdownError): # exit 3（ネットワーク・レート制限）
    exit_code = 3

class NoDataError(JpStockDrawdownError):    # exit 4（データ空・不正シンボル結果）
    exit_code = 4
```

## 3. エラー処理フロー

### 3.1 引数検証エラー（exit 2）

- argparse由来（不明なオプション・不足引数・不正フォーマット）
- 検証メッセージは対象の引数を明示: `error: invalid ticker: 'abc' (expect 4-digit code or symbol like 7203.T)`

### 3.2 取得時のエラー（exit 3 / 4）

複数銘柄を順次取得する際、**1銘柄の失敗で処理全体を止めない**。

```
for ticker in tickers:
    try:
        df = fetch_history(ticker, ...)
        stats = compute_stats(df)
        results.append(...)
    except NoDataError as e:
        errors.append({"ticker": t, "error": "no_data", "message": str(e)})
    except DataFetchError as e:
        errors.append({"ticker": t, "error": "fetch_failed" | "rate_limited", ...})
```

終了コードの決定ルール:

| 状況 | 終了コード |
|------|-----------|
| 全銘柄成功 | 0 |
| 一部成功・一部失敗 | 0（失敗は `errors` とstderrに報告） |
| 全銘柄失敗（うち1つ以上が fetch/rate-limit 系） | 3 |
| 全銘柄失敗（全て no_data 系） | 4 |
| 全銘柄失敗（no_data と fetch が混在） | 3 |

### 3.3 予期しない例外（exit 1）

- 意図しない例外は `main()` のトップレベルで捕捉し、`exit 1` にする。
- `--verbose` 時はトレースバックをstderrに表示。

## 4. stderrメッセージ方針

- 人間向けのエラー説明は stderr に出力（stdoutは結果のみ）。
- JSON形式でもエラーの本文はstderrへは出さず、`errors[]` フィールドに含める。ただし `--verbose` 時は診断ログをstderrへ出す。
- **エラーメッセージ・診断ログはすべて English** で記述する（日本語を使わない）。
- 日時は `yyyy-mm-dd` 形式（例: `2026-08-14`）。

## 5. エラー時出力例

### 全銘柄失敗（exit 4, table形式）

```
$ jp-dd quote 0000
error: no data for 0000.T (symbol may be invalid or delisted)
```

### 一部失敗（exit 0, JSON形式）

```json
{
  "command": "quote",
  "generated_at": "2026-08-15",
  "period": {"specified": "max", "start": "2013-01-01", "end": "2026-08-14"},
  "quotes": [
    { "ticker": "7203", "symbol": "7203.T", "name": null, "currency": "JPY",
      "as_of": "2026-08-14", "current_price": 2890.5,
      "highest_price": 3200.0, "lowest_price": 1500.0,
      "drawdown_pct": -9.6719,
      "highest_date": "2025-01-15", "highest_days_ago": 576,
      "lowest_date": "2024-08-05", "lowest_days_ago": 739 }
  ],
  "errors": [
    { "ticker": "0000", "error": "no_data", "message": "no data for 0000.T" }
  ]
}
```
