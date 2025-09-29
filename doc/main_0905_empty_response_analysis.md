# main_0905.py Empty Response 問題分析レポート

## 概要
`main_0905.py`で実行されるハイブリッド検索システムにおいて、「グラフ検索結果: Empty Response」が発生する問題の詳細分析レポートです。

**分析対象**: `cypher_template_demo.log`  
**分析日時**: 2025年9月29日  
**実行環境**: Windows 10, Python 3.10.11, Neo4j 2025.07.0

## LlamaIndex `engine.query()` 技術検証結果

### 検証目的
LlamaIndexの`engine.query()`が通常のNeo4jデータ（Function, Parameter等）で技術的に使用可能かどうかの検証

### 検証実施日時
**実行日時**: 2025年9月29日 16:52:53 - 16:54:36  
**実行環境**: Windows 10, Python 3.10.11, Neo4j 2025.07.0  
**質問**: "CreateVariableの引数と返り値"

### 技術検証結果

#### 1. LlamaIndex初期化フェーズ
```
2025-09-29 16:52:53,936 INFO main_helper_0905: PropertyGraphQueryEngineの構築が完了しました。
```

**実行内容**:
- ✅ **PropertyGraphIndex.from_existing**: 正常に初期化完了
- ✅ **Neo4j接続確立**: `docparser`データベースに正常接続
- ✅ **制約作成**: `__Node__`, `__Entity__`のユニーク制約を正常作成
- ✅ **ベクトルインデックス**: `__Entity__`のベクトルインデックスを正常作成

#### 2. データベース状況確認
```
サンプルFunctionノード（詳細）: [
  <Record name='Quit' description='EvoShipを終了する...'>,
  <Record name='ShowMainWindow' description='EvoShipのメインウィンドウを表示する...'>,
  <Record name='LoadPart' description='Partオブジェクトを読み込む...'>,
  <Record name='OpenDocument' description='Documentを開く...'>,
  <Record name='Create3DDocument' description='3DのDocumentを新規に作成する...'>
]

グラフスキーマ: [
  <Record nodeType=':`Type`' properties=['name', 'description']>,
  <Record nodeType=':`ObjectDefinition`' properties=['name', 'description', 'category']>,
  <Record nodeType=':`Parameter`' properties=['name', 'description', 'parent_object', 'parent_function', 'is_required']>,
  <Record nodeType=':`Function`' properties=['name', 'description', 'category', 'implementation_status', 'notes']>
]
```

**データベース統計**:
- **Function件数**: 72件
- **Parameter件数**: 479件
- **CreateVariable一致件数**: 1件

#### 3. LlamaIndex検索クエリの実行

