import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os

# テスト対象のスクリプトがインポートできるようにパスを追加
# このテストファイルはプロジェクトルートから `python -m unittest db_integration/test_integration.py` のように実行されることを想定
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from db_integration.integrate import main
from db_integration.core.code_parser import SyntaxNode, SyntaxRelation, NodeType, RelationType

class TestIntegrationScript(unittest.TestCase):

    @patch('os.getenv')
    @patch('os.getenv')
    @patch('db_integration.integrate.ApiParser')
    @patch('db_integration.integrate.CodeParser')
    @patch('db_integration.integrate.Neo4jUploader')
    @patch('db_integration.integrate.load_dotenv')
    @patch('sys.argv', [
        'db_integration/integrate.py',
        '--code-file', 'dummy_code.py',
        '--api-doc', 'dummy_api.txt',
        '--api-args', 'dummy_args.txt',
        '--db-name', 'test_db',
        '--clear-db'
    ])
    def test_main_orchestration_flow(self, mock_load_dotenv, mock_uploader, mock_code_parser, mock_api_parser, mock_getenv):
        """
        メインスクリプトが正しい順序で各モジュールを呼び出すかをテストします。
        """
        # --- Mockのセットアップ ---
        mock_getenv.side_effect = lambda key, default=None: {
            "NEO4J_URI": "bolt://localhost:7687",
            "NEO4J_USER": "neo4j",
            "NEO4J_PASSWORD": "password"
        }.get(key, default)

        # ApiParserのモック
        mock_api_parser_instance = mock_api_parser.return_value
        mock_api_parser_instance.parse.return_value = {
            "type_definitions": [{"name": "string", "description": "A string"}],
            "api_entries": [{
                "entry_type": "function",
                "name": "TestFunc",
                "description": "A test function from API"
            }]
        }

        # CodeParserのモック
        mock_code_parser_instance = mock_code_parser.return_value
        mock_code_parser_instance.parse_file.return_value = (
            [SyntaxNode('Func_1', NodeType.FUNCTION, 'TestFunc', 'def TestFunc(): pass', 0, 20, 1, 1, {})],
            []
        )

        # Neo4jUploaderのモック
        mock_uploader_instance = mock_uploader.return_value

        # --- テストの実行 ---
        main()

        # --- 検証 ---

        # 1. 各パーサーが正しい引数で呼び出されたか
        mock_api_parser_instance.parse.assert_called_once_with('dummy_api.txt', 'dummy_args.txt')
        mock_code_parser_instance.parse_file.assert_called_once_with('dummy_code.py')

        # 2. Uploaderのメソッドが正しい順序で呼び出されたか
        expected_calls = [
            call.clear_database(),
            call.upload_api_data(mock_api_parser_instance.parse.return_value),
            call.upload_code_data(*mock_code_parser_instance.parse_file.return_value),
            call.link_graphs(),
            call.close()
        ]
        mock_uploader_instance.method_calls.assert_has_calls(expected_calls, any_order=False)

        # 3. Uploaderが正しい引数でインスタンス化されたか
        mock_uploader.assert_called_once()
        # 実際の引数を確認 (環境変数に依存するため、ここでは呼び出されたことの確認に留める)
        self.assertEqual(mock_uploader.call_args[0][3], 'test_db')


    @patch('db_integration.integrate.ApiParser')
    @patch('db_integration.integrate.CodeParser')
    @patch('db_integration.integrate.Neo4jUploader')
    @patch('db_integration.integrate.load_dotenv')
    @patch('sys.argv', [
        'db_integration/integrate.py',
        '--code-file', 'dummy.py',
        '--api-doc', 'dummy.txt',
        '--api-args', 'dummy.txt',
        '--db-name', 'test_db'
        # --clear-db なし
    ])
    def test_clear_db_flag_not_set(self, mock_load_dotenv, mock_uploader, mock_code_parser, mock_api_parser, mock_getenv):
        """
        --clear-dbフラグがない場合にclear_databaseが呼ばれないことをテストします。
        """
        # --- Mockのセットアップ ---
        mock_getenv.side_effect = lambda key, default=None: {
            "NEO4J_URI": "bolt://localhost:7687",
            "NEO4J_USER": "neo4j",
            "NEO4J_PASSWORD": "password"
        }.get(key, default)
        mock_uploader_instance = mock_uploader.return_value
        mock_api_parser.return_value.parse.return_value = {}
        mock_code_parser.return_value.parse_file.return_value = ([], [])

        # --- テストの実行 ---
        main()

        # --- 検証 ---
        mock_uploader_instance.clear_database.assert_not_called()
        self.assertTrue(mock_uploader_instance.upload_api_data.called)
        self.assertTrue(mock_uploader_instance.upload_code_data.called)


if __name__ == '__main__':
    unittest.main()
