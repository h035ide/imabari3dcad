### EVOSHIP ヘルプ → Neo4j 取り込みガイド

このドキュメントは、`helpfile_parser/ingest_neo4j.py` を用いて EVOSHIP のヘルプHTMLをチャンク化し、Neo4j に格納する手順をまとめたものです。

---

#### 前提条件
- Python 環境はプロジェクトの `uv`（推奨）または venv を利用
- Neo4j が起動済み（Bolt 7687）で、対象 DB（例: `helpfile`）が存在
- ヘルプHTML一式が手元にある（例: `evoship/EVOSHIP_HELP_FILES`）

#### 必要な環境変数（`.env` 推奨）
- `NEO4J_URI`（例: `bolt://localhost:7687`）
- `NEO4J_USER` または `NEO4J_USERNAME`
- `NEO4J_PASSWORD`
- `NEO4J_DATABASE`（任意、未指定時は `neo4j`）
- `OPENAI_API_KEY`（`--use-llm-extract` 使用時）
- `OPENAI_MODEL`（任意、未指定時はコード内デフォルト `gpt-4o-mini`）

---

#### 代表コマンド（PowerShell）
以下は LLM 抽出を有効化し、ログ出力・wipe・DB指定を含む実行例です。

```powershell
uv run -m helpfile_parser.ingest_neo4j "evoship/EVOSHIP_HELP_FILES" `
  --max-files 3 `
  --use-llm-extract `
  --llm-model "gpt-5-nano" `
  --wipe `
  --log-file "helpfile_parser/logs/ingest_$(Get-Date -Format 'yyyyMMdd_HHmmss').log" `
  --log-level DEBUG `
  --console-level INFO `
  --database "helpfile"
```

補足:
- `--llm-model` は実行環境で利用可能なモデル名を指定してください。
- PowerShell の日時埋め込みは `$(Get-Date -Format 'yyyyMMdd_HHmmss')` を利用しています。

---

#### よく使うバリエーション
- ドライラン（Neo4j 書き込みなし、進捗表示）
```powershell
uv run python helpfile_parser/ingest_neo4j.py "evoship/EVOSHIP_HELP_FILES" --dry-run --console-level INFO
```

- 既存データ保持のままインポート
```powershell
uv run -m helpfile_parser.ingest_neo4j "evoship/EVOSHIP_HELP_FILES" --console-level INFO
```

- チャンク設定の調整
```powershell
uv run -m helpfile_parser.ingest_neo4j "evoship/EVOSHIP_HELP_FILES" --chunk-size 1000 --chunk-overlap 150
```

---

#### グラフのエクスポート（JSONL）
インポート完了後、`--export-dir` を指定すると、`data_source=EVOSHIP_HELP_FILES` に紐づくノード・リレーションを JSONL で保存できます。

出力内容:
- `nodes.jsonl`: 各行 `{ "id", "labels", "properties" }`
- `relationships.jsonl`: 各行 `{ "id", "type", "start", "end", "properties" }`

使用例:
```powershell
uv run -m helpfile_parser.ingest_neo4j "evoship/EVOSHIP_HELP_FILES" `
  --use-llm-extract `
  --llm-model "gpt-5-nano" `
  --database "helpfile" `
  --export-dir "helpfile_parser/export" `
  --console-level INFO
```

注意:
- `--dry-run` 指定時はエクスポートされません（Neo4j 未書き込みのため）。
- 出力対象は `EVOSHIP_HELP_FILES` のみです（スクリプト内の `DATA_SOURCE`）。

---

#### 出力例（INFO）
```
INFO LlamaIndexでチャンク化完了: 3 documents, 6 sections, 7 chunks (chunk_size=800, overlap=120)
INFO dry-runモードのためNeo4jへの書き込みをスキップします。
INFO 処理が完了しました: 3 documents, 6 sections, 7 chunks
```

---

#### トラブルシューティング
- 文字化けする（PowerShell）：本ツールは Windows で標準出力を UTF-8 に再設定します。問題が続く場合は PowerShell で `chcp 65001` を実行、またはターミナルの文字コード設定を UTF-8 にしてください。
- `ModuleNotFoundError`（相対インポート）：`-m helpfile_parser.ingest_neo4j` 形式での起動を推奨。スクリプト直実行でも動くようフォールバックを実装済みです。
- OpenAI のタイムアウト：ネットワーク混雑で一時的に `TimeoutException` が出る場合があります。自動リトライで復旧することが多いです。頻発する場合は同時実行を抑える（小さな `--max-files` から試す）、時間帯を変える、ネットワークを確認してください。
- Neo4j 接続：`NEO4J_URI/USER/PASSWORD/DATABASE` を再確認。APOC 利用環境であることを推奨します。

---

#### 検証のポイント
- 実行後にログ（例: `helpfile_parser/logs/ingest_YYYYMMDD_HHMMSS.log`）を確認
- Neo4j ブラウザで `MATCH (n) RETURN count(n);` などを確認
- 取り込み件数はコンソール/ログに集計表示（documents/sections/chunks）

---

#### 備考
- プロジェクトでは `uv` の利用を想定しています。`uv` がない場合は通常の `python` 実行でも可ですが、依存関係は事前に `uv pip install -r requirements.txt`（または `pip install -r requirements.txt`）で整えてください。


