# Code Generator: ハイブリッドRAGアーキテクチャ分析と移行計画

## 目的

本ドキュメントは、`code_generator/` モジュールを分析し、課題・改善点・実装方針を網羅的に整理したうえで、LangChainのエージェントに対し、LlamaIndexのグラフRAG(Neo4j)とベクトルインデックス(Chroma)を統合したハイブリッド検索を実現するための設計・実装ガイドを提供します。

---

## 1. 現状の構成とデータフロー

- エージェント層: `langchain` の Functions Agent を使用（`agent.py`）。
  - ツール: `ParameterExtractionTool`（意図/パラメータ抽出）, `GraphSearchTool`（ベクトル+グラフ探索）, `CodeValidationTool`（flake8）, `UnitTestTool`（unittest）。
- ベクトル検索: `Chroma` に永続化（`db/ingest_to_chroma.py`）。
  - コレクション: `api_functions`
  - メタデータ: `api_name`, `neo4j_node_id`
- グラフ探索: `neo4j` ドライバでCypherを直接実行（`tools.py`）。
  - ラベル: `ApiFunction` を統一
  - 取得情報: API名/説明/パラメータ/呼び出し関係/戻り値/クラス など
- Re-Ranking: `rerank_feature/ReRanker`（CrossEncoder、任意）

現状のハイブリッド検索（簡略図）

1. Chromaに対して `similarity_search_with_score` → 候補抽出
2. 曖昧性検出（スコア差/比率）→ 必要に応じてユーザーに選択促し
3. Re-Rank（任意）→ 上位 `neo4j_node_id` を抽出
4. Neo4jに対してCypherで詳細取得 → 整形してエージェントに返却

---

## 2. 現状で把握したポイント

- 主要な不具合は解消済み
  - Neo4jラベル不一致（`ApiFunction`）の統一済み
  - フィールド名不一致（`apiDescription`）の整合済み
  - 単体テスト実行の成否判定を `returncode` ベースに修正済み
  - 起動時の警告ツールインデックス修正済み
  - 戻り値の型注釈（`Optional[AgentExecutor]`）へ修正済み
  - Chroma内部属性依存の排除（公開APIへ）

- 設計/運用上の改善余地
  - 曖昧性検出しきい値を環境変数化済みだが、調整ガイド/説明が不足
  - Re-Rankingは任意依存（`sentence-transformers`）で非活性フォールバック設計
  - LLMモデル指定の一貫性（エージェント/ツール間）を要改善
  - ログ設定の一元化（`main.py` 起点）
  - `Chroma` のimport系の混在（`langchain_chroma` vs `langchain_community`）の統一推奨

---

## 3. 期待仕様とのギャップ

期待: 「LangChainのAgent」×「LlamaIndexのGraph RAG(Neo4j) + Vector(Chroma)」によるハイブリッド検索が主軸。

現状: ハイブリッド検索はLangChain + 手書きロジックで実現。LlamaIndexは未導入。

→ 提案: LlamaIndexを用いた以下の統合を実施し、保守容易性・検索品質・拡張性を向上。

---

## 4. 改善方針（LlamaIndex統合の設計）

### 4.1 依存関係（追加）

```bash
pip install -U \
  llama-index \
  llama-index-graph-stores-neo4j \
  llama-index-vector-stores-chroma
```

### 4.2 既存データの再利用方針

- Vector: 既存のChroma永続化パス（`chroma_db_store`）とコレクション名（`api_functions`）をLlamaIndexの `ChromaVectorStore` で再利用
- Graph: 既存のNeo4jグラフを `Neo4jPropertyGraphStore` と `PropertyGraphIndex.from_existing(...)` でラップ

### 4.3 構成案（ハイブリッド検索）

1. Vector ルート
   - `ChromaVectorStore` → `VectorStoreIndex` → `as_query_engine()`
2. Graph ルート
   - `Neo4jPropertyGraphStore` → `PropertyGraphIndex.from_existing(...)` → `as_query_engine(include_text=..., similarity_top_k=...)`
3. ルーティング/ハイブリッド
   - RouterQueryEngine（意図に応じてVector/Graphを選択）
   - もしくはHybrid構成のRetriever（BM25 + Vector + Rerank）

LlamaIndexドキュメント参照（要点）

- Neo4j（PropertyGraph）: `Neo4jPropertyGraphStore`, `PropertyGraphIndex.from_existing(...)`
- Chroma: `ChromaVectorStore` → `StorageContext.from_defaults(vector_store=...)` → `VectorStoreIndex`
- ルータ: `RouterQueryEngine` と `QueryEngineTool`

---

## 5. 実装ガイド（段階的移行）

### 5.1 初期化ユーティリティの新設

`code_generator/llamaindex_integration.py`（新規）を作成し、初期化関数を提供:

