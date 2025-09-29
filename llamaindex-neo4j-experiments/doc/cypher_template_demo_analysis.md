# Cypher Template Demo 動作分析レポート

## 概要
`engine.query("Where does ACME locate?")`の実行におけるLlamaIndex + Neo4jの動作分析レポートです。

**実行日時**: 2025年9月29日 16:09:20 - 16:09:29  
**実行環境**: Windows 10, Python 3.10.11, Neo4j 2025.07.0  
**ログファイル**: `cypher_template_demo.log` (3,321行, 約290KB)

## 実行フロー分析

### 1. 初期化フェーズ (16:09:20.489 - 16:09:20.544)
```
Neo4j接続確立 → データベーススキーマ取得 → メタデータ収集
```

**主要処理**:
- Neo4j接続プール作成 (127.0.0.1:7687)
- データベース 'demo' への接続確立
- APOCメタデータ取得:
  - ノードラベルとプロパティ取得
  - リレーションシップタイプとプロパティ取得
  - 制約情報取得

### 2. ドキュメント処理フェーズ (16:09:21.034 - 16:09:25.882)
```
テキストチャンク作成 → トリプレット抽出 → エンベディング生成 → Neo4j格納
```

**処理詳細**:
1. **テキストチャンク作成**
   ```
   入力: "Taro works at ACME. ACME is based in Tokyo."
   チャンク: 1つのテキストチャンクとして処理
   ```

2. **知識トリプレット抽出** (OpenAI GPT-3.5-turbo使用)
   ```
   抽出されたトリプレット:
   - (Taro, Works at, Acme)
   - (Acme, Is based in, Tokyo)
   - (SOURCE関係の追加)
   ```

3. **エンベディング生成** (OpenAI text-embedding-ada-002)
   ```
   入力テキストのベクトル化: 1536次元のエンベディング
   ベクトルデータベースへの格納準備
   ```

4. **Neo4jデータ格納**
   ```
   ノード作成:
   - Taro (__Entity__)
   - Acme (__Entity__)
   - Tokyo (__Entity__)
   - テキストチャンク (__Node__, Chunk)
   
   リレーションシップ作成:
   - Taro -[Works at]-> Acme
   - Acme -[Is based in]-> Tokyo
   - ソース関係の追加
   ```

### 3. クエリ処理フェーズ (16:09:26.219 - 16:09:29.143)
```
クエリ分析 → エンベディング検索 → グラフ検索 → 回答生成
```

**処理ステップ**:

1. **クエリ分析とキーワード生成** (16:09:26.219)
   ```
   入力クエリ: "Where does ACME locate?"
   OpenAI API呼び出し: キーワード生成
   目的: クエリの同義語や関連語を生成
   ```

2. **エンベディングベース検索** (16:09:26.221)
   ```
   クエリのベクトル化: text-embedding-ada-002
   類似度検索: Neo4jベクトルインデックス
   関連ノード特定: Acme, Tokyo, Taro
   ```

3. **グラフ構造検索** (16:09:26.134 - 16:09:27.866)
   ```
   Cypherクエリ実行:
   - エンティティ間の関係探索
   - パス検索とコンテキスト取得
   - 関連データの収集
   ```

4. **最終回答生成** (16:09:27.900 - 16:09:29.143)
   ```
   コンテキスト情報:
   - Taro -> Works at -> Acme
   - Acme -> Is based in -> Tokyo
   - 元のテキスト: "Taro works at ACME. ACME is based in Tokyo."
   
   最終回答: "ACME is located in Tokyo."
   ```

## パフォーマンス分析

### 実行時間内訳
| フェーズ | 開始時刻 | 終了時刻 | 所要時間 |
|----------|----------|----------|----------|
| 初期化 | 16:09:20.489 | 16:09:20.544 | 55ms |
| ドキュメント処理 | 16:09:21.034 | 16:09:25.882 | 4.848s |
| クエリ処理 | 16:09:26.219 | 16:09:29.143 | 2.924s |
| **総実行時間** | - | - | **8.654s** |

### API呼び出し統計
| API | 呼び出し回数 | 用途 |
|-----|-------------|------|
| OpenAI Chat Completions | 3回 | トリプレット抽出、キーワード生成、回答生成 |
| OpenAI Embeddings | 2回 | テキストエンベディング、クエリエンベディング |
| Neo4j Cypher | 15回以上 | データ格納、検索、メタデータ取得 |

### データベース操作統計
| 操作 | 回数 | 説明 |
|------|------|------|
| ノード作成 | 4個 | Taro, Acme, Tokyo, テキストチャンク |
| リレーションシップ作成 | 3個 | Works at, Is based in, SOURCE |
| 検索クエリ | 8回 | エンティティ検索、関係検索、パス検索 |

## 技術的詳細

### 使用技術スタック
- **LlamaIndex**: PropertyGraphIndex, Neo4jPropertyGraphStore
- **Neo4j**: グラフデータベース、ベクトルインデックス
- **OpenAI**: GPT-3.5-turbo, text-embedding-ada-002
- **APOC**: メタデータ取得、関係作成

