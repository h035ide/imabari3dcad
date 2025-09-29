# LlamaIndex形式のNeo4jデータ構造について

## 概要

LlamaIndex形式のNeo4jデータとは、LlamaIndexの`PropertyGraphIndex`が期待する特定のラベルとプロパティを持つNeo4jデータベースの構造を指します。通常のNeo4jデータとは異なり、LlamaIndex専用の特殊なラベルとスキーマを使用します。

## LlamaIndexが期待するデータ構造

### 1. 特殊なラベル

LlamaIndexは以下の特殊なラベルを期待します：

#### `__Node__` ラベル
- **用途**: テキストチャンクやドキュメントノードを表現
- **必須プロパティ**: `id` (ユニーク識別子)
- **追加プロパティ**: `text`, `embedding` (ベクトル埋め込み)
- **追加ラベル**: `Chunk` (テキストチャンクの場合)

#### `__Entity__` ラベル
- **用途**: エンティティノード（人物、場所、概念等）を表現
- **必須プロパティ**: `id` (ユニーク識別子)
- **追加プロパティ**: `embedding` (ベクトル埋め込み)
- **追加ラベル**: エンティティの種類（例：`Person`, `Company`, `Location`）

### 2. 制約とインデックス

LlamaIndexは以下の制約とインデックスを自動的に作成します：

```cypher
-- ユニーク制約
CREATE CONSTRAINT IF NOT EXISTS FOR (n:`__Node__`)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS FOR (n:`__Entity__`)
REQUIRE n.id IS UNIQUE;

-- ベクトルインデックス
CREATE VECTOR INDEX entity IF NOT EXISTS 
FOR (m:__Entity__) ON m.embedding;
```

### 3. データ作成パターン

#### テキストチャンクノードの作成
```cypher
MERGE (c:__Node__ {id: row.id})
SET c.text = row.text, c:Chunk
WITH c, row
SET c += row.properties
WITH c, row.embedding AS embedding
WHERE embedding IS NOT NULL
CALL db.create.setNodeVectorProperty(c, 'embedding', embedding)
RETURN count(*)
```

#### エンティティノードの作成
```cypher
UNWIND $data AS row
MERGE (source: __Node__ {id: row.source_id})
ON CREATE SET source:Chunk
MERGE (target: __Node__ {id: row.target_id})
ON CREATE SET target:Chunk
WITH source, target, row
CALL apoc.merge.relationship(source, row.label, {}, row.properties, target) 
YIELD rel
RETURN count(*)
```

## 検索クエリパターン

### 1. エンティティ検索
```cypher
MATCH (e: __Node__) 
WHERE e.id IS NOT NULL AND e.id in $ids 
WITH e
RETURN e.id AS name,
       [l in labels(e) WHERE l <> '__Entity__' | l][0] AS type,
       e{.* , embedding: Null, id: Null} AS properties
```

### 2. グラフ構造検索
```cypher
WITH $ids AS id_list
UNWIND range(0, size(id_list) - 1) AS idx
MATCH (e:`__Entity__`)
WHERE e.id = id_list[idx]
MATCH p=(e)-[r*1..1]-(other)
WHERE ALL(rel in relationships(p) WHERE type(rel) <> 'MENTIONS')
UNWIND relationships(p) AS rel
WITH distinct rel, idx
WITH startNode(rel) AS source,
     type(rel) AS type,
     rel{.*} AS rel_properties,
     endNode(rel) AS endNode,
     idx
LIMIT toInteger($limit)
RETURN source.id AS source_id, 
       [l in labels(source) WHERE NOT l IN ['__Entity__', '__Node__'] | l][0] AS source_type,
       source{.* , embedding: Null, id: Null} AS source_properties,
       type,
       rel_properties,
       endNode.id AS target_id, 
       [l in labels(endNode) WHERE NOT l IN ['__Entity__', '__Node__'] | l][0] AS target_type,
       endNode{.* , embedding: Null, id: Null} AS target_properties,
       idx
ORDER BY idx
LIMIT toInteger($limit)
```

