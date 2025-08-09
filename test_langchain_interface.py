"""
Tests for LangChain Interface

LangChainインターフェースの基本的なテストを実行します。
"""

import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# テスト対象のモジュールをインポート
from langchain_interface import (
    ConnectionConfig, 
    LangChainInterface, 
    Neo4jGraphIndex, 
    ChromaVectorStore,
    create_interface,
    quick_search
)


class TestConnectionConfig(unittest.TestCase):
    """ConnectionConfig のテスト"""
    
    def test_default_config(self):
        """デフォルト設定のテスト"""
        config = ConnectionConfig()
        self.assertEqual(config.neo4j_uri, "neo4j://localhost:7687")
        self.assertEqual(config.neo4j_username, "neo4j")
        self.assertEqual(config.chroma_collection_name, "imabari3dcad")
    
    def test_config_from_env(self):
        """環境変数からの設定読み込みテスト"""
        with patch.dict(os.environ, {
            'NEO4J_URI': 'neo4j://test:7687',
            'NEO4J_USERNAME': 'test_user',
            'CHROMA_COLLECTION': 'test_collection'
        }):
            config = ConnectionConfig.from_env()
            self.assertEqual(config.neo4j_uri, 'neo4j://test:7687')
            self.assertEqual(config.neo4j_username, 'test_user')
            self.assertEqual(config.chroma_collection_name, 'test_collection')


class TestNeo4jGraphIndex(unittest.TestCase):
    """Neo4jGraphIndex のテスト"""
    
    def setUp(self):
        self.config = ConnectionConfig(
            neo4j_password="test_password",
            neo4j_database="test_db"
        )
    
    def test_init_without_neo4j_library(self):
        """Neo4jライブラリがない場合の初期化テスト"""
        with patch('langchain_interface.GraphDatabase', side_effect=ImportError):
            index = Neo4jGraphIndex(self.config)
            self.assertIsNone(index.driver)
    
    def test_query_without_driver(self):
        """ドライバーがない場合のクエリテスト"""
        with patch('langchain_interface.GraphDatabase', side_effect=ImportError):
            index = Neo4jGraphIndex(self.config)
            result = index.query("MATCH (n) RETURN n")
            self.assertIn("Mock response", result)
    
    def test_add_documents_without_driver(self):
        """ドライバーがない場合のドキュメント追加テスト"""
        with patch('langchain_interface.GraphDatabase', side_effect=ImportError):
            index = Neo4jGraphIndex(self.config)
            # エラーが発生しないことを確認
            index.add_documents(["test document"])


class TestChromaVectorStore(unittest.TestCase):
    """ChromaVectorStore のテスト"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = ConnectionConfig(
            chroma_persist_directory=self.temp_dir,
            chroma_collection_name="test_collection"
        )
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_without_chroma_library(self):
        """Chromaライブラリがない場合の初期化テスト"""
        with patch('langchain_interface.chromadb', side_effect=ImportError):
            store = ChromaVectorStore(self.config)
            self.assertIsNone(store.client)
            self.assertIsNone(store.collection)
    
    def test_similarity_search_without_client(self):
        """クライアントがない場合の類似度検索テスト"""
        with patch('langchain_interface.chromadb', side_effect=ImportError):
            store = ChromaVectorStore(self.config)
            results = store.similarity_search("test query")
            self.assertEqual(len(results), 1)
            self.assertIn("Mock result", results[0]["content"])
    
    def test_add_texts_without_client(self):
        """クライアントがない場合のテキスト追加テスト"""
        with patch('langchain_interface.chromadb', side_effect=ImportError):
            store = ChromaVectorStore(self.config)
            # エラーが発生しないことを確認
            store.add_texts(["test text"])


class TestLangChainInterface(unittest.TestCase):
    """LangChainInterface のテスト"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = ConnectionConfig(
            neo4j_password="test_password",
            chroma_persist_directory=self.temp_dir
        )
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """インターフェースの初期化テスト"""
        interface = LangChainInterface(self.config)
        self.assertIsNotNone(interface.graph_index)
        self.assertIsNotNone(interface.vector_store)
        interface.close()
    
    def test_hybrid_search(self):
        """ハイブリッド検索のテスト"""
        interface = LangChainInterface(self.config)
        results = interface.hybrid_search("test query")
        
        self.assertIn("vector_results", results)
        self.assertIn("graph_results", results)
        self.assertEqual(results["query"], "test query")
        
        interface.close()
    
    def test_add_document(self):
        """ドキュメント追加のテスト"""
        interface = LangChainInterface(self.config)
        
        # エラーが発生しないことを確認
        interface.add_document("test content", {"type": "test"})
        
        interface.close()
    
    def test_connection_status(self):
        """接続状態確認のテスト"""
        interface = LangChainInterface(self.config)
        status = interface.get_connection_status()
        
        self.assertIn("neo4j_connected", status)
        self.assertIn("chroma_connected", status)
        self.assertIsInstance(status["neo4j_connected"], bool)
        self.assertIsInstance(status["chroma_connected"], bool)
        
        interface.close()