### Cypherクエリの詳細分析

#### 1. データベース初期化クエリ
```cypher
-- 制約作成
CREATE CONSTRAINT IF NOT EXISTS FOR (n:`__Node__`)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS FOR (n:`__Entity__`)
REQUIRE n.id IS UNIQUE;

-- ベクトルインデックス作成
CREATE VECTOR INDEX entity IF NOT EXISTS FOR (m:__Entity__) ON m.embedding
```

#### 2. メタデータ取得クエリ
```cypher
-- ノードラベルとプロパティ取得
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE NOT type = "RELATIONSHIP" AND elementType = "node"
  AND NOT label IN $EXCLUDED_LABELS
WITH label AS nodeLabels, collect({property:property, type:type}) AS properties
RETURN {labels: nodeLabels, properties: properties} AS output

-- リレーションシップタイプ取得
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE NOT type = "RELATIONSHIP" AND elementType = "relationship"
  AND NOT label in $EXCLUDED_LABELS
WITH label AS nodeLabels, collect({property:property, type:type}) AS properties
RETURN {type: nodeLabels, properties: properties} AS output
```

#### 3. ドキュメント格納クエリ
```cypher
-- テキストチャンクノード作成
UNWIND $data AS row
MERGE (c:__Node__ {id: row.id})
SET c.text = row.text, c:Chunk
WITH c, row
SET c += row.properties
WITH c, row.embedding AS embedding
WHERE embedding IS NOT NULL
CALL db.create.setNodeVectorProperty(c, 'embedding', embedding)
RETURN count(*)

-- リレーションシップ作成
UNWIND $data AS row
MERGE (source: __Node__ {id: row.source_id})
ON CREATE SET source:Chunk
MERGE (target: __Node__ {id: row.target_id})
ON CREATE SET target:Chunk
WITH source, target, row
CALL apoc.merge.relationship(source, row.label, {}, row.properties, target) YIELD rel
RETURN count(*)
```

#### 4. 検索クエリ
```cypher
-- エンティティ検索
MATCH (e: __Node__) WHERE e.id IS NOT NULL AND e.id in $ids 
WITH e
RETURN e.id AS name,
       [l in labels(e) WHERE l <> '__Entity__' | l][0] AS type,
       e{.* , embedding: Null, id: Null} AS properties

-- グラフ構造検索
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
       endNode{.* , embedding: Null, id: Null} AS target_properties
```

### OpenAI API呼び出しの詳細分析

#### 1. 知識トリプレット抽出 (GPT-3.5-turbo)
**プロンプト**:
```
Some text is provided below. Given the text, extract up to 10 knowledge triplets in the form of (subject, predicate, object). Avoid stopwords.
---------------------
Example:Text: Alice is Bob's mother.Triplets:
(Alice, is mother of, Bob)
Text: Philz is a coffee shop founded in Berkeley in 1982.
Triplets:
(Philz, is, coffee shop)
(Philz, founded in, Berkeley)
(Philz, founded in, 1982)
---------------------
Text: Taro works at ACME. ACME is based in Tokyo.
Triplets:
```

**API設定**:
- Model: `gpt-3.5-turbo`
- Temperature: `0.1`
- Stream: `False`

**レスポンス時間**: 1.358秒 (16:09:23.644 - 16:09:25.002)

#### 2. キーワード生成 (GPT-3.5-turbo)
**プロンプト**:
```
Given some initial query, generate synonyms or related keywords up to 10 in total, considering possible cases of capitalization, pluralization, common expressions, etc.
Provide all synonyms/keywords separated by '^' symbols: 'keyword1^keyword2^...'
Note, result should be in one-line, separated by '^' symbols.----
QUERY: Where does ACME locate?
----
KEYWORDS:
```

**API設定**:
- Model: `gpt-3.5-turbo`
- Temperature: `0.1`
- Stream: `False`

#### 3. 最終回答生成 (GPT-3.5-turbo)
**システムプロンプト**:
```
You are an expert Q&A system that is trusted around the world.
Always answer the query using the provided context information, and not prior knowledge.
Some rules to follow:
1. Never directly reference the given context in your answer.
2. Avoid statements like 'Based on the context, ...' or 'The context information ...' or anything along those lines.
```

**ユーザープロンプト**:
```
Context information is below.
---------------------
Here are some facts extracted from the provided text:

Taro -> Works at -> Acme
Acme -> Is based in -> Tokyo

Taro works at ACME. ACME is based in Tokyo.

[質問内容]
Where does ACME locate?
```

#### 4. エンベディング生成 (text-embedding-ada-002)

**入力1**: `"Taro works at ACME. ACME is based in Tokyo."`
- モデル: `text-embedding-ada-002`
- エンコーディング: `base64`
- 次元数: `1536`

**入力2**: `"Where does ACME locate?"`
- モデル: `text-embedding-ada-002`
- エンコーディング: `base64`
- 次元数: `1536`

**レスポンス時間**: 0.819秒 (16:09:25.040 - 16:09:25.859)

