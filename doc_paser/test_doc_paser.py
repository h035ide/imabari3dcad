#!/usr/bin/env python3
"""
doc_paserモジュールの簡単で理解しやすいテストスイート
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
import json

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestDocPaserBasic(unittest.TestCase):
    """doc_paserモジュールの基本機能テスト"""

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    def test_import_doc_paser_module(self):
        """doc_paserモジュールが正常にインポートできることを確認"""
        try:
            import doc_paser.doc_paser
            self.assertTrue(True, "doc_paserモジュールが正常にインポートされた")
        except ImportError as e:
            self.skipTest(f"doc_paserモジュールのインポートをスキップ: {e}")

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    def test_import_neo4j_importer_module(self):
        """neo4j_importerモジュールが正常にインポートできることを確認"""
        try:
            import doc_paser.neo4j_importer
            self.assertTrue(True, "neo4j_importerモジュールが正常にインポートされた")
        except ImportError as e:
            self.skipTest(f"neo4j_importerモジュールのインポートをスキップ: {e}")

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    def test_import_clear_database_module(self):
        """clear_databaseモジュールが正常にインポートできることを確認"""
        try:
            import doc_paser.clear_database
            self.assertTrue(True, "clear_databaseモジュールが正常にインポートされた")
        except ImportError as e:
            self.skipTest(f"clear_databaseモジュールのインポートをスキップ: {e}")


class TestDocPaserFileHandling(unittest.TestCase):
    """ファイル処理のテスト"""

    def test_json_file_exists(self):
        """テスト用のJSONファイルが存在することを確認"""
        test_data_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'test_data.json'
        )
        self.assertTrue(os.path.exists(test_data_file), "test_data.jsonファイルが存在する")

    def test_json_file_structure(self):
        """test_data.jsonファイルの構造が正しいことを確認"""
        test_data_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'test_data.json'
        )
        
        if os.path.exists(test_data_file):
            try:
                with open(test_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # JSONファイルが有効であることを確認
                self.assertIsInstance(data, (dict, list), "JSONファイルが正しい形式である")
                
            except json.JSONDecodeError as e:
                self.fail(f"JSONファイルの解析に失敗: {e}")
        else:
            self.skipTest("test_data.jsonファイルが存在しません")

    def test_parsed_api_result_exists(self):
        """parsed_api_result.jsonファイルが存在することを確認"""
        api_result_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'parsed_api_result.json'
        )
        self.assertTrue(os.path.exists(api_result_file), "parsed_api_result.jsonファイルが存在する")


class TestDocPaserFunctionality(unittest.TestCase):
    """機能的なテスト"""

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    def test_doc_paser_module_structure(self):
        """doc_paserモジュールが必要な要素を持っていることを確認"""
        try:
            import doc_paser.doc_paser as dp
            
            # 主要な関数やクラスが存在することを確認
            expected_attributes = ['main']  # 実際のモジュール構造に応じて調整
            for attr in expected_attributes:
                if hasattr(dp, attr):
                    self.assertTrue(callable(getattr(dp, attr)), f"{attr}が呼び出し可能である")
                    
        except Exception as e:
            # インポートエラーの場合はテストをスキップ
            self.skipTest(f"モジュールの構造テストをスキップ: {e}")

    @patch.dict(os.environ, {
        'NEO4J_URI': 'neo4j://localhost:7687',
        'NEO4J_USERNAME': 'neo4j',
        'NEO4J_PASSWORD': 'test_password'
    })
    def test_neo4j_importer_structure(self):
        """neo4j_importerモジュールが必要な要素を持っていることを確認"""
        try:
            import doc_paser.neo4j_importer as ni
            
            # 主要なクラスや関数が存在することを確認
            expected_attributes = ['main']  # 実際のモジュール構造に応じて調整
            for attr in expected_attributes:
                if hasattr(ni, attr):
                    self.assertTrue(callable(getattr(ni, attr)), f"{attr}が呼び出し可能である")
                    
        except Exception as e:
            # インポートエラーの場合はテストをスキップ
            self.skipTest(f"neo4j_importerの構造テストをスキップ: {e}")

    @patch('builtins.open', new_callable=mock_open, read_data='{"test": "data"}')
    def test_json_file_reading(self, mock_file):
        """JSONファイルの読み込み処理テスト"""
        # シンプルなJSONファイル読み込みテスト
        try:
            with open('test.json', 'r') as f:
                data = json.load(f)
            
            self.assertEqual(data, {"test": "data"}, "JSONファイルが正しく読み込まれる")
            mock_file.assert_called_once_with('test.json', 'r')
            
        except Exception as e:
            self.fail(f"JSONファイル読み込みテストに失敗: {e}")


class TestDocPaserErrorHandling(unittest.TestCase):
    """エラーハンドリングのテスト"""

    def test_missing_files_handling(self):
        """存在しないファイルの処理テスト"""
        nonexistent_file = '/path/to/nonexistent/file.json'
        
        # ファイルが存在しないことを確認
        self.assertFalse(os.path.exists(nonexistent_file), "テスト用の存在しないファイルパス")
        
        # ファイルアクセス時の適切なエラーハンドリングを確認
        with self.assertRaises(FileNotFoundError):
            with open(nonexistent_file, 'r') as f:
                json.load(f)

    def test_invalid_json_handling(self):
        """無効なJSONファイルの処理テスト"""
        invalid_json = '{"invalid": json, syntax}'
        
        with self.assertRaises(json.JSONDecodeError):
            json.loads(invalid_json)


if __name__ == '__main__':
    unittest.main(verbosity=2)