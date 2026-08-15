# jp-stock-drawdown

日本の上場企業の株価履歴を取得し、**最高価格 / 最低価格 / 現在価格 / 現在のドローダウン%** を出力するCLIツール。

- データソース: [yfinance](https://github.com/ranaroussi/yfinance)（Yahoo Finance）
- 実行環境: Python 3.11+ / [uv](https://docs.astral.sh/uv/)
- 出力: デフォルトは人間可読、`--format json` でAgent・自動処理向けに機械可読

## このリポジトリの構成

本リポジトリは **Spec-Driven Development** で開発します。
`docs/spec/` が正式な仕様（SPEC）であり、実装はこの仕様をベースにAgentが実施します。

```
docs/spec/
├── 00-overview.md             # 目的・スコープ・技術選定
├── 01-project-structure.md    # プロジェクト構造・モジュール責務
├── 02-cli-surface.md          # CLIインターフェース定義
├── 03-data-source.md          # yfinance連携仕様
├── 04-metrics.md              # 指標の定義と計算ロジック
├── 05-output-formats.md       # 出力形式（人間可読 / JSON）
├── 06-error-handling.md       # エラー処理・終了コード
├── 07-acceptance-criteria.md  # 受け入れ基準（Gherkin）
├── 08-agent-skills.md         # Agent用Skillの仕様
└── 09-implementation-plan.md  # 実装計画（Agent向け手順）
```

## インストール

前提: [uv](https://docs.astral.sh/uv/) と Python 3.11+ が必要です。

### ローカルにインストール（推奨）

`uv tool install` でホームディレクトリ配下にインストールすると、どこからでも `jp-dd` コマンドを直接実行できます。

```bash
uv tool install --from git+https://github.com/ktmrmshk/jp-stock-drawdown jp-stock-drawdown
jp-dd quote 7203
```

pip を使う場合:

```bash
pip install git+https://github.com/ktmrmshk/jp-stock-drawdown.git
jp-dd quote 7203
```

### 一時実行（インストール不要）

```bash
uvx --from git+https://github.com/ktmrmshk/jp-stock-drawdown jp-dd quote 7203
```

### 開発（リポジトリ内）

```bash
cd jp-stock-drawdown
uv sync
uv run jp-dd quote 7203                        # 通常実行
uv run python -m jp_stock_drawdown quote 7203  # モジュール実行
```

## 使い方

### 株価指標の表示

```bash
# 1銘柄（デフォルト: 全期間・表形式）
jp-dd quote 7203

# コマンド省略（quoteがデフォルト）
jp-dd 7203

# 複数銘柄（カンマではなくスペース区切り）
jp-dd quote 7203 6758 9984

# 期間指定（--start / --end は --period より優先）
jp-dd quote 7203 --period 5y
jp-dd quote 7203 --start 2024-01-01 --end 2024-12-31
```

銘柄コードは4桁の日本株コード（`7203` → `7203.T` に自動正規化）またはYahooシンボル（`7203.T` など）を指定します。

### 出力形式

```bash
# 表形式（デフォルト・人間可読）
jp-dd quote 7203

# JSON形式（Agent・自動処理向け）
jp-dd quote 7203 --format json

# ファイル出力（stdoutと同じ内容を書き出し）
jp-dd quote 7203 --format json -o result.json

# 社名取得スキップ / 診断ログ（いずれもstderrへ出力）
jp-dd quote 7203 --no-name
jp-dd quote 7203 --verbose
```

表形式の例（実データ）:

```
Symbol  Name                      Current   AsOf        High      HighDate    HighAgo   Low     LowDate     LowAgo     Drawdown
7203.T  Toyota Motor Corporation  3,020.00  2026-08-14  3,944.00  2026-03-02  165d ago  475.20  2011-11-24  5377d ago  -23.4%
```

- 価格はすべて終値（`Close`）基準。`Drawdown` はピークからの下落率（負値）。
- `HighAgo` / `LowAgo` は最新データ日からの経過日数。
- 日付はすべて `yyyy-mm-dd` 形式。

### 終了コード

| コード | 意味 |
|-------|------|
| 0 | 成功（1銘柄以上を取得・出力） |
| 1 | 汎用エラー（出力先ファイルの書き込み失敗など） |
| 2 | 使用法エラー（引数・オプションの形式不正） |
| 3 | データソースエラー（ネットワーク断・レート制限） |
| 4 | データなし（全銘柄で履歴を取得できない） |

複数銘柄の一部が失敗してもコマンドは継続し、失敗分は `errors[]`（JSON）またはstderr（表形式）に報告されます。

### Agent用Skillのインストール

`SKILL.md` をAgent実行環境へインストールできます（内容はパッケージに同梱）。

```bash
# opencodeデフォルト（~/.config/opencode/skills/jp-stock-drawdown/）
jp-dd skill install

# 別ディレクトリへ / 既存ファイルを上書き
jp-dd skill install --dir ~/.claude/skills
jp-dd skill install --force
```

## 状態

- [x] SPECドキュメント
- [x] 実装（Agentによる）
  - [x] `uv run jp-dd quote 7203` で株価指標の出力
  - [x] `uv run jp-dd skill install` でAgent用Skillのインストール
  - [x] `uv run pytest` / `uv run ruff check .` 成功
