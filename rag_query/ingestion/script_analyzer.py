"""
スクリプト解析モジュール

Tree-sitterを使用してPythonスクリプトを解析し、グラフデータを生成します。
"""

from tree_sitter import Language, Parser
import tree_sitter_python as tspython
from typing import List, Dict, Any, Tuple

from ..core.logger import get_logger
from ..core.exceptions import DataProcessingError

logger = get_logger(__name__)


class ScriptAnalyzer:
    """スクリプト解析クラス"""

    def __init__(self):
        """初期化"""
        self.language = Language(tspython.language())
        self.parser = Parser(self.language)

    def analyze_script(
        self, script_path: str, script_text: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        """
        スクリプトファイルを解析してグラフデータを生成する

        Args:
            script_path: スクリプトファイルパス
            script_text: スクリプト内容

        Returns:
            (トリプルのリスト, ノードプロパティ辞書)

        Raises:
            DataProcessingError: 解析エラー時
        """
        try:
            logger.info(f"スクリプト解析開始: {script_path}")

            triples = []
            node_props = {}

            # スクリプトノードを作成
            script_node_id = script_path
            node_props[script_node_id] = {
                "type": "ScriptExample",
                "properties": {"name": script_path, "code": script_text},
            }

            # メソッド呼び出しを抽出
            method_calls = self._extract_method_calls(script_text)
            all_methods_in_script = set()

            # データフロー追跡用の辞書
            variable_to_source_call_id = {}
            prev_call_node_id = None

            for i, call in enumerate(method_calls):
                method_name = call["method_name"]
                all_methods_in_script.add(method_name)

                # メソッド呼び出しノードを作成
                call_node_id = f"{script_path}_call_{i}"
                node_props[call_node_id] = {
                    "type": "MethodCall",
                    "properties": {"code": call["full_text"], "order": i},
                }

                # スクリプトとの関係を追加
                triples.append(
                    {
                        "source": script_node_id,
                        "source_type": "ScriptExample",
                        "label": "CONTAINS",
                        "target": call_node_id,
                        "target_type": "MethodCall",
                    }
                )

                # メソッドとの関係を追加
                triples.append(
                    {
                        "source": call_node_id,
                        "source_type": "MethodCall",
                        "label": "CALLS",
                        "target": method_name,
                        "target_type": "Method",
                    }
                )

                # データフロー解析
                self._analyze_data_flow(
                    call, call_node_id, variable_to_source_call_id, triples
                )

                # 順序関係の追加
                if prev_call_node_id:
                    triples.append(
                        {
                            "source": prev_call_node_id,
                            "source_type": "MethodCall",
                            "label": "NEXT",
                            "target": call_node_id,
                            "target_type": "MethodCall",
                        }
                    )

                prev_call_node_id = call_node_id

            # スクリプトとメソッドの関係を追加
            for method_name in all_methods_in_script:
                triples.append(
                    {
                        "source": script_node_id,
                        "source_type": "ScriptExample",
                        "label": "IS_EXAMPLE_OF",
                        "target": method_name,
                        "target_type": "Method",
                    }
                )

            logger.info(
                f"スクリプト解析完了: {script_path} - トリプル数={len(triples)}"
            )
            return triples, node_props

        except Exception as e:
            raise DataProcessingError(f"スクリプト解析エラー: {script_path}", str(e))

    def _extract_method_calls(self, script_text: str) -> List[Dict[str, Any]]:
        """
        スクリプトからメソッド呼び出しを抽出する

        Args:
            script_text: スクリプト内容

        Returns:
            メソッド呼び出し情報のリスト
        """
        tree = self.parser.parse(bytes(script_text, "utf8"))
        root_node = tree.root_node
        calls = []

        def find_calls(node):
            # メソッド呼び出し (`call`ノード) を探す
            if node.type == "call":
                function_node = node.child_by_field_name("function")
                # obj.method() の形式 (`attribute`ノード) であることを確認
                if function_node and function_node.type == "attribute":
                    obj_node = function_node.child_by_field_name("object")
                    method_node = function_node.child_by_field_name("attribute")

                    if obj_node and method_node:
                        call_details = {
                            "object_name": obj_node.text.decode("utf8"),
                            "method_name": method_node.text.decode("utf8"),
                            "full_text": node.text.decode("utf8"),
                            "node": node,
                            "assigned_to": None,
                        }

                        # 代入文の一部かチェック
                        parent = node.parent
                        if parent and parent.type == "assignment":
                            left_node = parent.child_by_field_name("left")
                            if left_node:
                                call_details["assigned_to"] = left_node.text.decode(
                                    "utf8"
                                )

                        calls.append(call_details)

            # 再帰的に子ノードを探索
            for child in node.children:
                find_calls(child)

        find_calls(root_node)
        return calls

    def _analyze_data_flow(
        self,
        call: Dict[str, Any],
        call_node_id: str,
        variable_to_source_call_id: Dict[str, str],
        triples: List[Dict[str, Any]],
    ) -> None:
        """
        データフローを解析してトリプルに追加する

        Args:
            call: メソッド呼び出し情報
            call_node_id: 呼び出しノードID
            variable_to_source_call_id: 変数と生成元の対応辞書
            triples: トリプルリスト（出力先）
        """
        # 引数の変数を解析
        arguments_node = call["node"].child_by_field_name("arguments")
        if arguments_node:
            arg_vars = []

            def find_identifiers(n):
                if n.type == "identifier":
                    arg_vars.append(n.text.decode("utf8"))
                for child in n.children:
                    find_identifiers(child)

            find_identifiers(arguments_node)

            # データフローのリレーションを追加
            for var_name in set(arg_vars):
                if var_name in variable_to_source_call_id:
                    source_call_node_id = variable_to_source_call_id[var_name]
                    triples.append(
                        {
                            "source": source_call_node_id,
                            "source_type": "MethodCall",
                            "label": "PASSES_RESULT_TO",
                            "target": call_node_id,
                            "target_type": "MethodCall",
                        }
                    )

        # 代入先変数を記録
        if call["assigned_to"]:
            variable_to_source_call_id[call["assigned_to"]] = call_node_id
