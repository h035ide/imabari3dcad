### code_generator モジュール概要

LangChainベースのコード生成エージェント。前検証(Pre‑flight)→生成→静的検証(flake8)→単体テスト実行(unittest)の自己修正ループで、最終的に構造化出力(`FinalAnswer`)を返します。検索はGraph/Vectorのハイブリッド（Chroma/Neo4j、またはLlamaIndexルーター）に対応。

### 主要コンポーネント
- `agent.py`
  - ツール: `user_query_parameter_extractor`, `hybrid_graph_knowledge_search`(or `llamaindex_hybrid_search`), `python_code_validator`, `python_unit_test_runner`
  - 出力: `schemas.FinalAnswer`（説明・imports・code_body）
- `tools.py`
  - `ParameterExtractionTool`: ユーザー要求から意図/パラメータを抽出。
  - `GraphSearchTool`: Chromaの類似検索→Neo4j詳細取得（曖昧さ検出あり）。
  - `LlamaIndexHybridSearchTool`: 既存ベクトル/グラフエンジンをルーティング。
  - `CodeValidationTool`: flake8で静的検証。
  - `UnitTestTool`: unittestを一時ディレクトリで実行。
- `db/ingest_to_chroma.py`: Neo4jのノードを埋め込み化しChromaへ永続化。
- `main.py`: REPL形式の対話実行。

### 環境変数(.env)
- `OPENAI_API_KEY`
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`
- `USE_LLAMAINDEX`（"1"で有効化）
- `AMBIGUITY_ABSOLUTE_THRESHOLD`, `AMBIGUITY_RELATIVE_THRESHOLD`（曖昧性判定）

### 事前準備（ハイブリッド検索）
```bash
# Neo4j -> Chroma 取り込み（デフォルト: label=ApiFunction）
python -m code_generator.db.ingest_to_chroma --label ApiFunction --database neo4j
```

### 実行
```bash
python -m code_generator.main
```

### 検索とグラフ前提
- `GraphSearchTool` のCypherは `ApiFunction` ノードと `(:Function)-[:IMPLEMENTS_API]->(:ApiFunction)` 等の関係を参照します。
  - 現状の `doc_paser` の投入スキーマ(Type/ObjectDefinition/Function/Parameter)だけでは `ApiFunction` が存在しません。
  - そのため、APIカタログを `ApiFunction` スキーマで別途整備するか、`LlamaIndexHybridSearchTool` の利用を推奨します。

### 参考ドキュメント
- `code_generator/doc/COMPREHENSIVE_SYSTEM_ANALYSIS_2025.md`
- `code_generator/doc/HYBRID_RAG_DESIGN.md`
- `code_generator/doc/LLAMAINDEX_INTEGRATION_GUIDE.md`


