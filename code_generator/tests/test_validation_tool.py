import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# --- [Path Setup] ---
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- [End Path Setup] ---

from code_generator.tools import CodeValidationTool

class TestCodeValidationTool(unittest.TestCase):

    def setUp(self):
        self.tool = CodeValidationTool()

    @patch('subprocess.run')
    def test_run_with_valid_code(self, mock_subprocess_run):
        """正常なコードを渡した際に、成功メッセージが返されることをテストします。"""
        # flake8が正常終了（問題なし）した状態をモック
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = ""
        mock_subprocess_run.return_value = mock_process

        valid_code = "import os\n\nprint(os.getcwd())\n"
        result = self.tool._run(code=valid_code)

        self.assertIn("コードの検証に成功しました", result)
        mock_subprocess_run.assert_called_once()

    @patch('subprocess.run')
    def test_run_with_invalid_code(self, mock_subprocess_run):
        """問題のあるコードを渡した際に、flake8のエラーが返されることをテストします。"""
        # flake8が問題を検出した状態をモック
        mock_process = MagicMock()
        mock_process.returncode = 1
        # flake8の実際の出力形式を模倣
        flake8_output = "/tmp/tmpxxxxxx.py:1:1: F401 'os' imported but unused"
        mock_process.stdout = flake8_output
        mock_subprocess_run.return_value = mock_process

        invalid_code = "import os\n\n" # 未使用のインポート
        result = self.tool._run(code=invalid_code)

        self.assertIn("コードの検証で以下の問題が検出されました", result)
        self.assertIn("1:1: F401 'os' imported but unused", result) # ファイルパスが除去された後のエラー
        mock_subprocess_run.assert_called_once()

    @patch('subprocess.run')
    def test_run_with_file_not_found_error(self, mock_subprocess_run):
        """flake8コマンドが存在しない場合に、エラーメッセージが返されることをテストします。"""
        # FileNotFoundErrorを発生させるようにモックを設定
        mock_subprocess_run.side_effect = FileNotFoundError

        code = "print('hello')"
        result = self.tool._run(code=code)

        self.assertIn("エラー: flake8コマンドが見つかりません", result)

if __name__ == '__main__':
    unittest.main()
