"""
LLM分析機能のテスト

このファイルは、LLM分析機能の基本的なテストを提供します。
"""

import unittest
from unittest.mock import Mock, patch
from analysis_schemas import FunctionAnalysis, ClassAnalysis, ErrorAnalysis, SyntaxNode
from enhanced_llm_analyzer import EnhancedLLMAnalyzer
from llm_analysis_utils import LLMAnalysisManager


class TestAnalysisSchemas(unittest.TestCase):
    """分析スキーマのテスト"""
    
    def test_function_analysis_creation(self):
        """FunctionAnalysisの作成テスト"""
        analysis = FunctionAnalysis(
            purpose="テスト関数",
            input_spec={"param1": "string"},
            usage_examples=["example1", "example2"]
        )
        
        self.assertEqual(analysis.purpose, "テスト関数")
        self.assertEqual(analysis.input_spec["param1"], "string")
        self.assertEqual(len(analysis.usage_examples), 2)
        self.assertTrue(analysis.is_valid())
    
    def test_function_analysis_invalid(self):
        """無効なFunctionAnalysisのテスト"""
        analysis = FunctionAnalysis(purpose="分析できませんでした")
        self.assertFalse(analysis.is_valid())
    
    def test_class_analysis_creation(self):
        """ClassAnalysisの作成テスト"""
        analysis = ClassAnalysis(
            purpose="テストクラス",
            design_pattern="Factory",
            methods=[{"name": "test_method", "purpose": "テスト"}]
        )
        
        self.assertEqual(analysis.purpose, "テストクラス")
        self.assertEqual(analysis.design_pattern, "Factory")
        self.assertTrue(analysis.is_valid())
    
    def test_syntax_node_creation(self):
        """SyntaxNodeの作成テスト"""
        node = SyntaxNode(
            name="test_function",
            text="def test_function(): pass",
            node_type="function",
            line_start=1,
            line_end=1
        )
        
        self.assertEqual(node.name, "test_function")
        self.assertEqual(node.node_type, "function")
        
        # 辞書変換テスト
        node_dict = node.to_dict()
        self.assertIn("name", node_dict)
        self.assertIn("text", node_dict)


class TestEnhancedLLMAnalyzer(unittest.TestCase):
    """EnhancedLLMAnalyzerのテスト"""
    
    def setUp(self):
        """テストの前準備"""
        self.analyzer = EnhancedLLMAnalyzer()
    
    def test_analyzer_initialization(self):
        """アナライザーの初期化テスト"""
        self.assertEqual(self.analyzer.model_name, "gpt-4")
        self.assertEqual(self.analyzer.temperature, 0.1)
    
    def test_fallback_function_analysis(self):
        """フォールバック関数分析のテスト"""
        node = SyntaxNode(
            name="test_func",
            text="def test_func(): pass",
            node_type="function"
        )
        
        analysis = self.analyzer._generate_fallback_function_analysis(node, "Test error")
        self.assertIsInstance(analysis, FunctionAnalysis)
        self.assertIn("Test error", analysis.purpose)
    
    def test_fallback_class_analysis(self):
        """フォールバッククラス分析のテスト"""
        node = SyntaxNode(
            name="TestClass",
            text="class TestClass: pass",
            node_type="class"
        )
        
        analysis = self.analyzer._generate_fallback_class_analysis(node, "Test error")
        self.assertIsInstance(analysis, ClassAnalysis)
        self.assertIn("Test error", analysis.purpose)
    
    def test_validate_function_analysis(self):
        """関数分析結果の検証テスト"""
        # 不完全な分析結果
        incomplete_analysis = {
            "purpose": "テスト関数",
            "input_spec": {"param": "string"}
            # 他のフィールドは欠落
        }
        
        validated = self.analyzer._validate_function_analysis(incomplete_analysis)
        
        # 必要なフィールドが全て存在することを確認
        required_fields = [
            "purpose", "input_spec", "output_spec", "usage_examples",
            "error_handling", "performance", "limitations", "related_functions"
        ]
        
        for field in required_fields:
            self.assertIn(field, validated)
        
        self.assertEqual(validated["purpose"], "テスト関数")
        self.assertEqual(validated["input_spec"]["param"], "string")


