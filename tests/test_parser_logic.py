import unittest
import tempfile
import os
import sys

# プロジェクトのルートをsys.pathに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code_parser.treesitter_neo4j_advanced import TreeSitterNeo4jAdvancedBuilder, NodeType

class TestParserLogic(unittest.TestCase):
    """
    TreeSitterNeo4jAdvancedBuilderの基本的な解析ロジックをテストする単体テスト。
    データベースやLLMなどの外部サービスには接続しません。
    """

    def setUp(self):
        """テストの前に毎回呼ばれるセットアップメソッド"""
        # ダミーの接続情報でビルダーを初期化
        self.builder = TreeSitterNeo4jAdvancedBuilder(
            neo4j_uri="dummy",
            neo4j_user="dummy",
            neo4j_password="dummy",
            enable_llm=False
        )

    def test_analyze_simple_function(self):
        """単純な関数定義を正しく解析できるかテスト"""
        # テスト対象のシンプルなPythonコード
        code_content = (
            "def my_simple_function(a, b):\n"
            "    return a + b\n"
        )

        # 一時ファイルにコードを書き込む
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False) as tmp:
            tmp.write(code_content)
            tmp_path = tmp.name

        try:
            # ファイルを解析
            self.builder.analyze_file(tmp_path)

            # --- アサーション ---
            # ノードが正しく生成されたか確認
            self.assertGreater(len(self.builder.syntax_nodes), 0, "ノードが一つも生成されませんでした")

            # Functionノードを探す
            function_nodes = [
                node for node in self.builder.syntax_nodes
                if node.node_type == NodeType.FUNCTION
            ]

            # Functionノードが1つだけ存在することを確認
            self.assertEqual(len(function_nodes), 1, "Functionノードの数が期待値と異なります")

            # そのFunctionノードの名前が正しいことを確認
            self.assertEqual(function_nodes[0].name, "my_simple_function", "関数名が正しく解析されていません")

            # Parameterノードが2つ存在することを確認
            parameter_nodes = [
                node for node in self.builder.syntax_nodes
                if node.node_type == NodeType.PARAMETER
            ]
            # tree-sitter-pythonの挙動により、parametersノードの中のidentifierもPARAMETERとして扱われる場合があるため、
            # 実際の解析結果に合わせたアサーションを行うのがより堅牢ですが、ここでは単純化します。
            # 期待されるパラメータは 'a' と 'b'
            param_names = {node.name for node in parameter_nodes}
            self.assertIn('a', param_names)
            self.assertIn('b', param_names)

        finally:
            # 一時ファイルを削除
            os.unlink(tmp_path)

if __name__ == '__main__':
    unittest.main()
