# Tree-sitter Neo4j統合システム

Tree-sitterの構文解析結果をNeo4jにグラフ形式で格納し、LLMによるコード理解強化を行う統合システムです。

## 概要

このシステムは以下の機能を提供します：

- **Tree-sitter構文解析**: Pythonコードの詳細な構文解析
- **Neo4jグラフ格納**: 構文要素をグラフデータベースに格納
- **LLM統合**: OpenAI APIを使用したコード理解の強化
- **複雑性分析**: 循環複雑度や認知的複雑度の計算
- **クエリエンジン**: グラフデータの高度な検索・分析

## システム構成

```
Tree-sitter解析 → 構造化データ変換 → LLM処理 → Neo4j格納 → クエリ分析
```

### 主要コンポーネント

1. **TreeSitterNeo4jAdvancedBuilder** (`treesitter_neo4j_advanced.py`)
   - メインの統合システム
   - Tree-sitter解析とNeo4j格納を統合
   - LLMによるコード理解強化

2. **Neo4jQueryEngine** (`neo4j_query_engine.py`)
   - グラフデータの検索・分析
   - 複雑性分析、依存関係追跡
   - コードメトリクス取得

3. **テストシステム** (`test_treesitter_neo4j_integration.py`)
   - 統合テスト
   - 各機能の動作確認

## インストール

### 必要な依存関係

```bash
pip install tree-sitter-python neo4j openai
```

### 環境変数の設定

```bash
# Neo4j接続情報
export NEO4J_URI="neo4j://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your_password"

# OpenAI API（LLM機能を使用する場合）
export OPENAI_API_KEY="your_openai_api_key"
```

## 使用方法

### 1. 基本的な使用

```python
from treesitter_neo4j_advanced import TreeSitterNeo4jAdvancedBuilder

# ビルダーの作成
builder = TreeSitterNeo4jAdvancedBuilder(
    neo4j_uri="neo4j://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password",
    database_name="treesitter_graph",
    enable_llm=True
)

# ファイル解析とNeo4j格納
builder.analyze_file("./evoship/create_test.py")
```

### 2. クエリエンジンの使用

```python
from neo4j_query_engine import Neo4jQueryEngine

# クエリエンジンの作成
query_engine = Neo4jQueryEngine(
    neo4j_uri="neo4j://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password",
    database_name="treesitter_graph"
)

# 高複雑性関数の検索
complex_functions = query_engine.find_functions_by_complexity(min_complexity=5.0)

# 関数の依存関係を検索
dependencies = query_engine.find_function_dependencies("function_name")

# コードメトリクスの取得
metrics = query_engine.find_code_metrics()
```

### 3. テストの実行

```bash
python test_treesitter_neo4j_integration.py
```

## 機能詳細

### 構文要素の抽出

以下の構文要素を自動的に抽出します：

- **ノードタイプ**:
  - `Module`: モジュール全体
  - `Class`: クラス定義
  - `Function`: 関数定義
  - `Variable`: 変数
  - `Parameter`: パラメータ
  - `Import`: インポート文
  - `Comment`: コメント
  - `Call`: 関数呼び出し
  - `Assignment`: 代入文
  - `Attribute`: 属性アクセス

- **リレーションタイプ**:
  - `CONTAINS`: 包含関係
  - `CALLS`: 関数呼び出し
  - `USES`: 変数使用
  - `IMPORTS`: インポート関係
  - `HAS_PARAMETER`: パラメータ所有
  - `ASSIGNS`: 代入関係
  - `HAS_ATTRIBUTE`: 属性所有

### 複雑性分析

- **循環複雑度**: 制御フローの複雑性を測定
- **認知的複雑度**: コードの理解しやすさを測定
- **ファイルメトリクス**: 行数、関数数、クラス数などの統計

### LLM統合

OpenAI APIを使用して以下の分析を提供：

- 関数の目的と機能の説明
- クラスの設計パターン分析
- コードの改善提案
- セキュリティ上の考慮事項

### クエリ機能

以下の高度なクエリ機能を提供：

- 複雑性による関数検索
- 依存関係の追跡
- コードパターンの検出
- メトリクス統計の取得
- グラフデータのエクスポート

## Neo4jクエリ例

### 高複雑性関数の検索

```cypher
MATCH (f:Function)
WHERE f.complexity_score >= 5
RETURN f.name, f.complexity_score, f.file_path
ORDER BY f.complexity_score DESC
```

### 関数の依存関係

```cypher
MATCH (caller:Function)-[:CALLS]->(called:Function)
WHERE caller.name = "main"
RETURN caller.name, called.name
```

### クラスとメソッドの関係

```cypher
MATCH (c:Class)-[:CONTAINS]->(f:Function)
RETURN c.name, collect(f.name) as methods
```

### LLM分析結果の取得

```cypher
MATCH (n)
WHERE n.llm_analysis IS NOT NULL
RETURN n.name, n.llm_analysis
```

## 設定オプション

### TreeSitterNeo4jAdvancedBuilder

```python
builder = TreeSitterNeo4jAdvancedBuilder(
    neo4j_uri="neo4j://localhost:7687",      # Neo4j URI
    neo4j_user="neo4j",                      # ユーザー名
    neo4j_password="password",               # パスワード
    database_name="treesitter_graph",        # データベース名
    enable_llm=True                          # LLM機能の有効/無効
)
```

### Neo4jQueryEngine

```python
query_engine = Neo4jQueryEngine(
    neo4j_uri="neo4j://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password",
    database_name="treesitter_graph"
)
```

## トラブルシューティング

### よくある問題

1. **Neo4j接続エラー**
   - Neo4jサーバーが起動していることを確認
   - 接続情報（URI、ユーザー名、パスワード）を確認

2. **LLM機能エラー**
   - OpenAI APIキーが設定されていることを確認
   - APIキーの有効性を確認

3. **Tree-sitter解析エラー**
   - Pythonファイルの構文が正しいことを確認
   - ファイルのエンコーディングがUTF-8であることを確認

### ログの確認

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## パフォーマンス最適化

### 大規模プロジェクトの処理

1. **バッチ処理**: ファイルを分割して処理
2. **LLM制限**: 重要な関数のみLLM分析を適用
3. **インデックス**: Neo4jにインデックスを作成

### メモリ使用量の最適化

1. **ノード数の制限**: 重要度の低いノードを除外
2. **テキストの切り詰め**: 長いコードテキストを制限
3. **キャッシュの活用**: 重複解析を回避

## 拡張機能

### カスタムノードタイプの追加

```python
class CustomNodeType(Enum):
    CUSTOM_TYPE = "CustomType"

# ノードタイプ判定ロジックを拡張
def determine_node_type(self, node: Node) -> NodeType:
    if node.type == "custom_pattern":
        return CustomNodeType.CUSTOM_TYPE
    # ... 既存のロジック
```

### カスタムリレーションの追加

```python
class CustomRelationType(Enum):
    CUSTOM_RELATION = "CUSTOM_RELATION"

# リレーション抽出ロジックを拡張
def extract_custom_relationships(self, parent, child, parent_id, child_id):
    if custom_condition:
        self.syntax_relations.append(SyntaxRelation(
            source_id=parent_id,
            target_id=child_id,
            relation_type=CustomRelationType.CUSTOM_RELATION,
            properties={}
        ))
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

バグ報告や機能要望は、GitHubのIssueでお知らせください。
プルリクエストも歓迎します。

## 更新履歴

- **v1.0.0**: 初期リリース
  - Tree-sitter統合
  - Neo4j格納機能
  - LLM統合
  - クエリエンジン
  - テストシステム 