class TestLLMAnalysisManager(unittest.TestCase):
    """LLMAnalysisManagerのテスト"""
    
    def setUp(self):
        """テストの前準備"""
        self.manager = LLMAnalysisManager()
    
    def test_manager_initialization(self):
        """マネージャーの初期化テスト"""
        self.assertIsInstance(self.manager.analyzer, EnhancedLLMAnalyzer)
        self.assertEqual(len(self.manager.analysis_cache), 0)
    
    def test_detect_element_type(self):
        """要素タイプの自動検出テスト"""
        # 関数の検出
        func_code = "def test_function(): pass"
        self.assertEqual(self.manager._detect_element_type(func_code), "function")
        
        # クラスの検出
        class_code = "class TestClass: pass"
        self.assertEqual(self.manager._detect_element_type(class_code), "class")
        
        # その他のコードの検出
        other_code = "x = 1 + 2"
        self.assertEqual(self.manager._detect_element_type(other_code), "snippet")
    
    def test_create_syntax_node_from_code(self):
        """コードからSyntaxNodeの作成テスト"""
        func_code = "def example_func(): return 42"
        node = self.manager._create_syntax_node_from_code(func_code, "function")
        
        self.assertEqual(node.name, "example_func")
        self.assertEqual(node.node_type, "function")
        self.assertEqual(node.text, func_code)
    
    def test_cache_functionality(self):
        """キャッシュ機能のテスト"""
        # 初期状態
        self.assertEqual(len(self.manager.analysis_cache), 0)
        
        # キャッシュ統計
        stats = self.manager.get_cache_stats()
        self.assertEqual(stats["cache_size"], 0)
        
        # キャッシュクリア
        self.manager.clear_cache()
        self.assertEqual(len(self.manager.analysis_cache), 0)
    
    def test_analyze_nonexistent_file(self):
        """存在しないファイルの分析テスト"""
        result = self.manager.analyze_python_file("nonexistent_file.py")
        self.assertIn("error", result)
        self.assertEqual(result["error"], "File not found")


class TestIntegration(unittest.TestCase):
    """統合テスト"""
    
    def test_simple_code_analysis_flow(self):
        """シンプルなコード分析フローのテスト"""
        manager = LLMAnalysisManager()
        
        # シンプルな関数コード
        simple_code = """
def add_numbers(a, b):
    '''二つの数を足す'''
    return a + b
"""
        
        # 分析実行（LLMが利用できない場合はフォールバックが動作）
        result = manager.analyze_code_snippet(simple_code, "function")
        
        # 基本的な構造の確認
        self.assertIn("type", result)
        self.assertIn("analysis", result)
        
        # エラーまたは有効な分析結果のいずれかが返されることを確認
        if "error" not in result:
            analysis = result["analysis"]
            self.assertIn("purpose", analysis)
        else:
            # エラーの場合も適切にハンドリングされていることを確認
            self.assertIsInstance(result.get("error"), str)


def run_basic_tests():
    """基本的なテストを実行"""
    print("LLM分析機能の基本テストを実行します...")
    
    # テストローダーを使用
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # テストケースの追加
    test_suite.addTests(loader.loadTestsFromTestCase(TestAnalysisSchemas))
    test_suite.addTests(loader.loadTestsFromTestCase(TestEnhancedLLMAnalyzer))
    test_suite.addTests(loader.loadTestsFromTestCase(TestLLMAnalysisManager))
    test_suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # テストの実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    if result.wasSuccessful():
        print("\n✅ 全てのテストが成功しました！")
    else:
        print(f"\n❌ {len(result.failures)} 個のテストが失敗しました")
        print(f"❌ {len(result.errors)} 個のエラーが発生しました")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_basic_tests()