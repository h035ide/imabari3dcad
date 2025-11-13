# RAG比較機能 - 設定ファイル管理

設定ファイルを使用して、RAG方式の定義やデフォルト設定を管理できます。機密情報（APIキー、パスワードなど）は`.env`ファイルで管理します。

## 設定ファイルの作成

デフォルト設定ファイルを作成：

```bash
uv run python -m helpfile_parser.rag_comparison init-config
```

これにより、`rag_comparison_config.json`が作成されます。

カスタムパスに作成：

```bash
uv run python -m helpfile_parser.rag_comparison init-config --output my_config.json
```

## 設定ファイルの構造

```json
{
  "rag_configs": [
    {
      "name": "vector_store_default",
      "description": "VectorStoreIndex (Chroma)（chunk_size=800, overlap=120）",
      "rag_type": "vector_store",
      "chunk_size": 800,
      "chunk_overlap": 120,
      "use_llm_extract": false,
      "llm_model": null,
      "embed_kg_nodes": true,
      "database": null,
      "chroma_persist_dir": null,
      "chroma_collection": null
    }
  ],
  "default_settings": {
    "top_k": 5,
    "log_level": "INFO",
    "console_level": "WARNING",
    "default_rag_type": "property_graph",
    "default_chunk_size": 800,
    "default_chunk_overlap": 120
  },
  "metadata": {
    "version": "1.0",
    "description": "RAG比較機能の設定ファイル",
    "note": "機密情報（APIキー、パスワードなど）は.envファイルで管理してください"
  }
}
```

## 設定ファイルの使用

### 設定ファイルを指定して実行

```bash
# 設定ファイルを指定してインデックスを構築
uv run python -m helpfile_parser.rag_comparison build evoship/EVOSHIP_HELP_FILES \
  --config-file rag_comparison_config.json

# 設定ファイルを指定して質問を実行
uv run python -m helpfile_parser.rag_comparison query "質問文" \
  --config-file rag_comparison_config.json

# 設定ファイルの設定のみを使用（デフォルト設定を無視）
uv run python -m helpfile_parser.rag_comparison query "質問文" \
  --config-file rag_comparison_config.json \
  --use-file-only
```

### 設定ファイルとデフォルト設定のマージ

- デフォルト（`--use-file-only`なし）: 設定ファイルの設定とデフォルト設定をマージ。設定ファイルの設定が優先されます。
- `--use-file-only`: 設定ファイルの設定のみを使用。デフォルト設定は無視されます。

## 機密情報の管理

機密情報（APIキー、パスワードなど）は`.env`ファイルで管理してください。

### .envファイルの例

```env
# Neo4j接続情報
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

# OpenAI API
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### 設定ファイルに含めない情報

以下の情報は設定ファイルに含めず、`.env`ファイルで管理してください：

- `NEO4J_PASSWORD`: Neo4jパスワード
- `OPENAI_API_KEY`: OpenAI APIキー
- その他のAPIキーやパスワード

## カスタムRAG方式の追加

設定ファイルに新しいRAG方式を追加：

```json
{
  "rag_configs": [
    {
      "name": "custom_vector_store",
      "description": "カスタムVectorStoreIndex設定",
      "rag_type": "vector_store",
      "chunk_size": 600,
      "chunk_overlap": 100,
      "embed_kg_nodes": true,
      "chroma_persist_dir": "data/chroma_custom",
      "chroma_collection": "help_custom"
    }
  ]
}
```

## 設定ファイルの検証

設定ファイルが正しく読み込まれるか確認：

```bash
# 設定ファイルから読み込まれた方式を一覧表示
uv run python -m helpfile_parser.rag_comparison list --config-file rag_comparison_config.json
```

