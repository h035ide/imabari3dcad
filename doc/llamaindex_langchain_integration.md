## LlamaIndex × LangChain 併用ガイド（設計/運用メモ）

### 結論
- LlamaIndexで構築したインデックス/QueryEngineは、LangChainのRetriever/Toolとしてラップ可能。
- 本プロジェクトは現状、取り込み（LangChain `OpenAIEmbeddings` + `Chroma`）と検索（LlamaIndex `ChromaVectorStore` → `VectorStoreIndex`）を分担しており“ハイブリッド構成”ができている。
- 追加のラップ（LangChain AgentへのTool化など）は「必要になってから」で十分。

### 役割分担（現状）
- 取り込み（ingest）：`main_helper_0905.py` の `ingest_data_to_chroma()`
  - LangChainの `OpenAIEmbeddings` と `Chroma` を使用
- 検索（query）：`main_helper_0905.py` の `build_vector_engine()`
  - LlamaIndexの `ChromaVectorStore` → `VectorStoreIndex` → `as_query_engine()` を使用
- グラフQA：`main_helper_0905.py` の `build_graph_engine()`
  - LlamaIndexの `Neo4jPropertyGraphStore` と `PropertyGraphIndex`

### いつラップすべきか（判断基準）
- すべきタイミング
  - LangChainのAgent/Tool選択を使いたい（複数ツール自動ルーティング）
  - LangSmithなどのトレーシング/モニタリングをLangChainで統一したい
  - 既存LangChainチェーンに、LlamaIndex検索を“1ツール”として統合したい
  - マルチソースRAGで他Retrieverと同一フレームで協調させたい
- まだ不要なタイミング
  - 単一RAGパイプラインで要件を満たしている
  - レイテンシや保守負荷（2フレームワーク追随）を最小化したい

### 最小統合パターン（LangChain Tool化の概念例）
```python
from langchain.tools import Tool

# どこかで LlamaIndex の QueryEngine を用意
# query_engine = build_vector_engine(persist_dir, collection, config)

def run_llamaindex(query: str) -> str:
    return str(query_engine.query(query))

li_tool = Tool(
    name="api_docs_search",
    func=run_llamaindex,
    description="APIドキュメントに対する高精度検索"
)
# li_tool を LangChain の Agent/Chain に組み込み
```

### メリット / デメリット
- メリット
  - LangChainエコシステム（Agents/Tools、Callbacks/Tracing、観測）を活用
  - 役割分担が明確（オーケストレーション=LangChain、索引/PGQA=LlamaIndex）
  - 既存の埋め込み/ベクターストア資産を共用しやすい
  - マルチツール・マルチコンテキストのRAG設計が柔軟
- デメリット
  - 依存/互換性の追随コスト（API変更の影響）
  - 二重抽象化でデバッグが複雑化（原因切り分けが難しい）
  - アダプタ層のオーバーヘッド（わずかなレイテンシ）
  - 設定の重複・ズレ（モデル/TopK/スコアの不一致）

### 現状コードの改善ポイント（優先順）
1) Chromaへの再取り込み時のID重複
   - 現状：`Chroma.add_texts()` は同一IDの更新（upsert）にならない場合がある
   - 対策：追加前に既存IDを削除、または `chromadb.PersistentClient` から `collection.upsert()` を利用

2) Neo4jデータベース名の不一致リスク
   - 現状：`fetch_data_from_neo4j()` は `os.getenv("NEO4J_DATABASE", "codeparsar")`、`build_graph_engine()` は `config.neo4j_database`（既定 `neo4j`）
   - 対策：`config.neo4j_database` を単一のソースオブトゥルースに統一

3) LLMモデル名と推論系パラメータの互換性
   - 現状：`gpt-5-mini` 想定、`reasoning_effort` などの適用互換に注意
   - 対策：実在モデル（例：`o4-mini` / `gpt-4o`）へ固定 or 環境変数で上書きし、該当モデル時のみ推論系パラメータ適用

4) ドキュメント数取得のAPI差
   - 現状：`vector_store.get()` はラッパーのバージョン差で `AttributeError` になり得る
   - 対策：`chromadb.PersistentClient` → `collection.get()` 等、正式APIでの取得に変更

5) Embeddingモデルの一元管理
   - 現状：取り込み/問い合わせで同一モデルを使っているが将来変更時に片側のみ変更のリスク
   - 対策：`Config` を単一ソースにし、双方必ず同じ設定を参照

6) `.env` ロード
   - 現状：OS環境変数依存
   - 対策：`python-dotenv` の導入または起動スクリプト側での明示ロード

7) `Settings` のグローバル副作用
   - 現状：`Settings.llm`/`Settings.embed_model` を関数内で上書き
   - 対策：並列エンジンがある場合の干渉に注意。可能ならローカルスコープ設定を検討

### 運用Tips
- Embedding/LLM/TopKなどの重要ハイパラは **`Config` に一元管理** し、取り込み・検索で同一値を参照
- バージョンを固定（`requirements.txt` / `uv.lock`）し、LangChain/LlamaIndex/Chroma の互換性を維持
- 例外時はバージョン・設定・クライアント種別をログ出力して原因切り分けを容易に

### 変更候補（最小）
- 取り込みのupsert対応：`chromadb` クライアント直利用に切り替え
- DB名の統一：`fetch_data_from_neo4j()` を `config.neo4j_database` 参照に統一
- 実在モデル/推論パラメータの整合：`Config` を環境変数で上書き可能にし、該当モデル時のみ推論系を付与

必要になれば、このドキュメントに沿って段階的に実装を進める。