### エラーハンドリング
- **非同期処理エラー**: `RuntimeError: Event loop is closed` (一時的)
- **リトライメカニズム**: 自動的にリトライ実行
- **最終結果**: エラーにも関わらず正常に回答生成

### データフロー
```
入力テキスト → チャンク分割 → トリプレット抽出 → グラフ構築 → 
クエリ受信 → エンベディング検索 → グラフ検索 → 回答生成
```

### 生成されたトリプレットの詳細

#### 抽出された知識トリプレット
1. **(Taro, Works at, Acme)**
   - 主語: Taro (人物)
   - 述語: Works at (関係)
   - 目的語: Acme (会社)

2. **(Acme, Is based in, Tokyo)**
   - 主語: Acme (会社)
   - 述語: Is based in (関係)
   - 目的語: Tokyo (場所)

#### トリプレットソースID
- **triplet_source_id**: `9c0e068c-0007-434c-99d3-b2f5b19e6ec7`
- 同じソースIDで複数のトリプレットが関連付けられている

### Neo4jデータ構造

#### ノード構造
```cypher
// エンティティノード
(:__Entity__ {
  id: "Taro",
  name: "Taro",
  triplet_source_id: "9c0e068c-0007-434c-99d3-b2f5b19e6ec7"
})

(:__Entity__ {
  id: "Acme", 
  name: "Acme",
  triplet_source_id: "9c0e068c-0007-434c-99d3-b2f5b19e6ec7"
})

(:__Entity__ {
  id: "Tokyo",
  name: "Tokyo", 
  triplet_source_id: "9c0e068c-0007-434c-99d3-b2f5b19e6ec7"
})

// テキストチャンクノード
(:__Node__:Chunk {
  id: "0b5b9981-da03-43af-a420-4a4cb42fe7ea",
  text: "Taro works at ACME. ACME is based in Tokyo.",
  embedding: [ベクトルデータ],
  _node_type: "text",
  _node_content: "Taro works at ACME. ACME is based in Tokyo."
})
```

#### リレーションシップ構造
```cypher
// 知識トリプレット関係
(Taro)-[:`Works at` {triplet_source_id: "9c0e068c-0007-434c-99d3-b2f5b19e6ec7"}]->(Acme)
(Acme)-[:`Is based in` {triplet_source_id: "9c0e068c-0007-434c-99d3-b2f5b19e6ec7"}]->(Tokyo)

// ソース関係
(9c0e068c-0007-434c-99d3-b2f5b19e6ec7)-[:SOURCE {triplet_source_id: "9c0e068c-0007-434c-99d3-b2f5b19e6ec7"}]->(0b5b9981-da03-43af-a420-4a4cb42fe7ea)
```

### APIレスポンス詳細

#### OpenAI Chat Completions レスポンス
- **Organization**: `ehime-university-computer-science-lab`
- **Project**: `proj_J2ozYACnCAyF9swBaMOIo4Ft`
- **Processing Time**: 332ms (トリプレット抽出), 47ms (エンベディング)
- **Rate Limits**: 
  - リクエスト制限: 10,000/日
  - トークン制限: 200,000/日
  - 残りリクエスト: 9,999
  - 残りトークン: 199,880

#### ベクトルインデックス
- **インデックス名**: `entity`
- **対象**: `(__Entity__)`
- **プロパティ**: `embedding`
- **次元数**: 1536次元
- **エンコーディング**: Base64

### パフォーマンス最適化

#### クエリ最適化
1. **制約の活用**: ユニーク制約による高速検索
2. **ベクトルインデックス**: 類似度検索の高速化
3. **APOC拡張**: 効率的なメタデータ取得
4. **バッチ処理**: UNWINDによる一括データ処理

#### メモリ効率
- **接続プール**: Neo4j接続の再利用
- **トランザクション管理**: 適切なコミット/ロールバック
- **エンベディング除外**: 検索結果からの重いデータ除外

## 結果評価

### 成功指標
✅ **正確性**: 正しい回答 "ACME is located in Tokyo." を生成  
✅ **完全性**: すべての処理ステップが正常完了  
✅ **効率性**: 8.6秒での高速処理  
✅ **信頼性**: エラー発生時もリトライで正常処理  

### 改善点
- 初期化時間の短縮 (55ms → 目標30ms以下)
- エラー発生率の削減 (現在は一時的な非同期エラー)
- メモリ使用量の最適化

## 結論

`engine.query("Where does ACME locate?")`の実行は、LlamaIndex + Neo4jの統合システムが正常に動作することを実証しました。自然言語クエリから構造化された知識グラフを検索し、適切な回答を生成する一連の処理が8.6秒で完了しています。

このシステムは、ドキュメントの知識抽出、グラフベースの知識表現、および自然言語での知識検索という、現代のAIシステムの重要な要素を統合した実用的なソリューションとして機能しています。

---

**レポート作成日**: 2025年9月29日  
**分析対象**: `cypher_template_demo.log`  
**分析者**: AI Assistant
