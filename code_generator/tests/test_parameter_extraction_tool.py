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

from code_generator.tools import ParameterExtractionTool

class TestParameterExtractionTool(unittest.TestCase):

    def setUp(self):
        """各テストの前に元の環境変数を保存し、クリアします。"""
        self.original_env = os.environ.copy()
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

    def tearDown(self):
        """各テストの後に環境変数を元に戻します。"""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_initialization_without_env_var(self):
        """APIキーがない場合、ツールが非アクティブで初期化されることをテストします。"""
        tool = ParameterExtractionTool()
        self.assertFalse(tool._is_configured)

    def test_run_in_disabled_mode(self):
        """非アクティブモードで実行された場合、フォールバックが機能することをテストします。"""
        tool = ParameterExtractionTool() # APIキーなしで初期化
        query = "some query"
        result = tool._run(query=query)
        self.assertEqual(result, {"intent": query, "parameters": {}})

    @patch('langchain_openai.ChatOpenAI.invoke')
    def test_run_with_valid_query_in_active_mode(self, mock_invoke):
        """APIキーがある場合に、意図とパラメータが正しく抽出されることをテストします。"""
        # --- Setup ---
        with patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key"}):
            tool = ParameterExtractionTool()
            self.assertTrue(tool._is_configured) # アクティブであることを確認

            # LLMの応答をモック
            mock_llm_response = MagicMock()
            mock_json_output = {
                "intent": "create a square cube",
                "parameters": {"side_length": 50}
            }
            mock_llm_response.content = json.dumps(mock_json_output)
            mock_invoke.return_value = mock_llm_response

            # --- Execute ---
            query = "一辺が50mmの正方形のキューブを作成してください"
            result = tool._run(query=query)

            # --- Assert ---
            self.assertIsInstance(result, dict)
            self.assertEqual(result['intent'], "create a square cube")
            self.assertEqual(result['parameters']['side_length'], 50)
            mock_invoke.assert_called_once()

    @patch('langchain_openai.ChatOpenAI.invoke')
    def test_run_with_parsing_error_in_active_mode(self, mock_invoke):
        """アクティブモードでLLMが不正なJSONを返した場合のフォールバック処理をテストします。"""
        # --- Setup ---
        with patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key"}):
            tool = ParameterExtractionTool()
            self.assertTrue(tool._is_configured)

            # LLMがパース不可能な不正な文字列を返したと仮定
            mock_llm_response = MagicMock()
            mock_llm_response.content = "this is not json"
            mock_invoke.return_value = mock_llm_response

            # --- Execute ---
            query = "some query"
            result = tool._run(query=query)

            # --- Assert ---
            self.assertEqual(result['intent'], query)
            self.assertEqual(result['parameters'], {})

if __name__ == '__main__':
    unittest.main()
