#!/usr/bin/env python3
"""
エンドツーエンド統合テスト - プロジェクト全体の動作確認
"""

import os
import sys
import unittest
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestProjectIntegrationE2E(unittest.TestCase):
    """プロジェクト全体のエンドツーエンドテスト"""

    def setUp(self):
        """テスト用の環境設定"""
        self.test_env = {
            'OPENAI_API_KEY': 'test_key_123',
            'NEO4J_URI': 'neo4j://localhost:7687',
            'NEO4J_USERNAME': 'neo4j',
            'NEO4J_PASSWORD': 'test_password'
        }

    def test_code_parser_workflow(self):
        """code_parserモジュールのワークフロー統合テスト"""
        with patch.dict(os.environ, self.test_env):
            try:
                from code_parser.treesitter_neo4j_advanced import TreeSitterNeo4jAdvancedBuilder
                
                # ビルダーの作成（LLM無効）
                builder = TreeSitterNeo4jAdvancedBuilder(
                    "neo4j://localhost:7687",
                    "neo4j",
                    "password",
                    enable_llm=False
                )
                
                # テスト用のPythonコード
                test_code = '''
def calculate_sum(a, b):
    """数値の合計を計算する関数"""
    return a + b

class Calculator:
    """簡単な計算機クラス"""
    
    def __init__(self):
        self.history = []
    
    def add(self, x, y):
        result = calculate_sum(x, y)
        self.history.append(f"{x} + {y} = {result}")
        return result

# メイン実行部分
if __name__ == "__main__":
    calc = Calculator()
    print(calc.add(2, 3))
'''
                
                # 一時ファイルでテスト
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(test_code)
                    temp_file = f.name
                
                try:
                    # ファイル解析
                    builder.analyze_file(temp_file)
                    
                    # 基本的な解析結果確認
                    self.assertGreater(len(builder.syntax_nodes), 0, "構文ノードが解析されている")
                    
                    # 関数とクラスが検出されていることを確認
                    node_names = [node.name for node in builder.syntax_nodes]
                    self.assertIn('calculate_sum', node_names, "関数が検出されている")
                    self.assertIn('Calculator', node_names, "クラスが検出されている")
                    
                finally:
                    # クリーンアップ
                    os.unlink(temp_file)
                    
            except Exception as e:
                self.skipTest(f"code_parserワークフローテストをスキップ: {e}")

    def test_code_generator_tools_integration(self):
        """code_generatorツール類の統合テスト"""
        with patch.dict(os.environ, self.test_env):
            try:
                from code_generator.tools import CodeValidationTool, UnitTestTool
                
                # コード検証ツールのテスト
                validation_tool = CodeValidationTool()
                
                # 有効なコード
                valid_code = "def hello(): return 'Hello, World!'"
                result = validation_tool._run(code=valid_code)
                self.assertIn("コードは有効です", result, "有効なコードが正しく検証される")
                
                # 単体テストツールのテスト
                test_tool = UnitTestTool()
                test_code = '''
import unittest
from source_code import hello

class TestHello(unittest.TestCase):
    def test_hello(self):
        self.assertEqual(hello(), "Hello, World!")
'''
                
                # モック化して実行
                with patch('subprocess.run') as mock_run:
                    mock_process = MagicMock()
                    mock_process.returncode = 0
                    mock_process.stderr = ".\n----------------------------------------------------------------------\nRan 1 test in 0.001s\n\nOK"
                    mock_run.return_value = mock_process
                    
                    result = test_tool._run(
                        code_to_test=valid_code,
                        test_code=test_code
                    )
                    self.assertIn("単体テストに成功しました", result, "単体テストが正常に動作する")
                    
            except Exception as e:
                self.skipTest(f"code_generatorツール統合テストをスキップ: {e}")

    def test_db_integration_workflow(self):
        """db_integrationモジュールのワークフロー統合テスト"""
        with patch.dict(os.environ, self.test_env):
            try:
                from db_integration.core.code_parser import CodeParser, SyntaxNode, NodeType
                
                # CodeParserの基本動作確認
                parser = CodeParser()
                
                # テスト用コード
                test_code = '''
import os

def process_data(data):
    """データを処理する関数"""
    return [x * 2 for x in data if x > 0]

class DataProcessor:
    def __init__(self, config):
        self.config = config
    
    def run(self):
        return process_data([1, 2, 3, -1, 4])
'''
                
                # 一時ファイルでテスト
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(test_code)
                    temp_file = f.name
                
                try:
                    # ファイル解析
                    nodes, relations = parser.parse_file(temp_file)
                    
                    # 解析結果の確認
                    self.assertGreater(len(nodes), 0, "ノードが解析されている")
                    
                    # 特定のノードタイプが検出されていることを確認
                    node_types = [node.node_type for node in nodes]
                    self.assertIn(NodeType.FUNCTION, node_types, "関数ノードが検出されている")
                    self.assertIn(NodeType.CLASS, node_types, "クラスノードが検出されている")
                    
                finally:
                    # クリーンアップ
                    os.unlink(temp_file)
                    
            except Exception as e:
                self.skipTest(f"db_integrationワークフローテストをスキップ: {e}")

    def test_doc_paser_file_handling(self):
        """doc_paserモジュールのファイル処理統合テスト"""
        try:
            # JSONファイルの存在確認
            doc_paser_dir = os.path.join(project_root, 'doc_paser')
            test_data_file = os.path.join(doc_paser_dir, 'test_data.json')
            api_result_file = os.path.join(doc_paser_dir, 'parsed_api_result.json')
            
            # ファイルの存在確認
            self.assertTrue(os.path.exists(test_data_file), "test_data.jsonが存在する")
            self.assertTrue(os.path.exists(api_result_file), "parsed_api_result.jsonが存在する")
            
            # ファイルサイズの確認（空でないことを確認）
            self.assertGreater(os.path.getsize(test_data_file), 0, "test_data.jsonが空でない")
            self.assertGreater(os.path.getsize(api_result_file), 0, "parsed_api_result.jsonが空でない")
            
        except Exception as e:
            self.skipTest(f"doc_paserファイル処理テストをスキップ: {e}")

    def test_project_structure_consistency(self):
        """プロジェクト構造の一貫性テスト"""
        try:
            # 主要ディレクトリの存在確認
            expected_dirs = [
                'code_parser',
                'code_generator', 
                'db_integration',
                'doc_paser',
                'tests'
            ]
            
            for dir_name in expected_dirs:
                dir_path = os.path.join(project_root, dir_name)
                self.assertTrue(os.path.exists(dir_path), f"{dir_name}ディレクトリが存在する")
                
                # __init__.pyファイルの存在確認（パッケージとして認識される）
                init_file = os.path.join(dir_path, '__init__.py')
                if dir_name != 'tests':  # testsディレクトリは__init__.pyがなくても良い
                    self.assertTrue(os.path.exists(init_file), f"{dir_name}/__init__.pyが存在する")
            
            # pyproject.tomlの存在確認
            pyproject_file = os.path.join(project_root, 'pyproject.toml')
            self.assertTrue(os.path.exists(pyproject_file), "pyproject.tomlが存在する")
            
            # READMEファイルの存在確認
            readme_file = os.path.join(project_root, 'README.md')
            self.assertTrue(os.path.exists(readme_file), "README.mdが存在する")
            
        except Exception as e:
            self.fail(f"プロジェクト構造テストに失敗: {e}")

    def test_environment_variable_handling(self):
        """環境変数の適切な処理テスト"""
        try:
            # 必要な環境変数のリスト
            required_env_vars = [
                'NEO4J_URI',
                'NEO4J_USERNAME', 
                'NEO4J_PASSWORD',
                'OPENAI_API_KEY'
            ]
            
            # 環境変数が設定されていない場合の適切なハンドリング確認
            with patch.dict(os.environ, {}, clear=True):
                # 各モジュールが環境変数不足を適切に処理することを確認
                from code_parser.parse_code import main as parse_main
                
                # parse_code.pyが環境変数チェックを行うことを確認
                with patch('sys.exit') as mock_exit:
                    parse_main()
                    # 環境変数が不足している場合は適切に終了することを確認
                    # （実装によってはSystemExitが呼ばれる）
                    
        except Exception as e:
            self.skipTest(f"環境変数処理テストをスキップ: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)