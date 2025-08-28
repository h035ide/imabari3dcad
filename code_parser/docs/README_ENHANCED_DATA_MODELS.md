# Enhanced Data Models for RAG-Optimized Code Parser

## 概要

このモジュールは、`RAG_IMPROVEMENT_PLAN.md`に基づいて実装された拡張データモデルです。従来の構文解析に加えて、RAG（Retrieval-Augmented Generation）システムに最適化された意味的情報、機能的関係、使用例、エラーハンドリング情報等を提供します。

## 実装したファイル

### 1. `enhanced_data_models.py`
拡張データモデルの中核実装
- `EnhancedNodeType`: 24の新しいノードタイプ（関数ドキュメント、使用例、エラーハンドリング等）
- `EnhancedRelationType`: 20の新しいリレーションタイプ（類似機能、互換性、代替関係等）
- `EnhancedSyntaxNode`: RAG特化フィールドを含む拡張構文ノード
- `EnhancedSyntaxRelation`: 意味的関係を含む拡張構文関係
- 分析結果クラス: `FunctionAnalysis`, `ClassAnalysis`, `ErrorAnalysis`, `PerformanceInfo`

### 2. `enhanced_data_migration.py`
既存Neo4jデータベースの移行機能
- `DataModelMigrator`: 既存データを拡張モデルに移行
- 制約・インデックス作成
- バックアップ・検証機能
- マイグレーション計画の自動生成

### 3. `enhanced_parser_adapter.py`
既存パーサーとの統合アダプター
- 既存の`SyntaxNode`/`SyntaxRelation`を拡張版に変換
- ドキュメントノードの自動生成
- 意味的関係の推論・生成
- 類似性関係の計算

### 4. `test_enhanced_data_models.py`
包括的なテストスイート
- 全てのデータモデルのテスト
- シリアライゼーション/デシリアライゼーションテスト
- 移行機能のテスト
- アダプター機能のテスト

## 主要な拡張機能

### 新しいノードタイプ
```python
# RAG特化ノードタイプ
EnhancedNodeType.FUNCTION_DOC      # 関数の詳細ドキュメント
EnhancedNodeType.USAGE_EXAMPLE     # 使用例・サンプルコード
EnhancedNodeType.ERROR_HANDLING    # エラーハンドリング情報
EnhancedNodeType.PERFORMANCE_INFO  # パフォーマンス特性
EnhancedNodeType.ALTERNATIVE       # 代替実装・代替手法
EnhancedNodeType.BEST_PRACTICE     # ベストプラクティス
```

### 新しいリレーションタイプ
```python
# 意味的・機能的関係
EnhancedRelationType.SIMILAR_FUNCTION     # 類似機能
EnhancedRelationType.COMPATIBLE_INPUT     # 入力互換性
EnhancedRelationType.ALTERNATIVE_TO       # 代替関係
EnhancedRelationType.PERFORMANCE_RELATED  # パフォーマンス関連
EnhancedRelationType.ERROR_RELATED        # エラー関連
```

### RAG特化フィールド
```python
class EnhancedSyntaxNode:
    # 意味的情報
    function_analysis: Optional[FunctionAnalysis]
    semantic_tags: List[str]
    embeddings: Optional[List[float]]
    
    # 品質・信頼性
    quality_score: float
    usage_frequency: int
    source_confidence: float
    
    # メタデータ
    last_updated: Optional[datetime]
    llm_confidence: float
```

## 使用方法

### 1. 基本的な使用例

```python
from enhanced_data_models import (
    EnhancedNodeType, EnhancedSyntaxNode,
    FunctionAnalysis, create_enhanced_node
)
from datetime import datetime

# 拡張ノードの作成
node = create_enhanced_node(
    node_id="func_001",
    node_type=EnhancedNodeType.FUNCTION,
    name="calculate_total",
    text="def calculate_total(items): return sum(items)",
    quality_score=0.9,
    semantic_tags=["calculation", "utility"]
)

# 関数分析の追加
node.function_analysis = FunctionAnalysis(
    purpose="リストの合計値を計算",
    input_spec={"items": {"type": "List[float]", "required": True}},
    output_spec={"type": "float", "description": "合計値"},
    usage_examples=["total = calculate_total([1, 2, 3])"],
    error_handling=["TypeError: 数値以外が含まれる場合"],
    performance={"time_complexity": "O(n)"},
    limitations=["非常に大きなリストでは精度の問題あり"],
    alternatives=["numpy.sum", "math.fsum"],
    related_functions=["calculate_average"],
    security_considerations=["入力検証なし"],
    test_cases=["正常ケース", "空リスト", "負の値"],
    complexity_metrics={"cyclomatic": 1},
    dependencies=[],
    version_compatibility={"python": ">=3.6"}
)

# Neo4j保存用の辞書変換
node_dict = node.to_dict()
```

