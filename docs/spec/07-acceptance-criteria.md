# SPEC 07: 受け入れ基準（Acceptance Criteria）

- ステータス: Approved
- 対象バージョン: v1.0.0

このドキュメントの基準は **実装完了の判定条件** である。Agentは実装後にこの基準をすべて満たすことをテストで証明する。ネットワークを要する基準は除外し、単体テストで検証可能な基準のみを要件とする（ネットワーク検証は手動確認）。

## 1. コマンドライフサイクル

### AC-01: ヘルプ表示
```
Given コマンド `jp-dd --help` を実行する
When コマンドを実行する
Then 終了コード0で使用法が表示される
And 使用法に `quote` サブコマンドの記述がある

Given コマンド `jp-dd quote --help` を実行する
When コマンドを実行する
Then 終了コード0でquoteのオプション一覧が表示される
And 表示に `--format`, `--period`, `--start`, `--end`, `-o/--output`, `--no-name`, `--verbose` が含まれる
```

### AC-02: バージョン表示
```
Given コマンド `jp-dd --version` を実行する
When コマンドを実行する
Then 終了コード0でバージョン文字列（例: `jp-stock-drawdown 0.1.0`）が出力される
```

### AC-03: コマンド省略のデフォルト
```
Given `jp-dd 7203` を実行する（サブコマンド省略）
When コマンドを実行する
Then `jp-dd quote 7203` と同等に動作する（quoteがデフォルト）
```

## 2. 引数検証

### AC-04: 4桁コードの正規化
```
Given `quote` サブコマンドにtickerとして `7203` を指定する
When シンボル正規化を実行する
Then 結果は `7203.T` である
```

### AC-05: 既存シンボルの維持
```
Given `quote` サブコマンドにtickerとして `7203.T` を指定する
When シンボル正規化を実行する
Then 結果は `7203.T` のままである
```

### AC-06: 不正ticker
```
Given `quote` サブコマンドにtickerとして `abc` を指定する
When コマンドを実行する
Then 終了コード2で使用法エラーが出力される
And エラーメッセージに `abc` が含まれる

Given `quote` サブコマンドにtickerとして `12345`（5桁）を指定する
When コマンドを実行する
Then 終了コード2で使用法エラーが出力される
```

### AC-07: ticker未指定
```
Given `jp-dd quote` を引数なしで実行する
When コマンドを実行する
Then 終了コード2で使用法エラーが出力される
```

### AC-08: periodのバリデーション
```
Given `quote 7203 --period 3y` を実行する
When コマンドを実行する
Then 終了コード2で使用法エラーが出力される（`3y` は許可リスト外）
```

### AC-09: 日付バリデーション
```
Given `quote 7203 --start 2024-13-01` を実行する
When コマンドを実行する
Then 終了コード2で使用法エラーが出力される

Given `quote 7203 --start 2025-01-01 --end 2024-01-01` を実行する
When コマンドを実行する
Then 終了コード2で使用法エラーが出力される（start > end）
```

## 3. 指標計算（ネットワーク不要・フィクスチャ使用）

### AC-10: 4指標と日付・経過日数の計算
```
Given テスト用DataFrame（Close = [100, 120, 110, 130, 90]、日付は2026-01-01〜2026-01-05）を compute_stats に渡す
When 計算を実行する
Then highest_price = 130.0
And lowest_price = 90.0
And current_price = 90.0
And drawdown_pct = -30.7692（小数4桁に丸め）
And highest_date = 2026-01-04（130の日付）
And lowest_date = 2026-01-05（90の日付）
And as_of = 2026-01-05
And highest_days_ago = 1
And lowest_days_ago = 0
```

### AC-11: 欠損値の扱い
```
Given CloseにNaNを含むDataFrameを compute_stats に渡す
When 計算を実行する
Then NaNは除外して計算され、例外は発生しない
```

### AC-12: 空データ
```
Given 行数0のDataFrameを compute_stats に渡す
When 計算を実行する
Then NoDataErrorが発生する
```

### AC-13: 単一データ
```
Given 1行のみのDataFrame（Close = [150]）を compute_stats に渡す
When 計算を実行する
Then highest = lowest = current = 150.0
And drawdown_pct = 0.0
And highest_date = lowest_date = as_of = その行の日付
And highest_days_ago = lowest_days_ago = 0
```

### AC-13b: 経過日数の同値性
```
Given highest_date == as_of のデータ（最高値が最新日）
When 計算を実行する
Then highest_days_ago = 0
And 経過日数は暦日数である（週末・祝日もカウント）
```

