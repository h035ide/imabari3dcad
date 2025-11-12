# マイグレーション情報

## 旧ファイルについて

`ingest1025.py` は新しいモジュール構造にリファクタリングされました。

### 新しい構造への対応
- API解析処理 → `ingestion/api_parser.py`, `ingestion/llm_extractor.py`
- スクリプト解析処理 → `ingestion/script_analyzer.py`
- Neo4j処理 → `storage/neo4j_manager.py`
- ChromaDB処理 → `storage/chroma_manager.py`
- 統合処理 → `ingestion/orchestrator.py`
- メインエントリー → `main.py`

### 使用方法
```bash
# データ取り込み実行
uv run python -m rag_query.main ingest

# クエリ実行
uv run python -m rag_query.main query "メソッドの使い方を教えて"
```

旧ファイル（ingest1025.py）は参考用として残していますが、
新しい構造を使用することを推奨します。
