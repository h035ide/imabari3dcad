"""
Enhanced Data Models Test Suite

拡張データモデルの包括的なテストスイート
"""

import unittest
import json
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from code_parser.enhanced_data_models import (
    EnhancedNodeType, EnhancedRelationType,
    EnhancedSyntaxNode, EnhancedSyntaxRelation,
    FunctionAnalysis, ClassAnalysis, ErrorAnalysis, PerformanceInfo,
    create_enhanced_node, create_enhanced_relation
)

from code_parser.enhanced_parser_adapter import EnhancedParserAdapter
from code_parser.enhanced_data_migration import DataModelMigrator


class TestEnhancedDataModels(unittest.TestCase):
    """拡張データモデルのテスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.sample_function_analysis = FunctionAnalysis(
            purpose="サンプル関数の処理",
            input_spec={"param1": {"type": "str", "required": True}},
            output_spec={"type": "dict", "description": "処理結果"},
            usage_examples=["result = sample_function('test')"],
            error_handling=["ValueError", "TypeError"],
            performance={"time_complexity": "O(n)"},
            limitations=["大きなデータには不適切"],
            alternatives=["alternative_function"],
            related_functions=["helper_function"],
            security_considerations=["入力検証が必要"],
            test_cases=["test_normal_case", "test_edge_case"],
            complexity_metrics={"cyclomatic": 3},
            dependencies=["requests", "json"],
            version_compatibility={"python": ">=3.8"}
        )
    
    def test_enhanced_node_type_enum(self):
        """拡張ノードタイプの列挙テスト"""
        # 基本ノードタイプの存在確認
        self.assertIn(EnhancedNodeType.FUNCTION, EnhancedNodeType)
        self.assertIn(EnhancedNodeType.CLASS, EnhancedNodeType)
        
        # 新規追加ノードタイプの存在確認
        self.assertIn(EnhancedNodeType.FUNCTION_DOC, EnhancedNodeType)
        self.assertIn(EnhancedNodeType.USAGE_EXAMPLE, EnhancedNodeType)
        self.assertIn(EnhancedNodeType.ERROR_HANDLING, EnhancedNodeType)
        self.assertIn(EnhancedNodeType.PERFORMANCE_INFO, EnhancedNodeType)
        
        # 値の確認
        self.assertEqual(EnhancedNodeType.FUNCTION_DOC.value, "FunctionDoc")
        self.assertEqual(EnhancedNodeType.USAGE_EXAMPLE.value, "UsageExample")
    
    def test_enhanced_relation_type_enum(self):
        """拡張リレーションタイプの列挙テスト"""
        # 基本リレーションタイプの存在確認
        self.assertIn(EnhancedRelationType.CALLS, EnhancedRelationType)
        self.assertIn(EnhancedRelationType.USES, EnhancedRelationType)
        
        # 新規追加リレーションタイプの存在確認
        self.assertIn(EnhancedRelationType.SIMILAR_FUNCTION, EnhancedRelationType)
        self.assertIn(EnhancedRelationType.ALTERNATIVE_TO, EnhancedRelationType)
        self.assertIn(EnhancedRelationType.PERFORMANCE_RELATED, EnhancedRelationType)
        
        # 値の確認
        self.assertEqual(EnhancedRelationType.SIMILAR_FUNCTION.value, "SIMILAR_FUNCTION")
        self.assertEqual(EnhancedRelationType.ALTERNATIVE_TO.value, "ALTERNATIVE_TO")
    
    def test_function_analysis_creation(self):
        """FunctionAnalysisの作成テスト"""
        analysis = self.sample_function_analysis
        
        self.assertEqual(analysis.purpose, "サンプル関数の処理")
        self.assertIn("param1", analysis.input_spec)
        self.assertEqual(analysis.input_spec["param1"]["type"], "str")
        self.assertTrue(analysis.input_spec["param1"]["required"])
        
        # to_dict メソッドのテスト
        analysis_dict = analysis.to_dict()
        self.assertIsInstance(analysis_dict, dict)
        self.assertEqual(analysis_dict["purpose"], "サンプル関数の処理")
        self.assertIn("input_spec", analysis_dict)
    
    def test_enhanced_syntax_node_creation(self):
        """拡張構文ノードの作成テスト"""
        node = EnhancedSyntaxNode(
            node_id="test_node_1",
            node_type=EnhancedNodeType.FUNCTION,
            name="test_function",
            text="def test_function(param1): pass",
            start_byte=0,
            end_byte=30,
            line_start=1,
            line_end=1,
            properties={"language": "python"},
            function_analysis=self.sample_function_analysis,
            semantic_tags=["test", "function"],
            quality_score=0.8
        )
        
        self.assertEqual(node.node_id, "test_node_1")
        self.assertEqual(node.node_type, EnhancedNodeType.FUNCTION)
        self.assertEqual(node.name, "test_function")
        self.assertIsNotNone(node.function_analysis)
        self.assertEqual(len(node.semantic_tags), 2)
        self.assertEqual(node.quality_score, 0.8)
    
    def test_enhanced_syntax_node_serialization(self):
        """拡張構文ノードのシリアライゼーションテスト"""
        node = EnhancedSyntaxNode(
            node_id="test_node_2",
            node_type=EnhancedNodeType.FUNCTION,
            name="test_function",
            text="def test_function(): pass",
            start_byte=0,
            end_byte=25,
            line_start=1,
            line_end=1,
            properties={"language": "python"},
            function_analysis=self.sample_function_analysis,
            semantic_tags=["test"],
            last_updated=datetime.now()
        )
        
        # 辞書への変換
        node_dict = node.to_dict()
        self.assertIsInstance(node_dict, dict)
        self.assertEqual(node_dict["node_id"], "test_node_2")
        self.assertEqual(node_dict["node_type"], "Function")
        
        # function_analysisがJSON文字列として保存されることを確認
        self.assertIn("function_analysis", node_dict)
        function_analysis_data = json.loads(node_dict["function_analysis"])
        self.assertEqual(function_analysis_data["purpose"], "サンプル関数の処理")
        
        # 復元テスト
        restored_node = EnhancedSyntaxNode.from_dict(node_dict)
        self.assertEqual(restored_node.node_id, node.node_id)
        self.assertEqual(restored_node.node_type, node.node_type)
        self.assertIsNotNone(restored_node.function_analysis)
        self.assertEqual(restored_node.function_analysis.purpose, node.function_analysis.purpose)
    
    def test_enhanced_syntax_relation_creation(self):
        """拡張構文関係の作成テスト"""
        relation = EnhancedSyntaxRelation(
            source_id="node_1",
            target_id="node_2",
            relation_type=EnhancedRelationType.SIMILAR_FUNCTION,
            confidence_score=0.9,
            semantic_similarity=0.8,
            functional_similarity=0.7,
            discovery_method="llm_analysis"
        )
        
        self.assertEqual(relation.source_id, "node_1")
        self.assertEqual(relation.target_id, "node_2")
        self.assertEqual(relation.relation_type, EnhancedRelationType.SIMILAR_FUNCTION)
        self.assertEqual(relation.confidence_score, 0.9)
        self.assertEqual(relation.semantic_similarity, 0.8)
        self.assertEqual(relation.discovery_method, "llm_analysis")
    
    def test_enhanced_syntax_relation_serialization(self):
        """拡張構文関係のシリアライゼーションテスト"""
        relation = EnhancedSyntaxRelation(
            source_id="node_1",
            target_id="node_2",
            relation_type=EnhancedRelationType.ALTERNATIVE_TO,
            properties={"strength": "high"},
            confidence_score=0.95,
            last_verified=datetime.now()
        )
        
        # 辞書への変換
        relation_dict = relation.to_dict()
        self.assertIsInstance(relation_dict, dict)
        self.assertEqual(relation_dict["source_id"], "node_1")
        self.assertEqual(relation_dict["relation_type"], "ALTERNATIVE_TO")
        
        # propertiesがJSON文字列として保存されることを確認
        properties_data = json.loads(relation_dict["properties"])
        self.assertEqual(properties_data["strength"], "high")
        
        # 復元テスト
        restored_relation = EnhancedSyntaxRelation.from_dict(relation_dict)
        self.assertEqual(restored_relation.source_id, relation.source_id)
        self.assertEqual(restored_relation.relation_type, relation.relation_type)
        self.assertEqual(restored_relation.properties["strength"], "high")
    
    def test_create_enhanced_node_helper(self):
        """create_enhanced_node ヘルパー関数のテスト"""
        node = create_enhanced_node(
            node_id="helper_test",
            node_type=EnhancedNodeType.USAGE_EXAMPLE,
            name="example_1",
            text="# Usage example",
            quality_score=0.9,
            semantic_tags=["example", "documentation"]
        )
        
        self.assertEqual(node.node_id, "helper_test")
        self.assertEqual(node.node_type, EnhancedNodeType.USAGE_EXAMPLE)
        self.assertEqual(node.quality_score, 0.9)
        self.assertEqual(len(node.semantic_tags), 2)
    
    def test_create_enhanced_relation_helper(self):
        """create_enhanced_relation ヘルパー関数のテスト"""
        relation = create_enhanced_relation(
            source_id="func_1",
            target_id="func_2",
            relation_type=EnhancedRelationType.PERFORMANCE_RELATED,
            confidence_score=0.8
        )
        
        self.assertEqual(relation.source_id, "func_1")
        self.assertEqual(relation.target_id, "func_2")
        self.assertEqual(relation.relation_type, EnhancedRelationType.PERFORMANCE_RELATED)
        self.assertEqual(relation.confidence_score, 0.8)


class TestEnhancedParserAdapter(unittest.TestCase):
    """拡張パーサーアダプターのテスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.adapter = EnhancedParserAdapter()
        
        # モックの Legacy SyntaxNode
        from code_parser.treesitter_neo4j_advanced import NodeType, SyntaxNode
        self.mock_legacy_node = SyntaxNode(
            node_id="legacy_1",
            node_type=NodeType.FUNCTION,
            name="legacy_function",
            text="def legacy_function(): pass",
            start_byte=0,
            end_byte=27,
            line_start=1,
            line_end=1,
            properties={"parameters": ["param1", "param2"]},
            complexity_score=2.5
        )
    
    def test_node_type_mapping(self):
        """ノードタイプマッピングのテスト"""
        from code_parser.treesitter_neo4j_advanced import NodeType
        
        mapping = self.adapter.node_type_mapping
        
        # 基本マッピングの確認
        self.assertEqual(mapping[NodeType.FUNCTION], EnhancedNodeType.FUNCTION)
        self.assertEqual(mapping[NodeType.CLASS], EnhancedNodeType.CLASS)
        self.assertEqual(mapping[NodeType.VARIABLE], EnhancedNodeType.VARIABLE)
    
    def test_relation_type_mapping(self):
        """リレーションタイプマッピングのテスト"""
        from code_parser.treesitter_neo4j_advanced import RelationType
        
        mapping = self.adapter.relation_type_mapping
        
        # 基本マッピングの確認
        self.assertEqual(mapping[RelationType.CALLS], EnhancedRelationType.CALLS)
        self.assertEqual(mapping[RelationType.USES], EnhancedRelationType.USES)
        self.assertEqual(mapping[RelationType.CONTAINS], EnhancedRelationType.CONTAINS)
    
    def test_convert_syntax_node(self):
        """構文ノード変換のテスト"""
        enhanced_node = self.adapter.convert_syntax_node(self.mock_legacy_node)
        
        self.assertEqual(enhanced_node.node_id, "legacy_1")
        self.assertEqual(enhanced_node.node_type, EnhancedNodeType.FUNCTION)
        self.assertEqual(enhanced_node.name, "legacy_function")
        self.assertEqual(enhanced_node.complexity_score, 2.5)
        self.assertIsNotNone(enhanced_node.last_updated)
        self.assertEqual(enhanced_node.source_confidence, 1.0)
        
        # 関数分析が生成されることを確認
        self.assertIsNotNone(enhanced_node.function_analysis)
        self.assertIn("param1", enhanced_node.function_analysis.input_spec)
    
    def test_convert_syntax_relation(self):
        """構文関係変換のテスト"""
        from code_parser.treesitter_neo4j_advanced import RelationType, SyntaxRelation
        
        mock_legacy_relation = SyntaxRelation(
            source_id="node_1",
            target_id="node_2",
            relation_type=RelationType.CALLS,
            properties={"frequency": 5}
        )
        
        enhanced_relation = self.adapter.convert_syntax_relation(mock_legacy_relation)
        
        self.assertEqual(enhanced_relation.source_id, "node_1")
        self.assertEqual(enhanced_relation.target_id, "node_2")
        self.assertEqual(enhanced_relation.relation_type, EnhancedRelationType.CALLS)
        self.assertEqual(enhanced_relation.confidence_score, 1.0)
        self.assertEqual(enhanced_relation.discovery_method, "static_analysis")
        self.assertEqual(enhanced_relation.properties["frequency"], 5)
    
    def test_create_enhanced_documentation_nodes(self):
        """拡張ドキュメントノード生成のテスト"""
        # テスト用の関数ノードを作成
        function_node = create_enhanced_node(
            node_id="test_func",
            node_type=EnhancedNodeType.FUNCTION,
            name="test_function",
            text="def test_function(): pass"
        )
        
        # 関数分析を追加
        function_node.function_analysis = FunctionAnalysis(
            purpose="テスト関数",
            input_spec={},
            output_spec={},
            usage_examples=["test_function()", "result = test_function()"],
            error_handling=[],
            performance={},
            limitations=[],
            alternatives=[],
            related_functions=[],
            security_considerations=[],
            test_cases=[],
            complexity_metrics={},
            dependencies=[],
            version_compatibility={}
        )
        
        doc_nodes = self.adapter.create_enhanced_documentation_nodes([function_node])
        
        # ドキュメントノードと使用例ノードが生成されることを確認
        doc_node_types = [node.node_type for node in doc_nodes]
        self.assertIn(EnhancedNodeType.FUNCTION_DOC, doc_node_types)
        self.assertIn(EnhancedNodeType.USAGE_EXAMPLE, doc_node_types)
        
        # 使用例ノードが2つ生成されることを確認
        example_nodes = [node for node in doc_nodes if node.node_type == EnhancedNodeType.USAGE_EXAMPLE]
        self.assertEqual(len(example_nodes), 2)
    
    def test_name_similarity_calculation(self):
        """名前類似性計算のテスト"""
        # 完全一致
        self.assertEqual(self.adapter._calculate_name_similarity("test", "test"), 1.0)
        
        # 部分一致
        similarity = self.adapter._calculate_name_similarity("test_function", "test_method")
        self.assertGreater(similarity, 0)
        self.assertLess(similarity, 1.0)
        
        # 完全不一致
        similarity = self.adapter._calculate_name_similarity("abc", "xyz")
        self.assertEqual(similarity, 0.0)


