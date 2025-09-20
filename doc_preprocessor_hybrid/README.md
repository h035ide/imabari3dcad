# ハイブリッド前処理パイプライン

このモジュールは、EVO.SHIP の API ドキュメントに対して二段階の前処理フローを構築します。

1. **決定的（ルールベース）抽出**
   - `api.txt` を解析し、パラメータや戻り値のメタデータを伴うオブジェクト／関数定義に変換します。
   - `api_arg.txt` を解析し、正規化された型記述に整えます。
   - 既存の `type_definitions` / `api_entries` スキーマに従うベースライン JSON を生成します。
2. **対象を絞った LLM 補強（任意）**
   - 説明不足や分類が曖昧な項目など、あいまいなエントリのみを LLM に送ります。
   - 変更された断片をトレーサビリティを保ったままベースライン JSON にマージします。
3. **構造化された出力**
 - `structured_api.json`: スキーマに整合した、補強後のビュー。
 - `graph_payload.json`: Neo4j 取り込み用のトリプルとノードメタデータ。
 - `vector_chunks.jsonl`: ベクターデータベース構築用のテキストチャンク。

決定的なレイヤーでは既存パイプラインのルールベースの強みを再利用し、第2段階では LLM の利用範囲を限定して監査可能性を保ちます。

## 使い方

```bash
python -m doc_preprocessor_hybrid.cli --api-doc data/src/api.txt --api-arg data/src/api_arg.txt --output-dir doc_preprocessor_hybrid/out
```

補強ステップを有効にするには、`--llm`（有効な `OPENAI_API_KEY` が必要）を追加してください。
## 外部ストレージへの格納

`structured_api_enriched.json` を既に生成済みであれば、同梱のローダーを使って Neo4j と ChromaDB へデータを同期できます。接続設定は環境変数で行います。

### Neo4j

| 環境変数 | 説明 |
| --- | --- |
| `NEO4J_URI` | 例: `bolt://localhost:7687` |
| `NEO4J_USERNAME` / `NEO4J_USER` | ログインユーザー |
| `NEO4J_PASSWORD` | パスワード |
| `NEO4J_DATABASE` | (任意) 対象データベース名 |
| `NEO4J_CLEAR` | (任意) `false` の場合は既存ノードを保持 |

```
python -m doc_preprocessor_hybrid.cli --store-neo4j
```

### ChromaDB

| 環境変数 | 説明 |
| --- | --- |
| `CHROMA_COLLECTION` | コレクション名 (必須) |
| `CHROMA_PERSIST_DIRECTORY` | 例: `vector_store` (既定値) |
| `CHROMA_CLEAR` | (任意) `false` で増分アップサート |
| `CHROMA_EMBEDDING_PROVIDER` | `openai` (既定) または `sentence-transformers` |
| `CHROMA_EMBEDDING_MODEL` | 使用モデル (未設定時は既定値) |
| `OPENAI_API_KEY` | `openai` プロバイダー利用時に必須 |

```
python -m doc_preprocessor_hybrid.cli --store-chroma
```

Neo4j/Chroma を同時に実行するには `--store-neo4j --store-chroma` を併用してください。
### LLM 補強時のソース参照

`--llm` 実行時には、ルールベースで切り出した `api.txt` / `api_arg.txt` の抜粋も併せてプロンプトへ送信するようになりました。これにより LLM は原文の文脈を参照しながら最小限の追記を行います。`api.txt` からは対象 API の近傍行、`api_arg.txt` からは関連する型定義を自動抽出します。
