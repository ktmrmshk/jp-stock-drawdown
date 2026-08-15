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

## 想定する利用方法（実装後のイメージ）

```bash
# uv でローカル実行
uv run jp-dd quote 7203

# 複数銘柄 + JSON出力
uv run jp-dd quote 7203 6758 9984 --format json

# uvx で簡易実行（Git URL版・公開後）
uvx --from git+https://github.com/OWNER/jp-stock-drawdown jp-dd quote 7203

# Agent用Skillをインストール（opencodeデフォルト）
uv run jp-dd skill install
```

## 状態

- [x] SPECドキュメント
- [ ] 実装（Agentによる）