### 2. 既存データの移行

```python
from enhanced_data_migration import DataModelMigrator

# 移行器の初期化
migrator = DataModelMigrator(
    uri="bolt://localhost:7687",
    user="neo4j", 
    password="your_password"
)

# 移行状況の確認
status = migrator.check_migration_status()
print("移行必要性:", status["needs_migration"])

# バックアップ作成
backup_result = migrator.backup_database()
print("バックアップ:", backup_result["backup_path"])

# マイグレーション実行（ドライラン）
result = migrator.execute_migration(dry_run=True)
print("計画:", result["plan"])

# 実際のマイグレーション実行
result = migrator.execute_migration(dry_run=False)

# 検証
validation = migrator.validate_migration()
print("検証結果:", validation["is_valid"])

migrator.close()
```

### 3. パーサーアダプターの使用

```python
from enhanced_parser_adapter import EnhancedParserAdapter
from treesitter_neo4j_advanced import TreeSitterNeo4jAnalyzer

# 既存パーサーの初期化
base_analyzer = TreeSitterNeo4jAnalyzer()

# アダプターの作成
adapter = EnhancedParserAdapter(base_analyzer)

# 既存ノードの変換（例）
legacy_nodes = []  # 既存システムから取得
legacy_relations = []  # 既存システムから取得

enhanced_nodes, enhanced_relations = adapter.enhance_existing_data(
    legacy_nodes, legacy_relations
)

# ドキュメントノードの生成
doc_nodes = adapter.create_enhanced_documentation_nodes(enhanced_nodes)

# 意味的関係の生成
semantic_relations = adapter.create_enhanced_relations(
    enhanced_nodes + doc_nodes
)

# 類似性関係の生成
similarity_relations = adapter.generate_similarity_relations(enhanced_nodes)
```

### 4. テストの実行

```bash
# テストスイートの実行
cd code_parser
python -m pytest test_enhanced_data_models.py -v

# または単体テストとして
python test_enhanced_data_models.py
```

## マイグレーション手順

### Step 1: 事前準備
```bash
# バックアップの作成
python -c "
from enhanced_data_migration import DataModelMigrator
migrator = DataModelMigrator('bolt://localhost:7687', 'neo4j', 'password')
result = migrator.backup_database()
print(f'バックアップ完了: {result[\"backup_path\"]}')
migrator.close()
"
```

### Step 2: ドライラン実行
```bash
python -c "
from enhanced_data_migration import DataModelMigrator
migrator = DataModelMigrator('bolt://localhost:7687', 'neo4j', 'password')
result = migrator.execute_migration(dry_run=True)
print('計画:', result['plan'])
migrator.close()
"
```

### Step 3: 実際のマイグレーション
```bash
python -c "
from enhanced_data_migration import DataModelMigrator
migrator = DataModelMigrator('bolt://localhost:7687', 'neo4j', 'password')
result = migrator.execute_migration(dry_run=False)
validation = migrator.validate_migration()
print('マイグレーション完了:', validation['is_valid'])
migrator.close()
"
```

## ベストプラクティス

### 1. ノード作成時の推奨事項
- `quality_score`を適切に設定（0.0-1.0）
- `semantic_tags`で検索性を向上
- `source_confidence`で信頼度を管理
- `last_updated`を設定してデータの新しさを追跡

### 2. 関係作成時の推奨事項
- `confidence_score`で関係の確実性を表現
- `discovery_method`で発見手法を記録
- 意味的類似度と機能的類似度を区別

### 3. 分析情報の品質向上
- 具体的で実行可能な使用例を提供
- エラーハンドリングは実際のコード例を含める
- パフォーマンス情報は計測可能なメトリクスを記録

## 注意事項

### 互換性
- 既存の`NodeType`/`RelationType`との後方互換性を維持
- 既存データは自動的に拡張データモデルに移行可能

### パフォーマンス
- 大量のノード・リレーションでは段階的移行を推奨
- インデックス作成により検索パフォーマンスが向上

### データ整合性
- マイグレーション前に必ずバックアップを作成
- 検証機能で整合性を確認

## 今後の拡張予定

1. **ベクトル検索の統合** (Phase 2)
   - ChromaDBとの連携
   - 自動ベクトル埋め込み生成

2. **高度なLLM分析** (Phase 2)
   - 分析品質の向上
   - 多様なLLMモデルの活用

3. **使用例収集の自動化** (Phase 3)
   - テストファイルからの自動抽出
   - ドキュメント文字列の解析

この実装により、RAG_IMPROVEMENT_PLAN.mdの「1. データモデルの拡張」が完全に実装されました。次のフェーズでベクトル検索とLLM分析の強化を進めることができます。