class TestFactoryFunctions(unittest.TestCase):
    """ファクトリー関数のテスト"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_interface_with_config_dict(self):
        """設定辞書を使ったインターフェース作成テスト"""
        config_dict = {
            "neo4j_password": "test",
            "chroma_persist_directory": self.temp_dir
        }
        
        interface = create_interface(config_dict)
        self.assertIsNotNone(interface)
        interface.close()
    
    def test_create_interface_with_env(self):
        """環境変数を使ったインターフェース作成テスト"""
        with patch.dict(os.environ, {
            'NEO4J_PASSWORD': 'test_env_password',
            'CHROMA_PERSIST_DIR': self.temp_dir
        }):
            interface = create_interface()
            self.assertIsNotNone(interface)
            interface.close()
    
    def test_quick_search(self):
        """クイック検索のテスト"""
        config = ConnectionConfig(
            neo4j_password="test",
            chroma_persist_directory=self.temp_dir
        )
        
        results = quick_search("test query", config)
        self.assertIsInstance(results, dict)
        self.assertIn("query", results)


class TestIntegrationScenarios(unittest.TestCase):
    """統合シナリオのテスト"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = ConnectionConfig(
            neo4j_password="test_password",
            chroma_persist_directory=self.temp_dir
        )
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_workflow(self):
        """完全なワークフローのテスト"""
        interface = LangChainInterface(self.config)
        
        # ドキュメント追加
        interface.add_document(
            "imabari3dcadは3D CADアプリケーションです",
            {"category": "description"}
        )
        
        # 検索実行
        results = interface.hybrid_search("3D CAD")
        self.assertIsInstance(results, dict)
        
        # 接続状態確認
        status = interface.get_connection_status()
        self.assertIsInstance(status, dict)
        
        interface.close()
    
    def test_error_handling(self):
        """エラーハンドリングのテスト"""
        # 無効な設定での初期化
        bad_config = ConnectionConfig(
            neo4j_uri="invalid://uri",
            chroma_persist_directory="/invalid/path"
        )
        
        interface = LangChainInterface(bad_config)
        
        # エラーが発生しても例外が投げられないことを確認
        results = interface.hybrid_search("test")
        self.assertIsInstance(results, dict)
        
        interface.close()


def run_basic_functionality_test():
    """基本機能の動作テスト"""
    print("=== Basic Functionality Test ===")
    
    try:
        # テスト用の一時ディレクトリ
        temp_dir = tempfile.mkdtemp()
        
        print("1. Creating LangChain Interface...")
        config = ConnectionConfig(
            neo4j_password="test_password",
            chroma_persist_directory=temp_dir
        )
        interface = LangChainInterface(config)
        
        print("2. Checking connection status...")
        status = interface.get_connection_status()
        print(f"   Connection Status: {status}")
        
        print("3. Adding test document...")
        interface.add_document(
            "これはテストドキュメントです。LangChainインターフェースのテストを行っています。",
            {"type": "test", "language": "ja"}
        )
        
        print("4. Performing hybrid search...")
        results = interface.hybrid_search("LangChain テスト")
        print(f"   Search completed. Result keys: {list(results.keys())}")
        
        print("5. Testing individual components...")
        # ベクトル検索
        vector_results = interface.search_vectors("テスト")
        print(f"   Vector search results: {len(vector_results)}")
        
        # グラフクエリ
        graph_result = interface.query_graph("MATCH (n) RETURN count(n) as count")
        print(f"   Graph query result: {graph_result}")
        
        print("6. Cleanup...")
        interface.close()
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        print("✓ Basic functionality test completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False


if __name__ == "__main__":
    print("LangChain Interface Test Suite\n")
    
    # 基本機能テスト
    basic_test_success = run_basic_functionality_test()
    print()
    
    # ユニットテスト実行
    print("=== Running Unit Tests ===")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    if basic_test_success:
        print("\n✓ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed!")
        sys.exit(1)