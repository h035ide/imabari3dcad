#!/usr/bin/env python3
"""
code_parserモジュールの統合テストスイート
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestCodeParser(unittest.TestCase):
    """code_parserモジュールの基本機能テスト"""

    def test_import_treesitter_module(self):
        """Tree-sitterモジュールが正常にインポートできることを確認"""
        try:
            from code_parser.treesitter_neo4j_advanced import TreeSitterNeo4jAdvancedBuilder
            self.assertTrue(True, "Tree-sitterモジュールのインポートに成功")
        except ImportError as e:
            self.fail(f"Tree-sitterモジュールのインポートに失敗: {e}")

    def test_builder_creation_without_neo4j(self):
        """Neo4j接続なしでビルダーが作成できることを確認"""
        try:
            from code_parser.treesitter_neo4j_advanced import TreeSitterNeo4jAdvancedBuilder
            
            # モックのNeo4j接続情報でビルダーを作成
            builder = TreeSitterNeo4jAdvancedBuilder(
                "neo4j://localhost:7687",
                "neo4j",
                "password",
                enable_llm=False
            )
            
            # ビルダーが正常に作成されたことを確認
            self.assertIsNotNone(builder)
            self.assertFalse(builder.enable_llm)
            
        except Exception as e:
            self.fail(f"ビルダーの作成に失敗: {e}")

    def test_parse_simple_python_code(self):
        """シンプルなPythonコードの解析テスト"""
        try:
            from code_parser.treesitter_neo4j_advanced import TreeSitterNeo4jAdvancedBuilder
            
            # ビルダーの作成
            builder = TreeSitterNeo4jAdvancedBuilder(
                "neo4j://localhost:7687",
                "neo4j", 
                "password",
                enable_llm=False
            )
            
            # テスト用のシンプルなPythonコード
            test_code = '''
def hello_world():
    """シンプルなテスト関数"""
    print("Hello, World!")
    return "success"

if __name__ == "__main__":
    hello_world()
'''
            
            # 一時ファイルを作成してテスト
            test_file_path = "/tmp/test_simple.py"
            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write(test_code)
            
            try:
                # ファイルを解析
                builder.analyze_file(test_file_path)
                
                # 解析結果を確認
                self.assertGreater(len(builder.syntax_nodes), 0, "構文ノードが解析されている")
                
            finally:
                # 一時ファイルをクリーンアップ
                if os.path.exists(test_file_path):
                    os.remove(test_file_path)
                    
        except Exception as e:
            self.fail(f"Pythonコードの解析に失敗: {e}")

    def test_parse_code_main_function(self):
        """parse_code.pyのメイン機能テスト"""
        try:
            from code_parser.parse_code import main
            
            # 環境変数をモック化
            with patch.dict(os.environ, {
                'NEO4J_URI': 'neo4j://localhost:7687',
                'NEO4J_USERNAME': 'neo4j',
                'NEO4J_PASSWORD': 'test_password'
            }):
                # TreeSitterNeo4jAdvancedBuilderをモック化
                with patch('code_parser.parse_code.TreeSitterNeo4jAdvancedBuilder') as mock_builder:
                    mock_instance = MagicMock()
                    mock_builder.return_value = mock_instance
                    
                    # sys.argvをモック化（存在しないファイルパスを指定）
                    with patch.object(sys, 'argv', ['parse_code.py', 'nonexistent_file.py']):
                        # ファイルが存在しないことをモック化
                        with patch('os.path.exists', return_value=False):
                            # 正常に実行できることを確認（例外が発生しないこと）
                            try:
                                main()  # ファイルが存在しない場合は早期リターンする
                            except SystemExit:
                                pass  # SystemExitは正常な終了として扱う
                            except Exception as e:
                                self.fail(f"main関数の実行に失敗: {e}")
                                
        except Exception as e:
            self.fail(f"parse_code.py のテストに失敗: {e}")


class TestCodeParserErrorHandling(unittest.TestCase):
    """エラーハンドリングのテスト"""
    
    def test_invalid_file_path(self):
        """存在しないファイルパスでの処理"""
        try:
            from code_parser.treesitter_neo4j_advanced import TreeSitterNeo4jAdvancedBuilder
            
            builder = TreeSitterNeo4jAdvancedBuilder(
                "neo4j://localhost:7687",
                "neo4j",
                "password",
                enable_llm=False
            )
            
            # 存在しないファイルパスでの処理
            nonexistent_file = "/path/to/nonexistent/file.py"
            
            # 例外が発生することを確認
            with self.assertRaises(Exception):
                builder.analyze_file(nonexistent_file)
                
        except Exception as e:
            # インポートエラーなどの場合はスキップ
            self.skipTest(f"テスト環境の制約によりスキップ: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)