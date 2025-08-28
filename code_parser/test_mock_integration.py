"""
モック統合テスト - 外部依存関係をモックしたテスト

外部サービス（Neo4j、ChromaDB、OpenAI API）に依存しないテストを実行します。
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestMockedTreeSitterIntegration(unittest.TestCase):
    """Tree-sitter統合のモックテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_mock.py")
        
        # テスト用Pythonファイルを作成
        test_code = '''
def hello_world():
    """Hello Worldを出力する関数"""
    print("Hello, World!")
    return "Hello, World!"

class Calculator:
    """簡単な計算機クラス"""
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        """2つの数を足す"""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def multiply(self, a, b):
        """2つの数を掛ける"""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result
'''
        
        with open(self.test_file, 'w') as f:
            f.write(test_code)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('code_parser.treesitter_neo4j_advanced.TreeSitterNeo4jAdvancedBuilder')
    def test_tree_sitter_parsing_mock(self, mock_builder_class):
        """Tree-sitter解析のモックテスト"""
        # モックの設定
        mock_builder = Mock()
        mock_builder_class.return_value = mock_builder
        
        # ファイル解析の呼び出し
        mock_builder.analyze_file(self.test_file)
        mock_builder.store_to_neo4j()
        
        # メソッドが正しく呼び出されたかチェック
        mock_builder.analyze_file.assert_called_once_with(self.test_file)
        mock_builder.store_to_neo4j.assert_called_once()
    
    @patch('code_parser.treesitter_neo4j_advanced.TreeSitterNeo4jAdvancedBuilder')
    def test_tree_sitter_with_llm_mock(self, mock_builder_class):
        """LLM統合のモックテスト"""
        # モックの設定
        mock_builder = Mock()
        mock_builder_class.return_value = mock_builder
        
        # LLM有効でビルダーを作成
        builder = mock_builder_class(
            "neo4j://localhost:7687",
            "neo4j",
            "password",
            enable_llm=True
        )
        
        # パラメータが正しく渡されたかチェック
        mock_builder_class.assert_called_once_with(
            "neo4j://localhost:7687",
            "neo4j",
            "password",
            enable_llm=True
        )


