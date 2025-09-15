import unittest
import os
import sys
import json
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
    def test_hybrid_search_workflow_unambiguous(self, mock_neo4j_driver, mock_chroma, mock_exists):
        """[非曖昧ケース] ハイブリッド検索のワークフロー全体をテストします。"""
        # --- Setup Mocks ---
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "fake_key", "NEO4J_URI": "bolt://fake_uri",
            "NEO4J_USER": "fake_user", "NEO4J_PASSWORD": "fake_password"
        }):
            # 2. ChromaDBのモックを設定 (スコアに十分な差がある)
            mock_vector_store_instance = mock_chroma.return_value
            mock_vector_store_instance.similarity_search_with_score.return_value = [
                (Document(page_content="doc1", metadata={"neo4j_node_id": "node123"}), 0.1),
                (Document(page_content="doc2", metadata={"neo4j_node_id": "node456"}), 0.5)
            ]

            # 3. Neo4jドライバとセッションのモックを設定
            mock_session = MagicMock()
            mock_session.run.return_value = [MagicMock(data=lambda: {'apiName': 'MockAPI'})]
            mock_neo4j_driver.return_value.session.return_value.__enter__.return_value = mock_session

            # --- Execute ---
            tool = GraphSearchTool()
            result = tool._run(query="find mock api")

            # --- Assertions ---
            mock_vector_store_instance.similarity_search_with_score.assert_called_with("find mock api", k=5)
            mock_session.run.assert_called_once()
            self.assertNotIn("AMBIGUOUS_RESULTS::", result)
            self.assertIn("ナレッジグラフから以下の情報が見つかりました", result)

    @patch('os.path.exists', return_value=True)
    @patch('code_generator.tools.Chroma')
    @patch('code_generator.tools.GraphDatabase.driver')
    def test_hybrid_search_workflow_ambiguous(self, mock_neo4j_driver, mock_chroma, mock_exists):
        """[曖昧ケース] 検索結果が曖昧な場合に、特別な応答が返されることをテストします。"""
        # --- Setup Mocks ---
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "fake_key", "NEO4J_URI": "bolt://fake_uri",
            "NEO4J_USER": "fake_user", "NEO4J_PASSWORD": "fake_password"
        }):
            # 2. ChromaDBのモックを設定 (スコアが非常に近い)
            mock_vector_store_instance = mock_chroma.return_value
            doc1_content = "API名: Sphere\n説明: Creates a sphere."
            doc2_content = "API名: Ball\n説明: Creates a ball."
            mock_vector_store_instance.similarity_search_with_score.return_value = [
                (Document(page_content=doc1_content, metadata={"api_name": "Sphere"}), 0.10),
                (Document(page_content=doc2_content, metadata={"api_name": "Ball"}), 0.105) # 差が10%以内
            ]

            # Neo4jセッションは呼ばれないはず
            mock_session = MagicMock()
            mock_neo4j_driver.return_value.session.return_value.__enter__.return_value = mock_session

            # --- Execute ---
            tool = GraphSearchTool()
            result = tool._run(query="create a round object")

            # --- Assertions ---
            mock_vector_store_instance.similarity_search_with_score.assert_called_with("create a round object", k=5)
            mock_session.run.assert_not_called() # グラフ探索は実行されない
            self.assertTrue(result.startswith("AMBIGUOUS_RESULTS::"))

            # JSONペイロードを検証
            json_part = result.split("::", 1)[1]
            data = json.loads(json_part)
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]['name'], "Sphere")
            self.assertEqual(data[1]['name'], "Ball")

if __name__ == '__main__':
    unittest.main()
