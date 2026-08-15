# SPEC 05: 出力形式

- ステータス: Approved
- 対象バージョン: v1.0.0

## 1. 共通規則

- 出力先: 既定はstdout。`-o/--output FILE` 指定時はファイルへ書き出す。
- 診断・ログはstderrへ（stdoutは純粋な結果のみ）。
- 文字エンコーディングはUTF-8。
- **言語**: CLIが出力するすべてのユーザー向けテキスト（表・エラーメッセージ・ヘルプ・ログ）は **English（英語）** で行う。日本語は使用しない。
- **日時形式**: すべての日付・日時は `yyyy-mm-dd` 形式（例: `2026-08-14`）で表す。時刻やタイムゾーンは出力しない。

## 2. table形式（デフォルト・人間可読）

### 2.1 ヘッダ行 + 銘柄ごとの行

```
Symbol   Name                   Current   AsOf        High     HighDate   HighAgo   Low      LowDate    LowAgo   Drawdown
7203.T   Toyota Motor Corp.   2,890.50   2026-08-14  3,200.00  2025-01-15  576d ago  1,500.00  2024-08-05  739d ago   -9.7%
6758.T   Sony Group Corporation  3,410.00   2026-08-14  3,500.00  2025-03-10  522d ago  2,100.00  2024-08-05  739d ago   -2.6%
```

- カラム幅は内容に応じて動的に揃える（等幅フォント前提）。
- `Name` が取得できない場合は `-` を表示。
- Drawdownは常に `%` 付きで表示（0.0% 含む）。
- 価格は `,` 区切り・小数点2桁。
- 日付は `yyyy-mm-dd`（例: `2026-08-14`）。
- `HighAgo` / `LowAgo` は `{N}d ago` 形式（例: `576d ago`）。`0` の場合は `0d ago`。

### 2.2 カラム定義

| カラム | 内容 |
|--------|------|
| `Symbol` | 正規化後のYahooシンボル |
| `Name` | 社名（best-effort、無ければ `-`） |
| `Current` | 現在価格 |
| `AsOf` | 現在価格の日付（最新データ日） |
| `High` | 最高価格 |
| `HighDate` | 最高価格が発生した日付 |
| `HighAgo` | 最高価格からの経過日数（`{N}d ago`） |
| `Low` | 最低価格 |
| `LowDate` | 最低価格が発生した日付 |
| `LowAgo` | 最低価格からの経過日数（`{N}d ago`） |
| `Drawdown` | ドローダウン%（`%` 付き） |

### 2.3 末尾サマリ

- 全銘柄失敗時: エラーメッセージをstderrへ、exit 4。
- 一部失敗時: 成功分の表をstdoutへ、失敗の説明をstderrへ、exit 0。

## 3. json形式（Agent向け）

### 3.1 スキーマ

```json
{
  "command": "quote",
  "generated_at": "2026-08-15",
  "period": {
    "specified": "max",
    "start": "2013-01-01",
    "end": "2026-08-14"
  },
  "quotes": [
    {
      "ticker": "7203",
      "symbol": "7203.T",
      "name": "Toyota Motor Corp.",
      "currency": "JPY",
      "as_of": "2026-08-14",
      "current_price": 2890.5,
      "highest_price": 3200.0,
      "lowest_price": 1500.0,
      "drawdown_pct": -9.6719,
      "highest_date": "2025-01-15",
      "highest_days_ago": 576,
      "lowest_date": "2024-08-05",
      "lowest_days_ago": 739
    }
  ],
  "errors": []
}
```

### 3.2 仕様詳細

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `command` | string | 常に `"quote"` |
| `generated_at` | string (yyyy-mm-dd) | 実行日 |
| `period.specified` | string | ユーザー指定の期間（`max` / `1y` 等） |
| `period.start` / `period.end` | string (yyyy-mm-dd) | 実際に取得されたデータの範囲 |
| `quotes[]` | array | 成功した銘柄ごとの結果 |
| `quotes[].ticker` | string | ユーザー入力のまま |
| `quotes[].symbol` | string | 正規化後のYahooシンボル |
| `quotes[].name` | string or null | best-effortの社名 |
| `quotes[].currency` | string | 常に `"JPY"` |
| `quotes[].as_of` | string (yyyy-mm-dd) | 現在価格の日付（最新データ日） |
| `quotes[].current_price` | number | 現在価格 |
| `quotes[].highest_price` | number | 最高価格 |
| `quotes[].lowest_price` | number | 最低価格 |
| `quotes[].drawdown_pct` | number | ドローダウン%（負値、小数点4桁まで丸め） |
| `quotes[].highest_date` | string (yyyy-mm-dd) | 最高価格が発生した日付 |
| `quotes[].highest_days_ago` | integer | 最高価格からの経過日数（`(as_of - highest_date).days`） |
| `quotes[].lowest_date` | string (yyyy-mm-dd) | 最低価格が発生した日付 |
| `quotes[].lowest_days_ago` | integer | 最低価格からの経過日数（`(as_of - lowest_date).days`） |
| `errors[]` | array of object | 失敗した銘柄の報告 |
| `errors[].ticker` | string | 失敗したticker |
| `errors[].error` | string | エラー種別（`no_data` / `fetch_failed` / `rate_limited`） |
| `errors[].message` | string | 人間可読なエラー説明 |

### 3.3 出力規則

- `json.dumps(..., ensure_ascii=False, indent=2)` で整形出力。
- 末尾に改行を付与。
- 全ての数値はJSONネイティブ数値（文字列にしない）。
- 1銘柄でも成功していれば `quotes` に含める（空配列でも `quotes` キーは必ず存在）。

## 4. ファイル出力（`-o`）

- ファイルへ書く内容はstdoutと同じ。
- 書き込み失敗（パーミッション等）はエラー（exit 1相当の汎用エラー。詳細は [06-error-handling.md](./06-error-handling.md)）。