class TestDataModelMigrator(unittest.TestCase):
    """データモデル移行機能のテスト"""
    
    def setUp(self):
        """テストセットアップ"""
        # Neo4jドライバーのモック
        self.mock_driver = MagicMock()
        self.mock_session = MagicMock()
        self.mock_driver.session.return_value.__enter__.return_value = self.mock_session
        
        with patch('code_parser.enhanced_data_migration.GraphDatabase.driver') as mock_driver_class:
            mock_driver_class.return_value = self.mock_driver
            self.migrator = DataModelMigrator("bolt://localhost:7687", "neo4j", "password")
    
    def test_migration_status_check(self):
        """マイグレーション状況チェックのテスト"""
        # モックデータの設定
        self.mock_session.run.side_effect = [
            [{"labels": ["Function", "Node"]}],  # 既存ノードタイプ
            [{"relation_type": "CALLS"}, {"relation_type": "USES"}],  # 既存リレーションタイプ
            [{"prop": "node_id"}, {"prop": "name"}, {"prop": "text"}]  # 既存プロパティ
        ]
        
        status = self.migrator.check_migration_status()
        
        self.assertIn("existing_node_types", status)
        self.assertIn("existing_relation_types", status)
        self.assertIn("needs_migration", status)
        self.assertIn("migration_plan", status)
        
        # 新しいノードタイプが必要なことを確認
        self.assertTrue(status["needs_migration"]["node_types"])
    
    def test_migration_plan_creation(self):
        """マイグレーション計画作成のテスト"""
        needs_migration = {
            "node_types": True,
            "relation_types": True,
            "properties": True,
            "constraints": True,
            "indexes": True
        }
        
        plan = self.migrator._create_migration_plan(needs_migration)
        
        # 計画にすべてのステップが含まれることを確認
        step_names = [step["step"] for step in plan]
        expected_steps = [
            "create_constraints",
            "create_indexes", 
            "add_enhanced_properties",
            "migrate_node_types",
            "migrate_relation_types"
        ]
        
        for expected_step in expected_steps:
            self.assertIn(expected_step, step_names)
        
        # 優先度順にソートされていることを確認
        priorities = [step["priority"] for step in plan]
        self.assertEqual(priorities, sorted(priorities))
    
    def test_dry_run_execution(self):
        """ドライラン実行のテスト"""
        # マイグレーション状況のモック
        self.mock_session.run.side_effect = [
            [],  # 既存ノードタイプ（空）
            [],  # 既存リレーションタイプ（空）
            []   # 既存プロパティ（空）
        ]
        
        result = self.migrator.execute_migration(dry_run=True)
        
        self.assertTrue(result["dry_run"])
        self.assertIn("results", result)
        self.assertIn("errors", result)
        
        # ドライランでは実際の変更が行われないことを確認
        for result_item in result["results"]:
            self.assertEqual(result_item["status"], "dry_run")
    
    def test_backup_creation(self):
        """バックアップ作成のテスト"""
        # モックデータの設定
        mock_nodes = [
            {"n": {"node_id": "1", "name": "test"}, "labels": ["Function"], "internal_id": 1}
        ]
        mock_relations = [
            {"source_id": "1", "target_id": "2", "relation_type": "CALLS", "props": {}}
        ]
        
        self.mock_session.run.side_effect = [mock_nodes, mock_relations]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            result = self.migrator.backup_database(tmp_path)
            
            self.assertTrue(result["success"])
            self.assertEqual(result["backup_path"], tmp_path)
            self.assertEqual(result["nodes_count"], 1)
            self.assertEqual(result["relations_count"], 1)
            
            # バックアップファイルの内容確認
            with open(tmp_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            self.assertIn("timestamp", backup_data)
            self.assertIn("nodes", backup_data)
            self.assertIn("relations", backup_data)
            self.assertEqual(len(backup_data["nodes"]), 1)
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_migration_validation(self):
        """マイグレーション検証のテスト"""
        # モック検証結果
        self.mock_session.run.side_effect = [
            [{"missing_required_props": 0}],
            [{"nodes_with_enhanced_props": 10}],
            [{"relations_missing_enhanced_props": 0}],
            [{"type_errors": 0}]
        ]
        
        validation_result = self.migrator.validate_migration()
        
        self.assertIn("is_valid", validation_result)
        self.assertIn("validation_results", validation_result)
        self.assertTrue(validation_result["is_valid"])
        self.assertEqual(validation_result["validation_results"]["missing_required_properties"], 0)


if __name__ == '__main__':
    # テストの実行
    unittest.main(verbosity=2)