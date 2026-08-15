# SPEC 09: 実装計画（Agent向け）

- ステータス: Approved
- 対象バージョン: v1.0.0

## 1. 前提

- 実装はこのSPEC群を唯一の仕様としてAgentが行う。
- 各フェーズ完了後に **pytest / ruff で検証**する。
- ネットワーク不要のテストで全AC（AC-04〜AC-20）を通過させること。

## 2. 実装フェーズ

### フェーズ1: プロジェクト骨格

**完了条件**: `uv run jp-dd --help` が動き、`--version` が出力される。

- [ ] `pyproject.toml`（SPEC 01 の内容、`[project.scripts] jp-dd` 含む）
- [ ] `src/jp_stock_drawdown/__init__.py`（`__version__`）
- [ ] `src/jp_stock_drawdown/__main__.py`
- [ ] `src/jp_stock_drawdown/cli.py`（argparse骨格、`quote` サブコマンド、`-h`/`-V`）
- [ ] `uv sync` で依存解決

### フェーズ2: データモデルとエラー

**完了条件**: `model.py` / `errors.py` が定義済み。

- [ ] `errors.py`: `JpStockDrawdownError` / `UsageError` / `DataFetchError` / `NoDataError`（exit_code付き）
- [ ] `model.py`: `QuoteRequest` / `QuoteStats` / `QuoteResult` / `DrawdownReport`（dataclass）
- [ ] JSONスキーマ（SPEC 05）に対応するフィールドを持つこと

### フェーズ3: 指標計算（ネットワーク不要）

**完了条件**: AC-10〜AC-13 がpytestで通過。

- [ ] `metrics.py`: `compute_stats(df) -> QuoteStats`（純関数）
- [ ] エッジケース（NaN除外・空・1行・0除算）の実装
- [ ] `tests/fixtures/sample_history.csv` 作成（Close = [100,120,110,130,90] を含むOHLCデータ）
- [ ] `tests/test_metrics.py`: AC-10〜AC-13

### フェーズ4: シンボル正規化とフェッチ

**完了条件**: AC-04〜AC-05 がpytestで通過。

- [ ] `fetcher.py`: `normalize_symbol()`（4桁→`.T`、既存維持、不正除外）
- [ ] `fetcher.py`: `fetch_history()`（yfinanceラッパー、`auto_adjust=False`、start/end/period対応）
- [ ] `fetcher.py`: yfinance例外を `DataFetchError` / `NoDataError` に変換
- [ ] `fetcher.py`: 社名取得（best-effort、失敗無視）
- [ ] `tests/test_fetcher.py`: モックyfinanceでAC-04〜AC-05 + 例外変換

### フェーズ5: CLI統合

**完了条件**: AC-06〜AC-09, AC-14〜AC-20 がpytestで通過。

- [ ] `cli.py`: 引数検証（ticker形式・period許可リスト・日付・start<=end）
- [ ] `cli.py`: オーケストレーション（複数銘柄順次、部分失敗収集）
- [ ] `cli.py`: 終了コード決定（SPEC 06 の表）
- [ ] `tests/test_cli.py`: 上記AC群（`--format json` 出力をjson.loadsで検証）

### フェーズ6: フォーマッタ

**完了条件**: AC-14〜AC-17 がpytestで通過。

- [ ] `formatter.py`: `format_table()`（動的カラム幅、カンマ区切り、%表示）
- [ ] `formatter.py`: `format_json()`（SPEC 05 のスキーマ、`ensure_ascii=False, indent=2`）
- [ ] `tests/test_formatter.py`

### フェーズ7: Skill作成とインストール機能

**完了条件**: AC-S01〜AC-S06, AC-22, AC-23。

- [ ] `src/jp_stock_drawdown/data/skill/SKILL.md`（同梱Skill定義。**English**で記述、SPEC 08 の構成に従う）
- [ ] `skill.py`: `importlib.resources` による読み出し・インストール・frontmatter検証
- [ ] `cli.py`: `skill install` サブコマンド（`--dir` / `--force`、SPEC 02 §3 の動作仕様）
- [ ] package data設定（`[tool.hatch.build.targets.wheel]`、SPEC 01 §3.2）
- [ ] `tests/test_skill.py`: AC-S04〜AC-S06, AC-22, AC-23
- [ ] `uv run jp-dd skill install` で `~/.config/opencode/skills/` へ実際にインストール
- [ ] 配置先のSkillが読み込み可能であることを確認

### フェーズ8: 手動検証（ネットワーク）

**完了条件**: AC-21（実ネットワーク）を満たす。

- [ ] `uv run jp-dd quote 7203`（表形式・実データ）
- [ ] `uv run jp-dd quote 7203 --format json`
- [ ] `uvx --from . jp-dd quote 7203 --format json`
- [ ] 実在しない銘柄でのエラー動作確認

## 3. Agentへの指示テンプレート

各フェーズをAgentに依頼する際の指示例:

```
SPECに従って実装してください。
対象フェーズ: フェーズN
参照: ~/agent_sandbox/jp-stock-drawdown/docs/spec/{該当ドキュメント}
完了条件: {フェーズの完了条件}
検証: uv run pytest で関連テスト通過、uv run ruff check . 成功
ファイル変更はgit管理対象（~/agent_sandbox/jp-stock-drawdown）内で行うこと。
```

## 4. コミット方針

- フェーズ完了ごとにコミットする（メッセージ例: `feat: add metrics computation (SPEC 04)`）。
- コミットは実装フェーズでAgentが行うか、ユーザーの指示に従う。

## 5. 依存フェーズマップ

```
フェーズ1 → 2 → 3
フェーズ1 → 2 → 4 → 5
フェーズ3・4 → 6
フェーズ5 → 7
フェーズ5・6 → 8
```