## 通常のNeo4jデータとの違い

### 現在のプロジェクトのデータ構造
```cypher
-- 現在使用されているラベル
:Function          -- API関数ノード
:Parameter         -- 関数パラメータノード
:Type              -- データ型ノード
:ObjectDefinition  -- オブジェクト定義ノード
```

### LlamaIndexが期待するデータ構造
```cypher
-- LlamaIndexが期待するラベル
:__Node__          -- テキストチャンクノード
:__Entity__        -- エンティティノード
:Chunk             -- チャンクラベル
:Person            -- 人物エンティティ
:Company           -- 企業エンティティ
:Location          -- 場所エンティティ
```

## データ変換の必要性

### 問題点
- **ラベルの不一致**: 通常のNeo4jデータは`Function`, `Parameter`等のラベルを使用
- **プロパティの不一致**: LlamaIndexは`id`, `text`, `embedding`等の特定プロパティを期待
- **スキーマの不一致**: リレーションシップの構造も異なる

### 解決策

#### 1. データ変換パイプラインの構築
```python
def convert_to_llamaindex_format(neo4j_data):
    """Neo4jデータをLlamaIndex形式に変換"""
    converted_nodes = []
    
    # Function -> __Entity__ 変換
    for function in neo4j_data['functions']:
        converted_nodes.append({
            'id': f"function_{function['name']}",
            'labels': ['__Entity__', 'Function'],
            'properties': {
                'name': function['name'],
                'description': function['description'],
                'category': function.get('category', '')
            }
        })
    
    # Parameter -> __Entity__ 変換
    for param in neo4j_data['parameters']:
        converted_nodes.append({
            'id': f"param_{param['name']}",
            'labels': ['__Entity__', 'Parameter'],
            'properties': {
                'name': param['name'],
                'description': param['description'],
                'parent_function': param['parent_function'],
                'is_required': param.get('is_required', False)
            }
        })
    
    return converted_nodes
```

#### 2. ハイブリッドアプローチ
- **ベクトル検索**: ChromaDBで意味的類似性検索
- **グラフ検索**: カスタムNeo4jクエリで構造的関係性検索
- **統合回答**: LangChainで結果統合

## 実装例

### LlamaIndex形式でのデータ作成
```python
from llama_index.core import PropertyGraphIndex
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore

# Neo4j接続設定
graph_store = Neo4jPropertyGraphStore(
    url="neo4j://localhost:7687",
    username="neo4j",
    password="password",
    database="demo"
)

# ドキュメントからLlamaIndex形式のグラフを作成
index = PropertyGraphIndex.from_vector_store(
    vector_store=vector_store,
    property_graph_store=graph_store,
    llm=llm,
    embed_model=embed_model,
)

# クエリエンジンの作成
query_engine = index.as_query_engine()
```

### カスタム検索の実装
```python
def custom_graph_search(query: str, neo4j_driver):
    """通常のNeo4jデータに対応したカスタム検索"""
    with neo4j_driver.session() as session:
        # Function検索
        function_result = session.run("""
            MATCH (f:Function) 
            WHERE toLower(f.name) CONTAINS toLower($query)
            OPTIONAL MATCH (p:Parameter) 
            WHERE toLower(p.parent_function) = toLower(f.name)
            RETURN f.name, f.description, collect(p) as parameters
        """, query=query)
        
        return format_function_results(function_result)
```

## まとめ

LlamaIndex形式のNeo4jデータは、LlamaIndexが効率的にグラフ検索を実行するために設計された特殊なデータ構造です。通常のNeo4jデータとは異なるラベルとプロパティを使用するため、既存のデータを使用する場合は適切な変換処理が必要です。

**推奨アプローチ**:
1. **短期**: カスタムグラフ検索エンジンの実装
2. **中期**: ハイブリッド検索システムの最適化
3. **長期**: LlamaIndex対応データ変換パイプラインの構築
