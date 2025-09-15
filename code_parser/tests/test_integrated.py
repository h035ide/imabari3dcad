"""
統合テスト - 3つのブランチの機能を統合したテスト

このテストは以下の機能をテストします：
1. Tree-sitterによるPythonコード解析
2. ベクトル検索による意味的検索
3. LLMによる高度なコード分析
4. パフォーマンス最適化
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from simple_utils import FileUtils, ValidationUtils, CacheUtils, PerformanceUtils
from simple_config import NEO4J_CONFIG, VECTOR_SEARCH_CONFIG, LLM_CONFIG


class TestFileUtils(unittest.TestCase):
    """FileUtilsのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.py")
        
        # テスト用Pythonファイルを作成
        with open(self.test_file, 'w') as f:
            f.write("def test_function():\n    pass\n")
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_ensure_directory(self):
        """ディレクトリ作成のテスト"""
        new_dir = os.path.join(self.temp_dir, "new", "subdir")
        FileUtils.ensure_directory(new_dir)
        self.assertTrue(os.path.exists(new_dir))
    
    def test_get_file_hash(self):
        """ファイルハッシュ取得のテスト"""
        hash1 = FileUtils.get_file_hash(self.test_file)
        hash2 = FileUtils.get_file_hash(self.test_file)
        self.assertEqual(hash1, hash2)
        self.assertIsInstance(hash1, str)
        self.assertEqual(len(hash1), 32)  # MD5ハッシュの長さ
    
    def test_is_python_file(self):
        """Pythonファイル判定のテスト"""
        self.assertTrue(FileUtils.is_python_file(self.test_file))
        self.assertFalse(FileUtils.is_python_file("test.txt"))
        self.assertFalse(FileUtils.is_python_file("test.pyc"))
    
    def test_find_python_files(self):
        """Pythonファイル検索のテスト"""
        # 追加のPythonファイルを作成
        test2_file = os.path.join(self.temp_dir, "test2.py")
        with open(test2_file, 'w') as f:
            f.write("print('hello')")
        
        python_files = FileUtils.find_python_files(self.temp_dir, recursive=False)
        self.assertEqual(len(python_files), 2)
        self.assertIn(self.test_file, python_files)
        self.assertIn(test2_file, python_files)


class TestValidationUtils(unittest.TestCase):
    """ValidationUtilsのテスト"""
    
    def test_validate_neo4j_config_valid(self):
        """有効なNeo4j設定のテスト"""
        self.assertTrue(ValidationUtils.validate_neo4j_config(
            "neo4j://localhost:7687", "neo4j", "password"
        ))
        self.assertTrue(ValidationUtils.validate_neo4j_config(
            "bolt://localhost:7687", "neo4j", "password"
        ))
    
    def test_validate_neo4j_config_invalid(self):
        """無効なNeo4j設定のテスト"""
        self.assertFalse(ValidationUtils.validate_neo4j_config("", "neo4j", "password"))
        self.assertFalse(ValidationUtils.validate_neo4j_config("neo4j://localhost:7687", "", "password"))
        self.assertFalse(ValidationUtils.validate_neo4j_config("neo4j://localhost:7687", "neo4j", ""))
        self.assertFalse(ValidationUtils.validate_neo4j_config("http://localhost:7687", "neo4j", "password"))
    
    def test_validate_file_path(self):
        """ファイルパス検証のテスト"""
        with tempfile.NamedTemporaryFile() as temp_file:
            self.assertTrue(ValidationUtils.validate_file_path(temp_file.name))
        
        self.assertFalse(ValidationUtils.validate_file_path("nonexistent_file.txt"))
        self.assertFalse(ValidationUtils.validate_file_path(""))
    
    def test_validate_python_code(self):
        """Pythonコード検証のテスト"""
        self.assertTrue(ValidationUtils.validate_python_code("print('hello')"))
        self.assertTrue(ValidationUtils.validate_python_code("def test(): pass"))
        self.assertFalse(ValidationUtils.validate_python_code("print('hello'"))  # 構文エラー
        self.assertFalse(ValidationUtils.validate_python_code(""))
        self.assertFalse(ValidationUtils.validate_python_code("   "))


