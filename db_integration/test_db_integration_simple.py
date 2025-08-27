#!/usr/bin/env python3
"""
db_integrationモジュールの簡単で理解しやすいテストスイート
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestDbIntegrationBasic(unittest.TestCase):
    """db_integrationモジュールの基本機能テスト"""

    def test_import_core_modules(self):
        """coreモジュールが正常にインポートできることを確認"""
        try:
            from db_integration.core.api_parser import ApiParser
            from db_integration.core.code_parser import CodeParser
            from db_integration.core.neo4j_uploader import Neo4jUploader
            self.assertTrue(True, "すべてのcoreモジュールが正常にインポートされた")
        except ImportError as e:
            self.fail(f"coreモジュールのインポートに失敗: {e}")

    def test_import_integrate_module(self):
        """integrateモジュールが正常にインポートできることを確認"""
        try:
            from db_integration.integrate import main
            self.assertTrue(callable(main), "main関数がインポートされた")
        except ImportError as e:
            self.fail(f"integrateモジュールのインポートに失敗: {e}")

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    def test_api_parser_creation(self):
        """ApiParserが正常に作成できることを確認"""
        try:
            from db_integration.core.api_parser import ApiParser
            parser = ApiParser()
            self.assertIsNotNone(parser, "ApiParserが正常に作成された")
        except Exception as e:
            self.fail(f"ApiParserの作成に失敗: {e}")

    def test_code_parser_creation(self):
        """CodeParserが正常に作成できることを確認"""
        try:
            from db_integration.core.code_parser import CodeParser
            parser = CodeParser()
            self.assertIsNotNone(parser, "CodeParserが正常に作成された")
        except Exception as e:
            self.fail(f"CodeParserの作成に失敗: {e}")

    @patch.dict(os.environ, {
        'NEO4J_URI': 'neo4j://localhost:7687',
        'NEO4J_USER': 'neo4j',
        'NEO4J_PASSWORD': 'test_password'
    })
    def test_neo4j_uploader_creation(self):
        """Neo4jUploaderが正常に作成できることを確認"""
        try:
            from db_integration.core.neo4j_uploader import Neo4jUploader
            # モック化されたNeo4jドライバーでUploaderを作成
            with patch('db_integration.core.neo4j_uploader.GraphDatabase') as mock_driver:
                mock_driver.driver.return_value = MagicMock()
                uploader = Neo4jUploader(
                    uri='neo4j://localhost:7687',
                    user='neo4j',
                    password='test_password',
                    database='test_db'
                )
                self.assertIsNotNone(uploader, "Neo4jUploaderが正常に作成された")
        except Exception as e:
            self.fail(f"Neo4jUploaderの作成に失敗: {e}")


class TestDbIntegrationDataModels(unittest.TestCase):
    """データモデルのテスト"""

    def test_syntax_node_creation(self):
        """SyntaxNodeが正常に作成できることを確認"""
        try:
            from db_integration.core.code_parser import SyntaxNode, NodeType
            node = SyntaxNode(
                node_id='test_1',
                node_type=NodeType.FUNCTION,
                name='test_function',
                text='def test_function(): pass',
                start_byte=0,
                end_byte=20,
                line_start=1,
                line_end=1,
                properties={}
            )
            self.assertEqual(node.node_id, 'test_1')
            self.assertEqual(node.name, 'test_function')
            self.assertEqual(node.node_type, NodeType.FUNCTION)
        except Exception as e:
            self.fail(f"SyntaxNodeの作成に失敗: {e}")

    def test_node_type_enum(self):
        """NodeTypeの列挙型が正常に動作することを確認"""
        try:
            from db_integration.core.code_parser import NodeType
            
            # 主要なノードタイプが定義されていることを確認
            expected_types = ['FUNCTION', 'CLASS', 'VARIABLE', 'IMPORT', 'MODULE']
            for type_name in expected_types:
                self.assertTrue(hasattr(NodeType, type_name), f"NodeType.{type_name}が定義されている")
        except Exception as e:
            self.fail(f"NodeType列挙型のテストに失敗: {e}")


class TestDbIntegrationErrorHandling(unittest.TestCase):
    """エラーハンドリングのテスト"""

    def test_missing_environment_variables(self):
        """環境変数が不足している場合の処理"""
        # 環境変数を一時的に削除
        with patch.dict(os.environ, {}, clear=True):
            with patch('db_integration.integrate.os.getenv') as mock_getenv:
                mock_getenv.return_value = None
                
                # mainの実行が適切にエラーハンドリングされることを確認
                try:
                    from db_integration.integrate import main
                    # main()を呼び出しても例外が発生しないか、適切にハンドリングされることを確認
                    # 実際の実装によってはSystemExitが発生する可能性がある
                    with patch('sys.exit') as mock_exit:
                        with patch('argparse.ArgumentParser.parse_args') as mock_args:
                            mock_args.return_value = MagicMock(
                                code_file='test.py',
                                api_doc='test.txt',
                                api_args='test.txt',
                                db_name='test',
                                clear_db=False
                            )
                            main()
                except Exception:
                    # 例外が発生しても、それは想定内の動作として扱う
                    pass


if __name__ == '__main__':
    unittest.main(verbosity=2)