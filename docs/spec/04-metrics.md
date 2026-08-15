# SPEC 04: 指標の定義と計算ロジック

- ステータス: Approved
- 対象バージョン: v1.0.0

## 1. 指標定義

すべての指標は **日次終値（`Close`）** を基準に計算する。入力は日付インデックスのDataFrame（`Close` カラム必須）。

| 指標 | フィールド名 | 定義 |
|------|------------|------|
| 最高価格 | `highest_price` | 対象期間の `Close` の最大値 |
| 最低価格 | `lowest_price` | 対象期間の `Close` の最小値 |
| 現在価格 | `current_price` | 対象期間の最後の `Close`（最新日） |
| ドローダウン% | `drawdown_pct` | `(current_price - highest_price) / highest_price × 100` |

### 補助情報（日付・経過日数）

すべての価格には **その価格が発生した日付** を付随させる。さらに最高価格・最低価格には **現在（最新データ日）からの経過日数** を付随させる。

| 項目 | フィールド名 | 定義 |
|------|------------|------|
| 取得日 | `as_of` | `current_price` の日付（最新データ日 = 「現在」） |
| 最高価格の日付 | `highest_date` | `highest_price` が発生した日付（複数日の場合は最初の日付） |
| 最低価格の日付 | `lowest_date` | `lowest_price` が発生した日付（複数日の場合は最初の日付） |
| 最高価格からの経過日数 | `highest_days_ago` | `(as_of - highest_date).days`（整数・0以上） |
| 最低価格からの経過日数 | `lowest_days_ago` | `(as_of - lowest_date).days`（整数・0以上） |

**経過日数の定義**
- `as_of`（最新データ日）を「現在」とし、そこから各日付までの **暦日数**（週末・祝日を含む）で表す。
- `highest_date == as_of` の場合は `0`。
- 営業日数（営業日カレンダー）ではない。

## 2. 計算ロジック

```python
import pandas as pd

def compute_stats(df: pd.DataFrame) -> QuoteStats:
    closes = df["Close"].dropna()
    highest = closes.max()
    lowest = closes.min()
    current = closes.iloc[-1]
    drawdown_pct = ((current - highest) / highest) * 100
    ...
```

- 小数点: 価格はyfinanceの精度に従い、出力時に丸める。
- `drawdown_pct` は **負値で表現**（ピークから何%下落しているかを示す）。現在価格がピークより上になることは定義上ない（highestが最大値のため）が、丸め誤差でわずかに正になる場合は `0.0` にクランプする。

## 3. エッジケース

| ケース | 挙動 |
|--------|------|
| データ行が0 | `NoDataError`（exit 4） |
| `Close` が全てNaN | `NoDataError`（exit 4） |
| `Close` の一部NaN | `dropna()` で除外して計算 |
| `highest == 0`（理論上ほぼ無し） | ゼロ除算を避け `NoDataError` |
| 1行のみ | highest = lowest = current、drawdown = 0.0 |
| 全期間 `max` | 全履歴での最高値・最安値（All Time High / Low） |

## 4. 計算例（ゴールデンデータ）

`Close = [100, 120, 110, 130, 90]`（日付は 2026-01-01〜2026-01-05 の5営業日）の場合:

| 指標 | 値 |
|------|-----|
| highest_price | 130 |
| lowest_price | 90 |
| current_price | 90 |
| drawdown_pct | (90-130)/130×100 = **-30.769...%** |
| as_of | 2026-01-05 |
| highest_date | 2026-01-04 |
| lowest_date | 2026-01-05 |
| highest_days_ago | (2026-01-05 - 2026-01-04).days = **1** |
| lowest_days_ago | (2026-01-05 - 2026-01-05).days = **0** |

※ このデータを `tests/fixtures/sample_history.csv` の計算検証に使用する。

## 5. 精度・フォーマット

- 計算内部は浮動小数点のまま保持する。
- **table形式**: 価格はカンマ区切りで小数点2桁、drawdownは `-30.8%`（小数点1桁、`%`付き）。
- **JSON形式**: 数値はそのまま（丸めず）。drawdownは小数点4桁までで丸める。
