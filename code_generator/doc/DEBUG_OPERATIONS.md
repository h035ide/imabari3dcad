### デバッグ系ツールの操作ガイド（Chroma / Neo4j / 再インジェスト）

このドキュメントは、`code_generator/` に追加したデバッグ用スクリプトの使い方をまとめたものです。Windows PowerShell での実行例は `uv run` を用いて記載しています。

---

## 事前準備

- `.env`（プロジェクトルート）に以下を設定
  - `OPENAI_API_KEY`
  - `NEO4J_URI`（例: `neo4j://127.0.0.1:7687`）
  - `NEO4J_USER`, `NEO4J_PASSWORD`
  - `NEO4J_DATABASE`（例: `codegenerator`）
- 依存関係は既存の `uv` 環境で実行可能です。PowerShell では `| cat` のパイプは不要です。

---

## Chroma デバッグ

### 1) ドキュメント確認と簡易検索: `debug_chroma.py`

```powershell
uv run code_generator\debug_chroma.py --query "球を作成する関数" --k 3
```

- `doc_count` と、上位 `k` 件のスコア・メタデータ・先頭コンテンツを表示します。
- 永続化ディレクトリは `chroma_db_store` を参照します。

### 2) スコア分布の確認: `debug_scores.py`

```powershell
uv run code_generator\debug_scores.py --query "球を作成する関数" --k 10
```

- 上位 `k` 件のスコア配列、`mean` / `std` を表示します。
- 閾値調整の目安:
  - 保守的: `AMBIGUITY_ABSOLUTE_THRESHOLD=0.02`, `AMBIGUITY_RELATIVE_THRESHOLD=1.02`
  - 厳格: `AMBIGUITY_ABSOLUTE_THRESHOLD=0.01`, `AMBIGUITY_RELATIVE_THRESHOLD=1.015`
- `.env` に上記を追記し、ツールの曖昧判定に反映させます。

---

## Neo4j デバッグ: `debug_neo4j.py`

### ラベル・件数・サンプル

```powershell
uv run code_generator\debug_neo4j.py --list-labels
uv run code_generator\debug_neo4j.py --count --label Function
uv run code_generator\debug_neo4j.py --sample 5 --label Function
```

### Chroma ↔ Neo4j クエリ照合（トップKの逐次突合せ）

```powershell
uv run code_generator\debug_neo4j.py --query "球を作成する関数" --collection api_functions_fn --k 10
```

- Chroma上位候補の `metadata.api_name` と、Neo4j の `name` を横並び表示し、一致・不一致を確認します。
- セッションは `.env` の `NEO4J_DATABASE` を用いて開かれます。

### Chroma メタデータ一括突合せ

```powershell
uv run code_generator\debug_neo4j.py --check-chroma --collection api_functions_fn --k 100
```

- `neo4j_node_id`（= `elementId(n)` 想定）が Neo4j に存在するかを一括チェックします。

### 任意の Cypher 実行（安全ガード付き）

- 読み取り（例）
```powershell
uv run code_generator\debug_neo4j.py --cypher "MATCH (n:Function) RETURN n.name LIMIT 5"
```

- 更新（ドライラン＝ロールバック）
```powershell
uv run code_generator\debug_neo4j.py --cypher "MATCH (n:Function {name:'X'}) SET n.flag=true" --write
```

- 更新（実反映）
```powershell
uv run code_generator\debug_neo4j.py --cypher "MATCH (n:Function {name:'X'}) SET n.flag=true" --write --commit
```

- 実行計画のみ
```powershell
uv run code_generator\debug_neo4j.py --cypher "MATCH (n:Function) RETURN n LIMIT 10" --explain
```

- 複数文をファイルから
```powershell
uv run code_generator\debug_neo4j.py --file .\scripts\fix.cypher --write --commit
```

- パラメータ指定（複数可）
```powershell
uv run code_generator\debug_neo4j.py --cypher "MATCH (n:Function {name:$name}) RETURN n" --param name=CreateSolid
```

- ノードの詳細 / 近傍
```powershell
uv run code_generator\debug_neo4j.py --show-id "<elementId>"
uv run code_generator\debug_neo4j.py --neighbors "<elementId>" --limit 25
```

注意:
- 更新系（`CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|INDEX|CONSTRAINT`）が含まれる場合は `--write` が必須です。
- `--write` だけではコミットされません。反映するには `--commit` が必要です。指定が無ければロールバックされます。

---

## Neo4j → Chroma 再インジェスト: `code_generator.db.ingest_to_chroma`

スキーマ変更や `elementId` の不一致がある場合、現在のNeo4jの実体に合わせて再インジェストすると整合が取れます。

```powershell
uv run -m code_generator.db.ingest_to_chroma --label Function --collection api_functions_fn --persist-dir chroma_db_store
```

オプション:
- `--label` 取得対象のラベル（例: `Function`, 既定は `ApiFunction`）
- `--collection` Chroma コレクション名（新規作成可）
- `--persist-dir` Chroma の永続化ディレクトリ
- `--require-description` 設定時は `description` の無いノードを除外

---

## 推奨ワークフロー

1. ラベル確認 → `--list-labels` / `--count --label <Label>` / `--sample`
2. 現在のラベルで再インジェスト（新コレクション）
3. `--query` で Chroma ↔ Neo4j の一致確認
4. `debug_scores.py` でスコア分布を見て閾値を `.env` に設定
5. 必要に応じて `--cypher` / `--file` を使い、ノードやリレーションを修正（`--write --commit`）

---

## トラブルシューティング

- `Neo4j のノードが見つからない`: DB 名（`NEO4J_DATABASE`）が一致しているか確認
- `Chroma のディレクトリが無い`: `chroma_db_store` が存在するか、再インジェストを実行
- `OPENAI_API_KEY が無い`: `.env` を確認。`debug_chroma.py`/`debug_scores.py`/`--query` は埋め込み作成で必須
- PowerShell の `| cat` エラー: パイプ不要です（標準出力に直接表示されます）
- LangChain の Chroma 非推奨警告: 現状は実行に影響なし。将来 `langchain-chroma` への移行を推奨

---

## 参考ファイル

- `code_generator/debug_chroma.py`
- `code_generator/debug_scores.py`
- `code_generator/debug_neo4j.py`
- `code_generator/db/ingest_to_chroma.py`


