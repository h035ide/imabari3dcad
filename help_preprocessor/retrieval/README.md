# Help Preprocessor - Advanced Retrieval System

EVOSHIPヘルプドキュメント用の高度なハイブリッド検索システムです。密ベクトル、疎ベクトル、全文検索、グラフ検索を組み合わせた多段階検索を提供します。

## 🚀 **主な機能**

### **1. マルチモーダル検索**
- **密ベクトル検索**: OpenAI Embeddings + Chroma による意味的検索
- **疎ベクトル検索**: TF-IDF + BM25 によるキーワードマッチング
- **全文検索**: Whoosh + Elasticsearch による高度なクエリ検索
- **グラフ検索**: Neo4j による関連性・階層検索

### **2. インテリジェント結果統合**
- **Reciprocal Rank Fusion (RRF)**: 複数検索結果の効果的な統合
- **重み付き統合**: 検索手法別の重要度調整
- **Borda Count**: ランキングベースの統合
- **適応的統合**: クエリ特性に基づく自動選択

### **3. LangChain/LlamaIndex統合**
- **RAG (Retrieval-Augmented Generation)**: 検索拡張生成
- **対話型チャット**: メモリ付き会話システム
- **カスタムプロンプト**: ヘルプシステム専用の最適化

## 📊 **アーキテクチャ概要**

```
User Query
    ↓
Query Router (適応的ルーティング)
    ↓
┌─────────────────────────────────────────────────────────┐
│  並列検索実行                                              │
├─────────────────┬─────────────────┬─────────────────────┤
│ Dense Search    │ Sparse Search   │ Full-text Search    │
│ (Chroma)        │ (TF-IDF/BM25)   │ (Whoosh/ES)         │
├─────────────────┴─────────────────┴─────────────────────┤
│ Graph Search (Neo4j)                                   │
└─────────────────────────────────────────────────────────┘
    ↓
Result Fusion Engine (RRF/重み付き/Borda/適応的)
    ↓
┌─────────────────────────────────────────────────────────┐
│  統合結果                                                │
├─────────────────┬─────────────────┬─────────────────────┤
│ LangChain       │ LlamaIndex      │ Raw Results         │
│ (RAG/Chat)      │ (QueryEngine)   │ (Direct Search)     │
└─────────────────┴─────────────────┴─────────────────────┘
    ↓
Final Response
```

## 🛠️ **セットアップ**

### **必要な依存関係**

```bash
# 基本パッケージ
uv pip install scikit-learn whoosh

# 密ベクトル検索
uv pip install chromadb openai

# グラフ検索
uv pip install neo4j

# LangChain統合
uv pip install langchain langchain-openai

# LlamaIndex統合
uv pip install llama-index

# Elasticsearch (オプション)
uv pip install elasticsearch
```

### **データ準備**

```bash
# ヘルプデータの前処理
uv run help-preprocess --dry-run  # 動作確認
uv run help-preprocess             # 実際の処理

# 検索インデックスの確認
ls data/sparse_index/    # TF-IDF インデックス
ls data/whoosh_index/    # Whoosh インデックス
ls data/help_preprocessor/chroma/  # Chroma ベクトルDB
```

## 🔍 **使用方法**

### **1. コマンドライン検索**

```bash
# 基本検索
uv run help-search --query "船舶設計の手順"

# ハイブリッド検索（全手法使用）
uv run help-search --query "船舶設計" --top-k 10 --output-format detailed

# 特定手法のみ使用
uv run help-search --query "エラー対処" --search-types sparse fulltext

# RAGモード（回答生成）
uv run help-search --query "船体構造の設計方法は？" --mode rag

# 対話型チャット
uv run help-search --interactive --mode chat
```

### **2. プログラムからの利用**

#### **基本的な検索**

```python
from help_preprocessor.retrieval import create_help_langchain_system
from help_preprocessor.retrieval.base import QueryContext

# システム初期化
system = create_help_langchain_system()
hybrid_retriever = system["hybrid_retriever"]

# 検索実行
context = QueryContext(
    query="船舶設計の基本手順",
    top_k=5,
    search_types=["dense", "sparse", "fulltext"],
    fusion_method="adaptive"
)

results = hybrid_retriever.search(context)

for result in results:
    print(f"[{result.source}] Score: {result.score:.3f}")
    print(f"Content: {result.content[:200]}...")
    print()
```

#### **RAG（検索拡張生成）**

```python
# LangChain RAG
rag_chain = system["rag_chain"]
response = rag_chain.query("船体構造の設計で注意すべき点は？")

print("回答:", response["answer"])
print("\n参照ドキュメント:")
for doc in response["source_documents"]:
    print(f"- {doc['metadata'].get('title', 'Unknown')}")
```

#### **対話型チャット**

```python
# 対話型チャット
chat_chain = system["conversational_chain"]

# 最初の質問
response1 = chat_chain.chat("船舶設計について教えて")
print("回答1:", response1["answer"])

# フォローアップ質問（文脈を保持）
response2 = chat_chain.chat("具体的な手順は？")
print("回答2:", response2["answer"])
```

#### **LlamaIndex統合**