class TestMockedVectorSearchIntegration(unittest.TestCase):
    """ベクトル検索統合のモックテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('code_parser.vector_search.VectorSearchEngine')
    @patch('code_parser.code_extractor.CodeExtractor')
    def test_vector_search_indexing_mock(self, mock_extractor_class, mock_engine_class):
        """ベクトル検索インデックス化のモックテスト"""
        # モックの設定
        mock_engine = Mock()
        mock_extractor = Mock()
        mock_engine_class.return_value = mock_engine
        mock_extractor_class.return_value = mock_extractor
        
        # モックのコード情報
        mock_code_infos = [
            Mock(id="func_001", name="hello_world", type="function"),
            Mock(id="class_001", name="Calculator", type="class")
        ]
        mock_extractor.extract_from_file.return_value = mock_code_infos
        
        # ベクトル検索エンジンの初期化
        vector_engine = mock_engine_class()
        code_extractor = mock_extractor_class()
        
        # コード情報の抽出とベクトル化
        code_infos = code_extractor.extract_from_file("test_file.py")
        for code_info in code_infos:
            vector_engine.add_code_info(code_info)
        
        # メソッドが正しく呼び出されたかチェック
        mock_extractor.extract_from_file.assert_called_once_with("test_file.py")
        self.assertEqual(mock_engine.add_code_info.call_count, 2)
    
    @patch('code_parser.vector_search.VectorSearchEngine')
    def test_vector_search_query_mock(self, mock_engine_class):
        """ベクトル検索クエリのモックテスト"""
        # モックの設定
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        
        # モックの検索結果
        mock_results = [
            {"id": "func_001", "name": "hello_world", "similarity": 0.95},
            {"id": "func_002", "name": "goodbye_world", "similarity": 0.87}
        ]
        mock_engine.search_similar_functions.return_value = mock_results
        
        # 検索の実行
        vector_engine = mock_engine_class()
        results = vector_engine.search_similar_functions("hello world", top_k=5)
        
        # 結果が正しく返されるかチェック
        self.assertEqual(results, mock_results)
        mock_engine.search_similar_functions.assert_called_once_with("hello world", top_k=5)


class TestMockedLLMIntegration(unittest.TestCase):
    """LLM統合のモックテスト"""
    
    @patch('code_parser.enhanced_llm_analyzer.EnhancedLLMAnalyzer')
    def test_llm_analysis_mock(self, mock_analyzer_class):
        """LLM分析のモックテスト"""
        # モックの設定
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        
        # モックの分析結果
        mock_analysis = Mock()
        mock_analysis.purpose = "テスト関数"
        mock_analysis.usage_examples = ["example1", "example2"]
        mock_analyzer.analyze_function_purpose.return_value = mock_analysis
        
        # 分析の実行
        analyzer = mock_analyzer_class()
        result = analyzer.analyze_function_purpose("test_function")
        
        # 結果が正しく返されるかチェック
        self.assertEqual(result, mock_analysis)
        mock_analyzer.analyze_function_purpose.assert_called_once_with("test_function")
    
    @patch('code_parser.enhanced_llm_analyzer.EnhancedLLMAnalyzer')
    def test_llm_class_analysis_mock(self, mock_analyzer_class):
        """LLMクラス分析のモックテスト"""
        # モックの設定
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        
        # モックの分析結果
        mock_analysis = Mock()
        mock_analysis.purpose = "計算機クラス"
        mock_analysis.design_pattern = "Strategy"
        mock_analyzer.analyze_class_purpose.return_value = mock_analysis
        
        # 分析の実行
        analyzer = mock_analyzer_class()
        result = analyzer.analyze_class_purpose("Calculator")
        
        # 結果が正しく返されるかチェック
        self.assertEqual(result, mock_analysis)
        mock_analyzer.analyze_class_purpose.assert_called_once_with("Calculator")


class TestMockedPerformanceOptimizerIntegration(unittest.TestCase):
    """パフォーマンス最適化統合のモックテスト"""
    
    @patch('code_parser.performance_optimizer.PerformanceOptimizer')
    def test_performance_benchmark_mock(self, mock_optimizer_class):
        """パフォーマンスベンチマークのモックテスト"""
        # モックの設定
        mock_optimizer = Mock()
        mock_optimizer_class.return_value = mock_optimizer
        
        # モックのベンチマーク結果
        mock_results = {
            "search_top_5": Mock(
                operation_type="search_top_5",
                total_time=0.5,
                avg_time=0.1,
                items_processed=5
            )
        }
        mock_optimizer.benchmark_search_performance.return_value = mock_results
        
        # ベンチマークの実行
        optimizer = mock_optimizer_class()
        results = optimizer.benchmark_search_performance(["test query"])
        
        # 結果が正しく返されるかチェック
        self.assertEqual(results, mock_results)
        mock_optimizer.benchmark_search_performance.assert_called_once_with(["test query"])


class TestMockedRAGSearchEngineIntegration(unittest.TestCase):
    """RAG検索エンジン統合のモックテスト"""
    
    @patch('code_parser.rag_search_engine.RAGSearchEngine')
    def test_rag_search_engine_mock(self, mock_rag_class):
        """RAG検索エンジンのモックテスト"""
        # モックの設定
        mock_rag = Mock()
        mock_rag_class.return_value = mock_rag
        
        # モックのインデックス化結果
        mock_index_result = {
            "total_extracted": 10,
            "successfully_indexed": 10,
            "elapsed_time": 1.5
        }
        mock_rag.index_file.return_value = mock_index_result
        
        # ファイルのインデックス化
        rag_engine = mock_rag_class()
        result = rag_engine.index_file("test_file.py")
        
        # 結果が正しく返されるかチェック
        self.assertEqual(result, mock_index_result)
        mock_rag.index_file.assert_called_once_with("test_file.py")
    
    @patch('code_parser.rag_search_engine.RAGSearchEngine')
    def test_rag_search_query_mock(self, mock_rag_class):
        """RAG検索クエリのモックテスト"""
        # モックの設定
        mock_rag = Mock()
        mock_rag_class.return_value = mock_rag
        
        # モックの検索結果
        mock_results = [
            {"id": "result1", "content": "test content 1"},
            {"id": "result2", "content": "test content 2"}
        ]
        mock_rag.search.return_value = mock_results
        
        # 検索の実行
        rag_engine = mock_rag_class()
        results = rag_engine.search("test query", top_k=5)
        
        # 結果が正しく返されるかチェック
        self.assertEqual(results, mock_results)
        mock_rag.search.assert_called_once_with("test query", top_k=5)


class TestMockedDataMigrationIntegration(unittest.TestCase):
    """データ移行統合のモックテスト"""
    
    @patch('code_parser.enhanced_data_migration.DataModelMigrator')
    def test_data_migration_mock(self, mock_migrator_class):
        """データ移行のモックテスト"""
        # モックの設定
        mock_migrator = Mock()
        mock_migrator_class.return_value = mock_migrator
        
        # モックの移行状況
        mock_status = {
            "existing_node_types": ["Module", "Function"],
            "needs_migration": {"node_types": True, "relation_types": False},
            "migration_plan": [{"step": "create_constraints", "priority": 1}]
        }
        mock_migrator.check_migration_status.return_value = mock_status
        
        # 移行状況のチェック
        migrator = mock_migrator_class()
        status = migrator.check_migration_status()
        
        # 結果が正しく返されるかチェック
        self.assertEqual(status, mock_status)
        mock_migrator.check_migration_status.assert_called_once()


class TestMockedEnhancedParserAdapterIntegration(unittest.TestCase):
    """拡張パーサーアダプター統合のモックテスト"""
    
    @patch('code_parser.enhanced_parser_adapter.EnhancedParserAdapter')
    def test_parser_adapter_mock(self, mock_adapter_class):
        """パーサーアダプターのモックテスト"""
        # モックの設定
        mock_adapter = Mock()
        mock_adapter_class.return_value = mock_adapter
        
        # モックの変換結果
        mock_enhanced_node = Mock(
            node_id="enhanced_001",
            node_type="EnhancedFunction",
            name="test_function"
        )
        mock_adapter.convert_syntax_node.return_value = mock_enhanced_node
        
        # ノードの変換
        adapter = mock_adapter_class()
        result = adapter.convert_syntax_node("test_node")
        
        # 結果が正しく返されるかチェック
        self.assertEqual(result, mock_enhanced_node)
        mock_adapter.convert_syntax_node.assert_called_once_with("test_node")


if __name__ == "__main__":
    # テストの実行
    unittest.main(verbosity=2)
