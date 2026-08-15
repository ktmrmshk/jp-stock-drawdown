# SPEC 01: プロジェクト構造

- ステータス: Approved
- 対象バージョン: v1.0.0

## 1. ディレクトリ構成

```
jp-stock-drawdown/                  # gitトップ
├── pyproject.toml                  # uv/Pythonパッケージ定義
├── README.md
├── .gitignore
├── .python-version                 # uv管理のPythonバージョン（3.11+）
├── src/
│   └── jp_stock_drawdown/
│       ├── __init__.py             # __version__
│       ├── __main__.py             # python -m jp_stock_drawdown 対応
│       ├── cli.py                  # argparse CLIエントリポイント
│       ├── errors.py               # 例外定義
│       ├── fetcher.py              # yfinanceラッパー（シンボル正規化・取得）
│       ├── metrics.py              # 指標計算（純関数）
│       ├── model.py                # データクラス定義
│       ├── formatter.py            # 出力フォーマッタ
│       ├── skill.py                # Skillインストール機能
│       └── data/
│           └── skill/
│               └── SKILL.md        # 同梱Skill定義（インストールの実体）
├── tests/
│   ├── conftest.py                 # フィクスチャ
│   ├── fixtures/
│   │   └── sample_history.csv      # ゴールデンデータ（ネットワーク不要テスト用）
│   ├── test_metrics.py
│   ├── test_fetcher.py
│   ├── test_cli.py                 # 終了コード・出力検証
│   ├── test_formatter.py
│   └── test_skill.py               # Skillインストール検証
└── docs/
    └── spec/                       # 本仕様群
```

## 2. モジュール責務

| モジュール | 責務 | ネットワーク依存 |
|-----------|------|-----------------|
| `cli.py` | 引数パース・検証・各処理のオーケストレーション・終了コード決定 | なし |
| `fetcher.py` | シンボル正規化、`yfinance` による履歴取得、データ前処理、取得エラーの変換 | **あり** |
| `metrics.py` | 履歴DataFrameから4指標を計算（純関数・入力はDataFrame） | なし |
| `model.py` | `QuoteRequest` / `QuoteResult` / `QuoteStats` / `DrawdownReport` 等のデータクラス | なし |
| `formatter.py` | 人間可読・JSON・テーブル出力への変換 | なし |
| `skill.py` | Skill（`SKILL.md`）のパッケージからの読み出し・インストール・検証 | なし |
| `data/skill/SKILL.md` | 同梱するSkill定義（インストールの実体。Englishで記述） | なし |
| `errors.py` | カスタム例外の定義 | なし |

## 3. pyproject.toml 要件

```toml
[project]
name = "jp-stock-drawdown"
version = "0.1.0"
description = "Japanese stock price drawdown analyzer CLI"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "yfinance>=0.2.50",
    "pandas>=2.0",
]

[project.scripts]
jp-dd = "jp_stock_drawdown.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/jp_stock_drawdown"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"

[tool.ruff]
line-length = 100
```

> 注: `pyproject.toml` のバージョン番号は仕様の厳密な値ではない。実装時に適切なものを選ぶこと。ただし `[project.scripts]` の `jp-dd` とエントリポイントは固定とする。

### 3.2 Skill定義のパッケージ同梱

- `src/jp_stock_drawdown/data/skill/SKILL.md` を **package data** として同梱する（`[tool.hatch.build.targets.wheel]` で取り込む）。
- 実行時は `importlib.resources`（`importlib.resources.files(...).joinpath(...).read_text()`）で読み出す。
- これにより `uv run` / `uvx --from .` / `uvx --from <git>` のいずれの実行方法でも `jp-dd skill install` が動作する。

### 3.1 src-layout を採用する理由

- パッケージ化（`uvx --from` / PyPI公開）に必要な正しいパッケージ構造
- テストがsrc内の実装を意図せず直接importしないようにできる
- ビルドが `hatchling` によりシンプル

## 4. 実行方法（v1.0.0時点で全て成立すること）

| 方法 | コマンド | 前提 |
|------|---------|------|
| 開発実行 | `uv run jp-dd quote 7203` | リポジトリ内、`uv sync` 済み |
| モジュール実行 | `python -m jp_stock_drawdown quote 7203` | `.venv` 内で実行 |
| グローバル一時実行 | `uvx --from . jp-dd quote 7203` | リポジトリ内 |
| リモート実行 | `uvx --from git+https://github.com/OWNER/jp-stock-drawdown jp-dd quote 7203` | 公開後 |

## 5. 依存関係の制約

- ランタイム依存は `yfinance` と `pandas` のみに保つ（`argparse` は標準ライブラリ）
- 開発依存は `pytest`（+ `ruff`）
- 追加のCLIフレームワーク（click, typer等）は導入しない

## 6. Pythonバージョン

- `requires-python = ">=3.11"`
- `.python-version` には開発検証済みバージョンを明記する（実装時に決定）