## 4. 出力形式

### AC-14: table形式（人間可読）
```
Given `quote 7203` が成功する状態で実行する
When 表形式で出力する
Then stdoutにヘッダ行（Symbol / Name / Current / AsOf / High / HighDate / HighAgo / Low / LowDate / LowAgo / Drawdown を含む）が出力される
And 各銘柄が1行で表示される
And Drawdownは `%` 付き（例: `-9.7%`）
And 価格はカンマ区切り・小数点2桁（例: `2,890.50`）
And 各価格の日付が `yyyy-mm-dd` 形式で表示される（AsOf / HighDate / LowDate）
And HighAgo / LowAgo が `{N}d ago` 形式で表示される（例: `576d ago`）
And 出力に日本語が含まれない
```

### AC-15: JSON形式（機械可読）
```
Given `quote 7203 --format json` を実行する
When 出力する
Then stdoutがJSONとしてパース可能である
And `quotes[0].symbol` = "7203.T"
And `quotes[0].drawdown_pct` が数値型である
And `quotes[0].highest_days_ago` / `quotes[0].lowest_days_ago` が整数型である
And `quotes[0].highest_date` / `quotes[0].lowest_date` / `quotes[0].as_of` が `yyyy-mm-dd` 文字列である
And `command` = "quote"
And `quotes` キーが必ず存在する（空配列でも）
```

### AC-16: 複数銘柄のJSON
```
Given `quote 7203 6758 --format json` を実行する
When 出力する
Then quotes 配列の長さが2である（成功時）
And 各要素のtickerが入力順を保持する
```

### AC-17: ファイル出力
```
Given `quote 7203 --format json -o /tmp/result.json` を実行する
When 出力する
Then ファイル `/tmp/result.json` が作成され、stdoutと同じ内容である
And 終了コード0である
```

## 5. エラー処理

### AC-18: 部分失敗（exit 0）
```
Given `quote 7203 0000 --format json` を実行する（0000はデータなし）
When コマンドを実行する
Then 終了コード0である
And quotesに7203の結果が含まれる
And errorsに0000のエントリが含まれる（error = "no_data"）
```

### AC-19: 全銘柄失敗（データなし）
```
Given `quote 0000 --format json` を実行する（データなし）
When コマンドを実行する
Then 終了コード4である
And quotesが空配列である
And errorsにno_dataの報告がある
```

### AC-20: ネットワーク失敗時のコード
```
Given fetchがDataFetchError（ネットワーク断）を発生させる状態
When `quote 7203` を実行する
Then 終了コード3である
```

## 6. 実行方法の成立

### AC-21: 各実行パスの成立
```
Given リポジトリ内で `uv sync` が成功する
When 以下のコマンドを順に実行する
Then すべて終了コード0である（ネットワーク成功時）
And 各コマンドが同等の結果を出力する
  1. uv run jp-dd quote 7203 --format json
  2. uv run python -m jp_stock_drawdown quote 7203 --format json
  3. uvx --from . jp-dd quote 7203 --format json
```

## 6.5 Skill インストール

### AC-22: パッケージ同梱SKILL.mdの存在
```
Given パッケージ内の `src/jp_stock_drawdown/data/skill/SKILL.md`
When 内容を読み出す
Then frontmatter（name / description）が存在する
And 本文に日本語が含まれない（Englishのみ）
And `uvx --from . jp-dd skill install --dir <tmp>` でも同梱ファイルから動作する
```

### AC-23: skill install（インストール・上書き保護）
```
Given 一時ディレクトリを `--dir` に指定して `jp-dd skill install` を実行する
When コマンドを実行する
Then 終了コード0
And `<dir>/jp-stock-drawdown/SKILL.md` が作成される
And 内容が同梱のSKILL.mdと同一である
And stdoutに `Installed skill 'jp-stock-drawdown' to <path>` が出力される

Given 同じ `<dir>` で再度 `skill install`（--force無し）を実行する
Then 終了コード1
And 既存ファイルは変更されない

Given `--force` 付きで実行する
Then 終了コード0で上書きされる
```

## 7. テスト実装要件

- ネットワーク不要でAC-04〜AC-19までを pytest でカバーする（fetcherはモック/フィクスチャ注入）。
- AC-21のネットワーク確認はCIや通常テストでは実行せず、手動確認項目とする。
- テスト実行コマンド: `uv run pytest`
- フォーマットチェック: `uv run ruff check .` が成功すること。
