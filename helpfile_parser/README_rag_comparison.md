# HTML形式のRAG化 - 複数方式比較機能

HTML形式のRAG化について、複数の方式を検討し、それぞれに対して同じ質問を行い、応答を比較する機能を提供します。

## 機能概要

- **複数のRAG方式の定義**: 異なるチャンクサイズ、オーバーラップ、抽出方法などを設定
- **インデックス構築**: 各方式でインデックスを構築（複数のNeo4jデータベースに対応）
- **質問実行と比較**: 各方式で同じ質問を実行し、結果を比較
- **結果の可視化**: JSON形式とMarkdown形式で結果を出力
- **実行セッション管理**: 実行ごとにディレクトリを作成し、ログ、生成物、クエリを自動保存

## 実行セッション管理

各実行（`build`, `query`, `compare`コマンド）ごとに、タイムスタンプ付きのディレクトリが`logs/`配下に自動作成されます。

### ディレクトリ構造

```
logs/
  └── {command}_{YYYYMMDD_HHMMSS}/
      ├── execution.log          # 実行ログ
      ├── queries.txt            # 実行したクエリの記録
      ├── configs.json           # 使用したRAG設定
      ├── summary.json           # 実行サマリー
      ├── error.log              # エラー発生時のエラーログ（該当時のみ）
      └── results/               # 結果保存ディレクトリ
          ├── comparison_results.json
          └── comparison_results.md
```

### 保存される情報

- **execution.log**: 実行中のすべてのログメッセージ
- **queries.txt**: 実行した質問文とタイムスタンプ
- **configs.json**: 使用したRAG方式の設定（JSON形式）
- **summary.json**: 実行コマンド、パラメータ、結果のサマリー
- **results/comparison_results.json**: 比較結果（JSON形式）
- **results/comparison_results.md**: 比較結果（Markdown形式）
- **error.log**: エラー発生時の詳細なエラー情報とトレースバック

## 利用可能なRAG方式

デフォルトで以下の5つの方式が定義されています：

### PropertyGraphIndex方式
1. **property_graph_default**: PropertyGraphIndex（chunk_size=800, overlap=120, embed有効）

### VectorStoreIndex方式（LlamaIndex + Chroma）
2. **vector_store_default**: VectorStoreIndex (Chroma)（chunk_size=800, overlap=120）
3. **vector_store_small**: VectorStoreIndex (Chroma)（chunk_size=400, overlap=60）

### LangChain方式
4. **langchain_chroma_default**: LangChain + Chroma（chunk_size=800, overlap=120）
5. **langchain_neo4j**: LangChain + Neo4j Graph（既存のNeo4jデータを使用）

## RAG方式のタイプ

以下の4つのRAG方式タイプが利用可能です：

- **property_graph**: LlamaIndex PropertyGraphIndex（Neo4jを使用）
- **vector_store**: LlamaIndex VectorStoreIndex（Chromaを使用）
- **langchain_chroma**: LangChain + Chroma（ベクトル検索）
- **langchain_neo4j**: LangChain + Neo4j Graph（Cypher QA）

## 使い方

### 1. 利用可能な方式を一覧表示

```bash
uv run python -m helpfile_parser.rag_comparison list
```

### 2. インデックスを構築

すべてのデフォルト方式でインデックスを構築：

```bash
uv run python -m helpfile_parser.rag_comparison build <EVOSHIP_HELP_FILESのパス>
```

特定の方式のみでインデックスを構築：

```bash
uv run python -m helpfile_parser.rag_comparison build <EVOSHIP_HELP_FILESのパス> --configs default small_chunks
```

既存のインデックスを削除してから構築：

```bash
uv run python -m helpfile_parser.rag_comparison build <EVOSHIP_HELP_FILESのパス> --wipe
```

### 3. 単一の質問を実行して比較

```bash
uv run python -m helpfile_parser.rag_comparison query "質問文"
```

結果をJSON形式で保存：

```bash
uv run python -m helpfile_parser.rag_comparison query "質問文" --output results.json
```

結果をMarkdown形式で保存：

```bash
uv run python -m helpfile_parser.rag_comparison query "質問文" --markdown results.md
```

特定の方式のみで実行：

```bash
uv run python -m helpfile_parser.rag_comparison query "質問文" --configs default small_chunks
```

### 4. 複数の質問を一括で比較

```bash
uv run python -m helpfile_parser.rag_comparison compare --questions "質問1" "質問2" "質問3"
```

結果を保存：

```bash
uv run python -m helpfile_parser.rag_comparison compare \
  --questions "質問1" "質問2" "質問3" \
  --output results.json \
  --markdown results.md
```

## データベースの分離

各方式で異なるNeo4jデータベースを使用する場合は、`rag_comparison.py`の`DEFAULT_CONFIGS`を編集して、各方式の`database`パラメータを指定してください。

例：

```python
RAGConfig(
    name="small_chunks",
    description="小さなチャンク（chunk_size=400, overlap=60）",
    chunk_size=400,
    chunk_overlap=60,
    embed_kg_nodes=True,
    database="rag_small_chunks",  # 別DBを使用
),
```

## ログ設定

ログレベルと出力先を指定できます：

```bash
uv run python -m helpfile_parser.rag_comparison query "質問文" \
  --log-level DEBUG \
  --log-file logs/comparison.log \
  --console-level WARNING
```

## 出力形式

### JSON形式

各質問に対する各方式の結果が含まれます：

```json
[
  {
    "question": "質問文",
    "timestamp": "2025-11-05T10:00:00",
    "results": [
      {
        "config_name": "default",
        "question": "質問文",
        "answer": "回答内容",
        "retrieved_nodes_count": 5,
        "execution_time_seconds": 2.34,
        "error": null,
        "timestamp": "2025-11-05T10:00:01"
      },
      ...
    ]
  }
]
```

### Markdown形式

読みやすい形式で結果が出力されます：

```markdown
# 質問: 質問文

**実行日時**: 2025-11-05T10:00:00

## 結果比較

### default
**実行時間**: 2.34秒
**取得ノード数**: 5

**回答**:
```
回答内容
```

---
```

## 注意事項

1. **データベースの管理**: 各方式で同じデータベースを使用する場合、`--wipe`オプションを使用すると既存のデータが削除されます。異なるデータベースを使用することを推奨します。

2. **インデックス構築時間**: 各方式でインデックスを構築するには時間がかかります。特に`llm_extract`方式はLLMを使用するため、より時間がかかります。

3. **環境変数**: Neo4j接続情報とOpenAI APIキーが`.env`ファイルまたは環境変数に設定されている必要があります。

## カスタム方式の追加

新しいRAG方式を追加するには、`rag_comparison.py`の`DEFAULT_CONFIGS`に新しい`RAGConfig`を追加してください：

```python
RAGConfig(
    name="custom",
    description="カスタム設定",
    chunk_size=600,
    chunk_overlap=100,
    use_llm_extract=False,
    embed_kg_nodes=True,
    database="rag_custom",
),
```

