# SPEC 02: CLIインターフェース

- ステータス: Approved
- 対象バージョン: v1.0.0

## 1. 全体構造

```
jp-dd <command> [options] [arguments]

commands:
  quote     株価履歴から最高価格・最低価格・現在価格・ドローダウン%を出力（デフォルト）
  skill     Agent用Skillの管理（インストール）
```

- コマンド省略時は `quote` をデフォルトとする（`jp-dd 7203` で動作する）。
- グローバルオプション: `-h/--help`, `-V/--version`

## 2. `quote` コマンド

### 2.1 位置引数

| 引数 | 必須 | 説明 |
|------|------|------|
| `tickers` | 必須（1つ以上） | 銘柄コード。`7203` / `7203.T` 形式。複数指定可。 |

### 2.2 オプション

| オプション | デフォルト | 説明 |
|-----------|-----------|------|
| `--period PERIOD` | `max` | 取得期間。`1d 5d 1mo 3mo 6mo 1y 2y 5y 10y max` |
| `--start yyyy-mm-dd` | なし | 取得開始日（指定時はperiodより優先） |
| `--end yyyy-mm-dd` | なし | 取得終了日（指定時はperiodより優先） |
| `--format FORMAT` | `table` | 出力形式。`table` / `json` |
| `-o, --output FILE` | なし | 出力先ファイル（省略時はstdout） |
| `--no-name` | オフ | 社名取得をスキップ（応答高速化） |
| `--verbose` | オフ | 診断情報をstderrへ出力 |

### 2.3 引数検証ルール

1. `tickers` が空 → 使用法エラー（exit 2）
2. 各tickerの形式:
   - `^\d{4}$`（4桁数字）→ `7203.T` に正規化
   - `^\d{4}\.(T|N|F|S|OS)$` → そのまま使用
   - 上記以外 → 使用法エラー（exit 2、対象tickerをメッセージに含める）
3. `--period` が許可リスト外 → 使用法エラー（exit 2）
4. `--start` / `--end` は `yyyy-mm-dd` 形式のみ。`--start > --end` はエラー（exit 2）
5. `--period` と `--start` を同時指定した場合、`--start`（および `--end`）を優先

## 3. `skill` コマンド

Agent用Skill（`SKILL.md`）をAgent実行環境へインストールする。Skill定義はパッケージに同梱されているため、リポジトリ内でなくても動作する。

### 3.1 サブコマンド

| サブコマンド | 説明 |
|-------------|------|
| `install` | Skillを指定ディレクトリへインストール |

### 3.2 `install` のオプション

| オプション | デフォルト | 説明 |
|-----------|-----------|------|
| `--dir DIR` | `~/.config/opencode/skills` | スキルディレクトリのベースパス（`~` 展開対応）。この下に `<skill-name>/SKILL.md` を作成 |
| `--force` | オフ | 既存ファイルを上書きする（省略時は上書きしない） |

### 3.3 動作仕様

1. 同梱の `SKILL.md` を `importlib.resources` で読み出す。
2. インストール先: `<dir>/jp-stock-drawdown/SKILL.md`。
3. 親ディレクトリが無ければ作成する。
4. 既にファイルが存在し `--force` 無し → **上書きしない**。メッセージをstderrへ、exit 1。
5. 成功時: `Installed skill 'jp-stock-drawdown' to <path>` をstdoutへ出力し、exit 0。
6. インストール後に frontmatter（`name` / `description`）がパース可能であることを確認する（失敗時はexit 1）。

### 3.4 使用例

```bash
# デフォルト（opencode）へインストール
uv run jp-dd skill install

# 別ディレクトリへインストール
uv run jp-dd skill install --dir ~/.claude/skills

# 上書き
uv run jp-dd skill install --force
```

## 4. 使用例

```bash
# 1銘柄、デフォルト（全期間・表形式）
uv run jp-dd quote 7203

# 表形式の例（イメージ）
# Symbol   Name              Current   AsOf        High     HighDate   HighAgo   Low      LowDate    LowAgo   Drawdown
# 7203.T  Toyota Motor Corp.   2,890.50   2026-08-14  3,200.00  2025-01-15  576d ago  1,500.00  2024-08-05  739d ago   -9.7%

# 複数銘柄
uv run jp-dd quote 7203 6758 9984

# JSON出力（Agent向け）
uv run jp-dd quote 7203 --format json

# 期間指定
uv run jp-dd quote 7203 --period 5y
uv run jp-dd quote 7203 --start 2024-01-01 --end 2024-12-31

# ファイル出力
uv run jp-dd quote 7203 --format json -o /tmp/result.json

# コマンド省略
uv run jp-dd 7203
```

## 5. `--help` 出力の例

```
usage: jp-dd [-h] [-V] {quote,skill} ...

Japanese stock price drawdown analyzer

commands:
  quote    Show highest/lowest/current price and drawdown %
  skill    Manage the agent skill (install)
```

```
usage: jp-dd quote [-h] [--period PERIOD] [--start START] [--end END]
                   [--format {table,json}] [-o FILE] [--no-name] [--verbose]
                   tickers [tickers ...]
```

```
usage: jp-dd skill install [-h] [--dir DIR] [--force]
```

- ヘルプ文言は **English** で書くこと。**全コマンドで `-h` が必ず正常動作**すること。

## 6. 終了コード

| 終了コード | 意味 |
|-----------|------|
| 0 | 成功（1銘柄以上が正常取得された場合） |
| 2 | 使用法エラー（引数・オプションの不正） |
| 3 | データソースエラー（ネットワーク・レート制限など） |
| 4 | 全銘柄でデータなし / 取得失敗 |

詳細は [06-error-handling.md](./06-error-handling.md) を参照。