**実行されたCypherクエリ**:
```cypher
-- 1. エンティティ検索
MATCH (e: __Node__) WHERE e.id IS NOT NULL AND e.id in $ids 
WITH e
RETURN e.id AS name,
       [l in labels(e) WHERE l <> '__Entity__' | l][0] AS type,
       e{.* , embedding: Null, id: Null} AS properties

-- 2. グラフ構造検索
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

**クエリパラメータ**:
```json
{
  "ids": ["Cypher", "Neo4j", "Createvariable", "Createvariable", "Create variable", "Function", "Parameter", "Parameters", "引数", "戻り値"],
  "limit": 30
}
```

#### 4. 検索結果

**1. エンティティ検索結果**:
```
2025-09-29 16:53:35,494 DEBUG neo4j.io: [#D34F] S: SUCCESS {'statuses': [{'gql_status': '02000', 'status_description': 'note: no data'}], 'type': 'r', 't_last': 5, 'db': 'docparser'}
```

**2. グラフ構造検索結果**:
```
2025-09-29 16:53:35,500 DEBUG neo4j.io: [#D34F] S: SUCCESS {'statuses': [{'gql_status': '02000', 'status_description': 'note: no data'}], 'type': 'r', 't_last': 1, 'db': 'docparser'}
```

**3. 最終レスポンス**:
```
2025-09-29 16:53:35,502 DEBUG main_helper_0905: グラフ検索レスポンス: Response(response='Empty Response', source_nodes=[], metadata=None)
2025-09-29 16:53:35,502 DEBUG main_helper_0905: グラフ検索レスポンス (文字列): 'Empty Response'
```

### 問題の根本原因分析

#### 1. データ構造の不一致

**LlamaIndexが期待するラベル**:
- `__Node__`: テキストチャンクやドキュメントノード
- `__Entity__`: エンティティノード（人物、場所、概念等）

**実際のNeo4jデータのラベル**:
- `Function`: API関数ノード
- `Parameter`: 関数パラメータノード
- `Type`: データ型ノード
- `ObjectDefinition`: オブジェクト定義ノード

#### 2. データ取得の失敗

| 検索段階 | 期待するラベル | 実際のラベル | 結果 |
|----------|----------------|--------------|------|
| エンティティ検索 | `__Node__` | `Function`, `Parameter` | ❌ データなし |
| グラフ構造検索 | `__Entity__` | `Function`, `Parameter` | ❌ データなし |

#### 3. フォールバック処理の動作

フォールバック処理が発動し、直接Neo4jクエリを実行：
```
診断: Function件数=72, keyword一致件数=1, Parameter件数=479
サンプルFunction名: Quit, ShowMainWindow, LoadPart, OpenDocument, Create3DDocument
```

### 技術検証の結論

#### 検証結果サマリー

| 項目 | 結果 | 詳細 |
|------|------|------|
| **LlamaIndex初期化** | ✅ 成功 | PropertyGraphIndex正常作成 |
| **Neo4j接続** | ✅ 成功 | データベース接続確立 |
| **制約・インデックス作成** | ✅ 成功 | `__Node__`, `__Entity__`制約作成 |
| **Cypherクエリ実行** | ✅ 成功 | クエリ正常実行 |
| **データ取得** | ❌ 失敗 | 期待するラベルが存在しない |
| **最終結果** | ❌ 空 | "Empty Response"を返す |

#### 技術的制約

**LlamaIndex `engine.query()` の制約**:

1. **データ構造の制約**: 
   - LlamaIndexが作成した特殊なラベル（`__Node__`, `__Entity__`）を期待
   - 通常のNeo4jデータ（`Function`, `Parameter`等）は認識しない

2. **事前処理の必要性**:
   - 通常のNeo4jデータをLlamaIndex形式に変換する必要がある
   - エンティティ抽出とトリプレット生成が必要

3. **スキーマの依存性**:
   - LlamaIndexの固定スキーマに依存
   - カスタムスキーマへの対応が困難

#### 実用性の評価

**LlamaIndex `engine.query()` の実用性**:

- ✅ **技術的動作**: エラーなく実行される
- ❌ **データ互換性**: 通常のNeo4jデータには非対応
- ❌ **実用性**: 事前データ変換が必要
- ❌ **柔軟性**: カスタムスキーマに対応困難

### 推奨アプローチ

#### 1. カスタムグラフ検索エンジンの実装
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

#### 2. ハイブリッド検索の最適化
- **ベクトル検索**: ChromaDBで意味的類似性検索
- **グラフ検索**: カスタムNeo4jクエリで構造的関係性検索
- **統合回答**: LangChainで結果統合

#### 3. データ変換パイプラインの構築
```python
def convert_to_llamaindex_format(neo4j_data):
    """Neo4jデータをLlamaIndex形式に変換"""
    # Function -> __Entity__ 変換
    # Parameter -> __Entity__ 変換
    # リレーションシップ -> LlamaIndex形式変換
    pass
```

### 最終結論

**LlamaIndex `engine.query()` は技術的に動作しますが、通常のNeo4jデータ（Function, Parameter等）を直接使用することはできません。**

**推奨解決策**:
1. **短期**: カスタムグラフ検索エンジンの実装
2. **中期**: ハイブリッド検索システムの最適化
3. **長期**: LlamaIndex対応データ変換パイプラインの構築

---

**レポート作成日**: 2025年9月29日  
**分析対象**: `cypher_template_demo.log`  
**技術検証**: LlamaIndex `engine.query()` 動作確認  
**分析者**: AI Assistant