```python
# 疑似コード（実装目安）
import os, chromadb
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.core import PropertyGraphIndex

def build_vector_engine(persist_dir: str, collection: str):
    client = chromadb.PersistentClient(path=persist_dir)
    col = client.get_or_create_collection(collection)
    vec_store = ChromaVectorStore(chroma_collection=col)
    storage = StorageContext.from_defaults(vector_store=vec_store)
    # 既存ベクトルのみからインデックスを構築
    vindex = VectorStoreIndex.from_vector_store(vec_store, storage_context=storage)
    return vindex.as_query_engine()

def build_graph_engine(uri: str, user: str, password: str, database: str):
    pg_store = Neo4jPropertyGraphStore(username=user, password=password, url=uri)
    gindex = PropertyGraphIndex.from_existing(property_graph_store=pg_store)
    return gindex.as_query_engine()
```

### 5.2 ツール統合（新設または置換）

- 新ツール `LlamaIndexHybridSearchTool` を追加（`tools.py` 同等のI/F）
  - 内部で上記 `build_*_engine()` を初期化
  - RouterQueryEngine もしくはハイブリッドRetrieverを構成
  - 応答は既存 `GraphSearchTool` の整形方針に合わせ、API名/説明/パラメータ/呼び出し関係などを人間可読に加工
- フィーチャーフラグ（例: `USE_LLAMAINDEX=1`）で `GraphSearchTool` と切替可能に

### 5.3 既存との整合

- 既存 `db/ingest_to_chroma.py` はそのまま利用（Chromaの永続化先・コレクション名を共通化）
- 既存Cypherに依存した出力形式を踏襲しつつ、LlamaIndexの `Node` から不足情報を補完

---

## 6. 改善項目（コード品質/運用）

- LLM設定の一貫性
  - `OPENAI_MODEL` / `OPENAI_TEMPERATURE` を全ツール/エージェントで統一的に参照
- ログ設定の集約
  - `main.py` を起点に `basicConfig`、各モジュールは `getLogger(__name__)` のみ
- しきい値チューニングの指針
  - `AMBIGUITY_ABSOLUTE_THRESHOLD`（既定0.1）/ `AMBIGUITY_RELATIVE_THRESHOLD`（既定1.1）の社内推奨レンジをREADMEに明記
- Importの統一
  - `Chroma` のimportは `langchain_chroma` に統一
- 依存パッケージ
  - `flake8`, `sentence-transformers`（任意）, `llama-index-*` の明示

---

## 7. テスト戦略

- ユニットテスト
  - LlamaIndex初期化（モック/スキップ条件）
  - LLM応答のパース/フォールバック
- 統合テスト
  - Vector→Graphの一連の検索フロー（少量のテストデータで）
  - フィーチャーフラグON/OFFの挙動
- E2E
  - 代表クエリ（API作成/検索/コード生成）で最終出力が既定フォーマットで返ること

---

## 8. 移行手順チェックリスト

1) 依存関係の追加（`llama-index-*`, `chromadb`）
2) `llamaindex_integration.py` の実装
3) 新ツール `LlamaIndexHybridSearchTool` の追加
4) 環境変数・設定の整理（モデル名/温度/しきい値/フラグ）
5) テスト追加（ユニット/統合/E2E）
6) ドキュメント更新（運用手順/しきい値調整ガイド）

---

## 9. リスクと回避策

- スキーマ差異: 既存Neo4jスキーマとLlamaIndexの期待フォーマット差
  - 回避: `PropertyGraphIndex.from_existing` を前提にし、必要に応じてカスタムRetrieval/クエリ調整
- 依存の肥大化: 追加パッケージによる環境負荷
  - 回避: フィーチャーフラグで段階導入、CIでの軽量モード（LLMモック）
- Re-Ranking依存: `sentence-transformers` の容量/実行時間
  - 回避: オプショナル化（現状どおり非活性時はパススルー）

---

## 10. 受け入れ基準（Doneの定義）

- `USE_LLAMAINDEX=1` でLlamaIndexルートが有効化され、
  - Vector/Graphの両ルートで検索可能
  - 代表クエリでGraph由来の属性（パラメータ、呼び出し元、戻り値など）が含まれる
- 既存のLangChainルート（フィーチャーフラグOFF）は従来どおり動作
- 主要テスト（ユニット/統合/E2E）がグリーン

---

## 参考（一次情報の抜粋）

- Neo4j（PropertyGraph）
  - `Neo4jPropertyGraphStore`: 既存グラフから `PropertyGraphIndex.from_existing(...)` で利用可
- Vector（Chroma）
  - `ChromaVectorStore` → `StorageContext.from_defaults(vector_store=...)` → `VectorStoreIndex`
- ルーティング/ハイブリッド
  - `RouterQueryEngine` と `QueryEngineTool` / `vector_store_query_mode="hybrid"`

（出典: LlamaIndex 公式ドキュメント/サンプルコード）