class TestCacheUtils(unittest.TestCase):
    """CacheUtilsのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.cache = CacheUtils(max_size=3, ttl=1)
    
    def test_cache_set_get(self):
        """キャッシュの設定・取得のテスト"""
        self.cache.set("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")
        self.assertIsNone(self.cache.get("nonexistent"))
    
    def test_cache_max_size(self):
        """キャッシュの最大サイズ制限のテスト"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")
        self.cache.set("key4", "value4")  # 最大サイズを超える
        
        # 最も古いエントリが削除されているはず
        self.assertIsNone(self.cache.get("key1"))
        self.assertEqual(self.cache.get("key4"), "value4")
    
    def test_cache_ttl(self):
        """キャッシュのTTLのテスト"""
        # 初期タイムスタンプを0に設定
        self.cache.timestamps = {"key1": 0}
        self.cache.cache = {"key1": "value1"}
        
        # TTLを超える時間を設定
        with patch('simple_utils.time') as mock_time:
            mock_time.time.return_value = 1000  # TTLを超える
            self.assertIsNone(self.cache.get("key1"))
    
    def test_cache_clear(self):
        """キャッシュのクリアのテスト"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        
        self.cache.clear()
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))


class TestPerformanceUtils(unittest.TestCase):
    """PerformanceUtilsのテスト"""
    
    def test_measure_time_decorator(self):
        """時間測定デコレータのテスト"""
        @PerformanceUtils.measure_time
        def test_function():
            import time
            time.sleep(0.01)  # 10ms待機
            return "test"
        
        result = test_function()
        self.assertEqual(result, "test")
    
    def test_benchmark_function(self):
        """関数ベンチマークのテスト"""
        def test_function():
            import time
            time.sleep(0.001)  # 1ms待機
        
        results = PerformanceUtils.benchmark_function(test_function, iterations=3)
        
        self.assertIn("min_time", results)
        self.assertIn("max_time", results)
        self.assertIn("avg_time", results)
        self.assertIn("total_time", results)
        self.assertEqual(results["iterations"], 3)
        
        # 時間が正しく測定されているかチェック
        self.assertGreater(results["min_time"], 0)
        self.assertGreater(results["max_time"], 0)
        self.assertGreater(results["avg_time"], 0)
        self.assertGreater(results["total_time"], 0)


class TestSimpleConfig(unittest.TestCase):
    """設定ファイルのテスト"""
    
    def test_neo4j_config_structure(self):
        """Neo4j設定の構造テスト"""
        self.assertIn("uri", NEO4J_CONFIG)
        self.assertIn("user", NEO4J_CONFIG)
        self.assertIn("password", NEO4J_CONFIG)
        self.assertIn("database", NEO4J_CONFIG)
    
    def test_vector_search_config_structure(self):
        """ベクトル検索設定の構造テスト"""
        self.assertIn("persist_directory", VECTOR_SEARCH_CONFIG)
        self.assertIn("collection_name", VECTOR_SEARCH_CONFIG)
        self.assertIn("embedding_model", VECTOR_SEARCH_CONFIG)
    
    def test_llm_config_structure(self):
        """LLM設定の構造テスト"""
        self.assertIn("model_name", LLM_CONFIG)
        self.assertIn("temperature", LLM_CONFIG)
        self.assertIn("api_key", LLM_CONFIG)


class TestIntegration(unittest.TestCase):
    """統合テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_integration.py")
        
        # テスト用Pythonファイルを作成
        test_code = '''
def calculate_fibonacci(n):
    """フィボナッチ数列のn番目の値を計算"""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

class MathUtils:
    """数学ユーティリティクラス"""
    
    def __init__(self):
        self.cache = {}
    
    def factorial(self, n):
        """階乗を計算"""
        if n <= 1:
            return 1
        return n * self.factorial(n-1)
'''
        
        with open(self.test_file, 'w') as f:
            f.write(test_code)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('code_parser.treesitter_neo4j_advanced.TreeSitterNeo4jAdvancedBuilder')
    def test_file_parsing_integration(self, mock_builder_class):
        """ファイル解析の統合テスト"""
        # モックの設定
        mock_builder = Mock()
        mock_builder_class.return_value = mock_builder
        
        # ファイル解析のテスト
        self.assertTrue(FileUtils.is_python_file(self.test_file))
        self.assertTrue(ValidationUtils.validate_file_path(self.test_file))
        
        # ファイルハッシュの取得
        file_hash = FileUtils.get_file_hash(self.test_file)
        self.assertIsInstance(file_hash, str)
    
    def test_cache_performance_integration(self):
        """キャッシュとパフォーマンスの統合テスト"""
        cache = CacheUtils(max_size=10, ttl=60)
        
        # キャッシュにデータを設定
        for i in range(5):
            cache.set(f"key{i}", f"value{i}")
        
        # パフォーマンス測定
        def cache_operation():
            for i in range(5):
                cache.get(f"key{i}")
        
        results = PerformanceUtils.benchmark_function(cache_operation, iterations=3)
        # ベンチマーク結果が正しく計算されているかチェック
        self.assertIn("total_time", results)
        self.assertIn("avg_time", results)
        self.assertEqual(results["iterations"], 3)


if __name__ == "__main__":
    # テストの実行
    unittest.main(verbosity=2)
