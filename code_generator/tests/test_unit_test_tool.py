import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# --- [Path Setup] ---
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- [End Path Setup] ---

from code_generator.tools import UnitTestTool

class TestUnitTestTool(unittest.TestCase):

    def setUp(self):
        self.tool = UnitTestTool()
        self.valid_code = "def add(a, b):\n    return a + b"
        self.test_for_valid_code = (
            "import unittest\n"
            "from source_code import add\n\n"
            "class TestAdd(unittest.TestCase):\n"
            "    def test_add(self):\n"
            "        self.assertEqual(add(1, 2), 3)\n"
        )
        self.test_for_invalid_code = (
            "import unittest\n"
            "from source_code import add\n\n"
            "class TestAdd(unittest.TestCase):\n"
            "    def test_add_fail(self):\n"
            "        self.assertEqual(add(1, 2), 4)\n" # This will fail
        )

    @patch('subprocess.run')
    def test_run_with_passing_test(self, mock_subprocess_run):
        """単体テストが成功した場合に、成功メッセージが返されることをテストします。"""
        # unittestが成功した状態をモック
        mock_process = MagicMock()
        mock_process.stderr = ".\n----------------------------------------------------------------------\nRan 1 test in 0.001s\n\nOK"
        mock_process.returncode = 0  # 成功を示すreturncode
        mock_subprocess_run.return_value = mock_process

        result = self.tool._run(
            code_to_test=self.valid_code,
            test_code=self.test_for_valid_code
        )

        self.assertIn("単体テストに成功しました", result)
        mock_subprocess_run.assert_called_once()

    @patch('subprocess.run')
    def test_run_with_failing_test(self, mock_subprocess_run):
        """単体テストが失敗した場合に、エラー内容が返されることをテストします。"""
        # unittestが失敗した状態をモック
        mock_process = MagicMock()
        mock_process.stderr = (
            "F\n======================================================================\n"
            "FAIL: test_add_fail (test_code.TestAdd)\n"
            "----------------------------------------------------------------------\n"
            "Traceback (most recent call last):\n"
            "  File \"/tmp/tmp_dir/test_code.py\", line 6, in test_add_fail\n"
            "    self.assertEqual(add(1, 2), 4)\n"
            "AssertionError: 3 != 4\n\n"
            "----------------------------------------------------------------------\n"
            "Ran 1 test in 0.001s\n\nFAILED (failures=1)"
        )
        mock_process.returncode = 1  # 失敗を示すreturncode
        mock_subprocess_run.return_value = mock_process

        result = self.tool._run(
            code_to_test=self.valid_code,
            test_code=self.test_for_invalid_code
        )

        self.assertIn("単体テストで失敗またはエラーが検出されました", result)
        self.assertIn("AssertionError: 3 != 4", result)
        mock_subprocess_run.assert_called_once()

if __name__ == '__main__':
    unittest.main()