```python
from help_preprocessor.retrieval import create_help_llamaindex_system

# LlamaIndex システム
system = create_help_llamaindex_system()

# QueryEngine使用
query_engine = system["query_engine"]
response = query_engine.query("エラーが発生した場合の対処法")

print("回答:", response["answer"])
print("ソース:", len(response["source_nodes"]), "件")
```

### **3. 高度な設定**

#### **カスタム設定ファイル**

```json
{
  "enable_dense": true,
  "enable_sparse": true,
  "enable_fulltext": true,
  "enable_graph": true,
  "fusion_method": "weighted",
  "source_weights": {
    "dense": 1.0,
    "sparse_tfidf": 0.8,
    "sparse_bm25": 0.8,
    "fulltext_whoosh": 0.6,
    "graph_neo4j": 0.5
  },
  "llm_model": "gpt-4",
  "chroma_collection": "evoship-help",
  "neo4j_uri": "bolt://localhost:7687",
  "neo4j_username": "neo4j",
  "neo4j_password": "password"
}
```

```bash
# 設定ファイル使用
uv run help-search --config config.json --query "設計手順"
```

## 📈 **検索手法の特徴**

### **密ベクトル検索（Dense Vector）**
- **適用場面**: 意味的類似性、概念検索、多言語対応
- **長所**: 高い意味理解、同義語・関連語も検索
- **短所**: 計算コスト高、完全一致に弱い

```python
# 例: "船舶" → "船", "海洋構造物", "maritime" なども検索
```

### **疎ベクトル検索（Sparse Vector）**
- **適用場面**: キーワードマッチング、専門用語、正確な検索
- **長所**: 高速、軽量、正確なマッチング
- **短所**: 意味理解なし、同義語に弱い

```python
# TF-IDF: 文書頻度ベースの重み付け
# BM25: より高度な関連性スコア（Elasticsearchで使用）
```

### **全文検索（Full-text）**
- **適用場面**: 複雑なクエリ、ファセット検索、フィルタ検索
- **長所**: 柔軟なクエリ構文、高速インデックス
- **短所**: セットアップ複雑、チューニング必要

```python
# Whoosh: 軽量、Pythonネイティブ
# Elasticsearch: 高機能、分散対応
```

### **グラフ検索（Graph）**
- **適用場面**: 関連性探索、階層検索、概念間の関係
- **長所**: 関係性理解、探索的検索
- **短所**: クエリ複雑、大規模データでのパフォーマンス

```python
# Neo4j Cypher例:
# MATCH (topic:HelpTopic)-[:BELONGS_TO]->(category:HelpCategory)
# WHERE topic.title CONTAINS "設計"
# RETURN topic, category
```

## 🎯 **結果統合戦略**

### **Reciprocal Rank Fusion (RRF)**
```python
# RRFスコア = Σ(1 / (k + rank_i))
# k=60が一般的、異なる検索手法の結果を効果的に統合
```

### **重み付き統合**
```python
# 各検索手法に重みを設定
weights = {
    "dense": 1.0,      # 意味的検索を重視
    "sparse": 0.8,     # キーワード検索
    "fulltext": 0.6,   # 全文検索
    "graph": 0.5       # 関係性検索
}
```

### **適応的統合**
```python
# クエリ特性に基づく自動選択
# - 短いクエリ → RRF
# - 技術用語多数 → 重み付き
# - 一般的クエリ → Borda Count
```

## 🔧 **トラブルシューティング**

### **検索結果が少ない場合**
```bash
# 各手法の個別確認
uv run help-search --query "your_query" --search-types dense --output-format detailed
uv run help-search --query "your_query" --search-types sparse --output-format detailed
```

### **パフォーマンス最適化**
```python
# 結果数制限
context = QueryContext(query="...", top_k=3)  # デフォルト5→3に削減

# 使用手法限定
context = QueryContext(query="...", search_types=["dense", "sparse"])
```

### **メモリ使用量削減**
```python
# 重いモデルの無効化
config = HybridRetrieverConfig(
    enable_dense=False,    # OpenAI Embeddings無効
    enable_graph=False     # Neo4j無効
)
```

## 📚 **応用例**

### **1. 技術サポートシステム**
```python
def technical_support_search(user_query: str, error_code: str = None):
    context = QueryContext(
        query=f"{user_query} {error_code or ''}",
        search_types=["sparse", "fulltext"],  # 正確なマッチング重視
        fusion_method="weighted"
    )
    return hybrid_retriever.search(context)
```

### **2. 学習支援システム**
```python
def learning_assistant(topic: str, difficulty_level: str = "beginner"):
    # 関連トピックも含めて幅広く検索
    context = QueryContext(
        query=topic,
        search_types=["dense", "graph"],  # 意味的・関係性検索
        top_k=10
    )
    return rag_chain.query(f"{topic}について{difficulty_level}向けに説明してください")
```

### **3. 品質管理システム**
```python
def quality_check_search(process_name: str):
    # 手順書と関連する品質基準を検索
    context = QueryContext(
        query=f"{process_name} 品質管理 チェックリスト",
        search_types=["fulltext", "graph"],
        fusion_method="borda"
    )
    return hybrid_retriever.search(context)
```

このハイブリッド検索システムにより、EVOSHIPヘルプドキュメントから高精度で多角的な情報検索が可能になります。
