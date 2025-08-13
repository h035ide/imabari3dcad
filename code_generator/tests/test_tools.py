import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# --- [Path Setup] ---
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- [End Path Setup] ---

from code_generator.tools import GraphSearchTool
from langchain_core.documents import Document

class TestGraphSearchToolHybrid(unittest.TestCase):

    def setUp(self):
        """各テストの前に元の環境変数を保存し、クリアします。"""
        self.original_env = os.environ.copy()
        keys_to_clear = ["OPENAI_API_KEY", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"]
        for key in keys_to_clear:
            if key in os.environ:
                del os.environ[key]

    def tearDown(self):
        """各テストの後に環境変数を元に戻します。"""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_initialization_without_env_vars(self):
        """環境変数がない場合、ツールが非アクティブモードで初期化されることをテストします。"""
        tool = GraphSearchTool()
        self.assertFalse(tool._is_configured)
        self.assertIsNone(tool._neo4j_driver)
        self.assertIsNone(tool._vector_store)

    @patch('code_generator.tools.Chroma')
    @patch('code_generator.tools.GraphDatabase.driver')
    def test_initialization_with_env_vars(self, mock_neo4j_driver, mock_chroma):
        """環境変数がある場合、ツールがアクティブモードで初期化されることをテストします。"""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "fake_key",
            "NEO4J_URI": "bolt://fake_uri",
            "NEO4J_USER": "fake_user",
            "NEO4J_PASSWORD": "fake_password"
        }):
            tool = GraphSearchTool()
            self.assertTrue(tool._is_configured)
            self.assertIsNotNone(tool._neo4j_driver)
            self.assertIsNotNone(tool._vector_store)
            mock_neo4j_driver.assert_called_with("bolt://fake_uri", auth=("fake_user", "fake_password"))
            mock_chroma.assert_called()

    def test_run_in_disabled_mode(self):
        """設定されていないツールを実行すると、スキップメッセージが返されることをテストします。"""
        tool = GraphSearchTool()
        result = tool._run(query="any query")
        self.assertIn("ツールが設定されていません", result)

    @patch('os.path.exists', return_value=False)
    def test_run_when_chroma_db_missing(self, mock_exists):
        """ChromaDBが存在しない場合、適切なメッセージが返されることをテストします。"""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "fake_key",
            "NEO4J_URI": "bolt://fake_uri",
            "NEO4J_USER": "fake_user",
            "NEO4J_PASSWORD": "fake_password"
        }):
            # ツールが設定済みとして初期化されるように、ドライバとChromaもモックします
            with patch('code_generator.tools.Chroma'), patch('code_generator.tools.GraphDatabase.driver'):
                tool = GraphSearchTool()
                self.assertTrue(tool._is_configured)  # 実行前に設定済みであることを確認
                result = tool._run(query="any query")
                self.assertIn("ChromaDBのデータベースが見つかりません", result)

    @patch('os.path.exists', return_value=True)
    @patch('code_generator.tools.Chroma')
    @patch('code_generator.tools.GraphDatabase.driver')
    def test_hybrid_search_workflow(self, mock_neo4j_driver, mock_chroma, mock_exists):
        """ハイブリッド検索のワークフロー全体をモックしてテストします。"""
        # --- Setup Mocks ---
        # 1. 環境変数を設定
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "fake_key",
            "NEO4J_URI": "bolt://fake_uri",
            "NEO4J_USER": "fake_user",
            "NEO4J_PASSWORD": "fake_password"
        }):
            # 2. ChromaDBのモックを設定
            mock_vector_store_instance = mock_chroma.return_value
            mock_vector_store_instance.similarity_search.return_value = [
                Document(page_content="", metadata={"neo4j_node_id": "node123"}),
                Document(page_content="", metadata={"neo4j_node_id": "node456"})
            ]

            # 3. Neo4jドライバとセッションのモックを設定
            mock_session = MagicMock()
            mock_neo4j_record = {
                'apiName': 'MockAPI',
                'functionSignature': 'MockAPI(param1: str)',
                'className': 'MockClass',
                'parameters': ['param1'],
                'calledBy': ['Caller1', 'Caller2'],
                'returnType': 'Class',
                'returnName': 'MockResultObject'
            }
            mock_session.run.return_value = [
                MagicMock(data=lambda: mock_neo4j_record)
            ]
            mock_neo4j_driver.return_value.session.return_value.__enter__.return_value = mock_session

            # --- Execute ---
            tool = GraphSearchTool()
            result = tool._run(query="find mock api")

            # --- Assertions ---
            # 1. ベクトル検索が呼ばれたか
            mock_vector_store_instance.similarity_search.assert_called_with("find mock api", k=20)

            # 2. グラフ探索（Cypher）が正しいIDで呼ばれたか
            mock_session.run.assert_called_once()
            call_args = mock_session.run.call_args
            self.assertIn("WHERE elementId(api) IN $node_ids", call_args.args[0])
            self.assertEqual(call_args.kwargs['node_ids'], ["node123", "node456"])

            # 3. 最終的な出力が正しいか
            self.assertIn("ナレッジグラフから以下の情報が見つかりました", result)
            self.assertIn("- API名: MockAPI", result)
            self.assertIn("- 所属クラス: MockClass", result)
            self.assertIn("- シグネチャ: MockAPI(param1: str)", result)
            self.assertIn("- パラメータ: param1", result)
            self.assertIn("- 戻り値: MockResultObject (型: Class)", result)
            self.assertIn("- 主な呼び出し元: Caller1, Caller2", result)

if __name__ == '__main__':
    unittest.main()
