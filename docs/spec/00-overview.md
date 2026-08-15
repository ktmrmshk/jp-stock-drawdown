# SPEC 00: 概要

- ステータス: Approved
- 作成日: 2026-08-15
- 対象バージョン: v1.0.0

## 1. 目的

日本の上場企業の株価履歴を取得し、以下の4指標を出力するCLIツールを提供する。

1. **最高価格**（highest_price）
2. **最低価格**（lowest_price）
3. **現在価格**（current_price）
4. **現在のドローダウン%**（drawdown_pct）

利用者は2種類を想定する。

- **人間**: ターミナルで直接実行し、読みやすい表形式で確認する。
- **Agent（LLMエージェント）**: `--format json` で機械可読な出力を受け取り、分析・判断の材料にする。

## 2. スコープ

### 2.1 In Scope（v1.0.0）

- 日本市場（主に東京証券取引所上場）の銘柄を対象とした株価履歴の取得
- 上記4指標の算出と表示
- 複数銘柄の一括指定
- 取得期間の指定（`--period` / `--start` / `--end`）
- 人間可読形式（デフォルト）とJSON形式の両対応
- `uv` での実行（`uv run`）と `uvx` での簡易実行
- Agentが利用するためのSkill（`SKILL.md`）の定義

### 2.2 Out of Scope（v1.0.0 では実装しない）

- 売買の推奨・投資助言
- テクニカル指標の網羅（移動平均・RSI等）
- 完全な銘柄コード→企業名のDB（社名は取得できた場合の付帯情報）
- リアルタイム取引・ライブ配信
- バックテスト・シミュレーション
- 株価履歴のCSVダンプ（`--with-history` 等は将来拡張）
- 日本以外の市場への対応（`.T` 以外のサフィックスは受け付けるが正規化のみ）

## 3. 技術選定

| 項目 | 選定 | 理由 |
|------|------|------|
| 言語 | Python 3.11+ | yfinance/pandasのエコシステム |
| データソース | [yfinance](https://github.com/ranaroussi/yfinance) | Yahoo Financeの無料データ、日本の銘柄（`.T`）に対応 |
| パッケージ管理 | [uv](https://docs.astral.sh/uv/) | 高速・pyproject.toml駆動・`uvx`による簡易実行 |
| CLI構築 | 標準ライブラリ `argparse` | 依存を最小化、単純なCLI形状 |
| データ処理 | pandas | yfinanceの標準データ型（DataFrame） |
| テスト | pytest | uvのプロジェクトテンプレート標準 |
| ライセンス | MIT | 個人利用・配布ともに制約が少ない |

## 4. 主要な設計方針

1. **単一コマンド原則**: `quote` サブコマンドに全機能を集約し、CLI表面を最小化する。
2. **人間可読がデフォルト**: 人間が見る形式をデフォルトとし、機械用は明示オプションで選択。
3. **部分失敗許容**: 複数銘柄指定時、一部が失敗しても他は出力し、失敗は `errors` 欄で報告する。
4. **指標計算は純関数**: フェッチ（yfinance）と計算（metrics）を分離し、計算はネットワーク不要でテスト可能にする。
5. **uvx実行可能性**: `uvx --from <URL> jp-dd` で動作するよう、パッケージとしてビルド可能にする。

## 5. 前提条件

- macOS / Linux / Windows で動作することを目指す（検証はmacOS中心）
- ネットワーク接続が必要（Yahoo Financeへアクセス）
- APIキー・認証は不要（yfinanceは公開データを使用）

## 6. 関連ドキュメント

- [01-project-structure.md](./01-project-structure.md)
- [02-cli-surface.md](./02-cli-surface.md)
- [03-data-source.md](./03-data-source.md)
- [04-metrics.md](./04-metrics.md)
- [05-output-formats.md](./05-output-formats.md)
- [06-error-handling.md](./06-error-handling.md)
- [07-acceptance-criteria.md](./07-acceptance-criteria.md)
- [08-agent-skills.md](./08-agent-skills.md)
- [09-implementation-plan.md](./09-implementation-plan.md)
