#%%
import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query, Node, QueryCursor
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import json
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any, Literal, Union

# .envファイルから環境変数を読み込む
load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


def test_neo4j_connection(uri: str, username: str, password: str, database_name: str = "neo4j") -> bool:
    """Neo4j接続をテストする関数"""
    print(f"\n=== Neo4j接続テスト ===")
    print(f"URI: {uri}")
    print(f"ユーザー名: {username}")
    print(f"データベース名: {database_name}")
    
    try:
        # ステップ1: ドライバー作成
        print("1. ドライバーを作成中...")
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        # ステップ2: 接続確認
        print("2. 接続を確認中...")
        driver.verify_connectivity()
        print("✓ 接続成功")
        
        # ステップ3: データベース確認
        print("3. データベースを確認中...")
        with driver.session(database="system") as session:
            result = session.run("SHOW DATABASES")
            databases = [record["name"] for record in result]
            print(f"利用可能なデータベース: {databases}")
            
            if database_name not in databases:
                print(f"⚠️  データベース '{database_name}' が存在しません")
                print("デフォルトの 'neo4j' データベースを使用します")
                database_name = "neo4j"
            else:
                print(f"✓ データベース '{database_name}' が存在します")
        
        # ステップ4: 指定データベースでの接続テスト
        print(f"4. データベース '{database_name}' での接続をテスト中...")
        with driver.session(database=database_name) as session:
            result = session.run("RETURN 1 as test")
            test_value = result.single()["test"]
            print(f"✓ データベース '{database_name}' での接続成功 (テスト値: {test_value})")
        
        driver.close()
        print("=== 接続テスト完了 ===\n")
        return True
        
    except Exception as e:
        print(f"❌ 接続エラー: {e}")
        print("\n=== 対処法 ===")
        print("1. Neo4jサーバーが起動しているか確認してください")
        print("2. 接続URIが正しいか確認してください (例: bolt://localhost:7687)")
        print("3. ユーザー名とパスワードが正しいか確認してください")
        print("4. ファイアウォール設定を確認してください")
        print("5. Neo4jのバージョンとドライバーの互換性を確認してください")
        print("\n=== 一般的な接続設定 ===")
        print("ローカルNeo4j: bolt://localhost:7687")
        print("Neo4j Aura: bolt://your-instance.neo4j.io:7687")
        print("ユーザー名: neo4j (デフォルト)")
        print("パスワード: インストール時に設定したパスワード")
        print("=== 接続テスト失敗 ===\n")
        return False


def test_connection_only():
    """Neo4j接続のみをテストする関数"""
    print("=== Neo4j接続テスト専用モード ===")
    
    if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
        print("❌ Neo4jの接続情報が.envファイルに設定されていません。")
        print("以下の環境変数を.envファイルに設定してください:")
        print("NEO4J_URI=bolt://localhost:7687")
        print("NEO4J_USERNAME=neo4j")
        print("NEO4J_PASSWORD=your_password")
        return False
    
    # 接続テストを実行
    success = test_neo4j_connection(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, "TreeSitterDB")
    
    if success:
        print("✅ 接続テスト成功！TreeSitterDBへの保存が可能です。")
    else:
        print("❌ 接続テスト失敗。上記の対処法を参考に設定を確認してください。")
    
    return success


def manage_treesitter_db():
    """TreeSitterDB管理機能"""
    if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
        print("❌ Neo4jの接続情報が.envファイルに設定されていません。")
        return False
    
    graph_builder = Neo4jGraphBuilder(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, database_name="TreeSitterDB")
    
    print("=== TreeSitterDB管理 ===")
    print("1. 統計情報を表示")
    print("2. データをクリア")
    print("3. 接続テスト")
    
    choice = input("選択してください (1-3): ").strip()
    
    if choice == "1":
        print("\n=== TreeSitterDB統計情報 ===")
        stats = graph_builder.get_treesitter_db_stats()
        if "error" not in stats:
            print("ノード数:")
            for label, count in stats["nodes"].items():
                print(f"  {label}: {count}個")
            
            print("\n関係数:")
            for rel_type, count in stats["relationships"].items():
                print(f"  {rel_type}: {count}個")
            
            print(f"\n関数数: {len(stats['functions'])}個")
            for func in stats["functions"][:5]:  # 最初の5個を表示
                print(f"  - {func['name']}: {func['description'][:50]}...")
        else:
            print(f"エラー: {stats['error']}")
    
    elif choice == "2":
        confirm = input("TreeSitterDBのデータをクリアしますか？ (y/N): ").strip().lower()
        if confirm == 'y':
            graph_builder.clear_treesitter_db()
        else:
            print("キャンセルしました。")
    
    elif choice == "3":
        test_neo4j_connection(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, "TreeSitterDB")
    
    else:
        print("無効な選択です。")
    
    return True


class PythonCodeAnalyzer:
    """Pythonコードの構文解析とグラフ構築を行うクラス"""
    
    def __init__(self, source_code: str):
        """初期化
        
        Args:
            source_code: 解析対象のPythonソースコード
        """
        self.source_code = source_code
        self.source_code_bytes = bytes(source_code, "utf8")
        
        # tree-sitterのセットアップ
        self.py_language = Language(tspython.language())
        self.parser = Parser(self.py_language)
        self.tree = self.parser.parse(self.source_code_bytes)
        
        # 抽出結果の格納
        self.graph_elements = {
            "functions": {},
            "classes": {},
            "calls": [],
            "parameter_descriptions": {}
        }
    
    def get_node_text(self, node: Node) -> str:
        """指定されたノードのテキストをソースコードから取得する"""
        return self.source_code_bytes[node.start_byte:node.end_byte].decode('utf8')
    
    def find_enclosing_scope(self, start_node: Node, scope_type: str) -> Optional[Node]:
        """指定されたノードから親をたどり、特定のスコープ（クラスや関数）を見つける"""
        current_node = start_node.parent
        while current_node:
            if current_node.type == scope_type:
                return current_node
            current_node = current_node.parent
        return None
    
    def debug_node_structure(self, node: Node, indent: int = 0) -> None:
        """ノードの構造をデバッグ出力する"""
        prefix = "  " * indent
        node_text = self.get_node_text(node)
        # 長いテキストは省略表示
        if len(node_text) > 50:
            node_text = node_text[:47] + "..."
        print(f"{prefix}{node.type}: '{node_text}' (start: {node.start_byte}, end: {node.end_byte})")
        for child in node.children:
            self.debug_node_structure(child, indent + 1)
    
    def extract_parameters_with_order(self, params_node: Node) -> List[Dict[str, Any]]:
        """パラメータノードから順序付きのパラメータリストを抽出
        
        Args:
            params_node: パラメータノード
            
        Returns:
            パラメータ情報のリスト
        """
        parameters = []
        if not params_node:
            return parameters
        
        print(f"パラメータノードの詳細構造:")
        self.debug_node_structure(params_node)
        
        # パラメータノードの子要素を順番に処理
        children = list(params_node.children)
        i = 0
        
        while i < len(children):
            child = children[i]
            print(f"処理中の子要素 {i}: {child.type} - '{self.get_node_text(child)}'")
            
            # 括弧やカンマは無視
            if child.type in [",", "(", ")"]:
                i += 1
                continue
            
            # パラメータの開始を検出
            if child.type == "identifier":
                # 通常のパラメータ（型ヒントなし）
                param_name = self.get_node_text(child)
                parameters.append(self._create_parameter_info(
                    param_name, None, False, len(parameters)
                ))
                print(f"  通常パラメータを追加: {param_name}")
                i += 1
                
            elif child.type == "typed_parameter":
                # 型ヒント付きパラメータ
                param_info = self._extract_typed_parameter(child)
                if param_info:
                    param_info["order"] = len(parameters)
                    parameters.append(param_info)
                    print(f"  型ヒント付きパラメータを追加: {param_info['name']} ({param_info['type_hint']})")
                i += 1
                
            elif child.type == "typed_default_parameter":
                # デフォルト値付き型ヒントパラメータ
                param_info = self._extract_typed_default_parameter(child)
                if param_info:
                    param_info["order"] = len(parameters)
                    param_info["is_optional"] = True
                    parameters.append(param_info)
                    print(f"  デフォルト値付きパラメータを追加: {param_info['name']} ({param_info['type_hint']}) [オプション]")
                i += 1
                
            else:
                print(f"  未処理の子要素タイプ: {child.type}")
                i += 1
        
        self._print_extracted_parameters(parameters)
        return parameters
    
    def _create_parameter_info(self, name: str, type_hint: Optional[str], 
                              is_optional: bool, order: int) -> Dict[str, Any]:
        """パラメータ情報辞書を作成"""
        return {
            "name": name,
            "order": order,
            "type": "parameter",
            "type_hint": type_hint,
            "description": "",
            "is_optional": is_optional
        }
    
    def _extract_typed_parameter(self, node: Node) -> Optional[Dict[str, Any]]:
        """型ヒント付きパラメータを抽出"""
        print(f"  typed_parameterの子要素:")
        for j, subchild in enumerate(node.children):
            print(f"    {j}: {subchild.type} - '{self.get_node_text(subchild)}'")
        
        # 子要素の構造を確認
        children = list(node.children)
        
        # 基本的な構造: identifier, :, type
        if len(children) >= 3:
            name_node = children[0]  # identifier (パラメータ名)
            colon_node = children[1]  # :
            type_node = children[2]   # type (型)
            
            if (name_node.type == "identifier" and 
                colon_node.type == ":" and 
                type_node.type == "type"):
                
                param_name = self.get_node_text(name_node)
                type_hint = self.get_node_text(type_node)
                return self._create_parameter_info(param_name, type_hint, False, 0)
        
        # より複雑な構造の場合
        param_name = None
        type_hint = None
        
        for child in children:
            if child.type == "identifier":
                param_name = self.get_node_text(child)
            elif child.type == "type":
                type_hint = self.get_node_text(child)
        
        if param_name:
            return self._create_parameter_info(param_name, type_hint, False, 0)
        
        return None
    
    def _extract_typed_default_parameter(self, node: Node) -> Optional[Dict[str, Any]]:
        """デフォルト値付き型ヒントパラメータを抽出"""
        print(f"  typed_default_parameterの子要素:")
        for j, subchild in enumerate(node.children):
            print(f"    {j}: {subchild.type} - '{self.get_node_text(subchild)}'")
        
        # 子要素の構造を確認
        children = list(node.children)
        
        # 基本的な構造: identifier, :, type, =, default_value
        if len(children) >= 5:
            name_node = children[0]      # identifier (パラメータ名)
            colon_node = children[1]     # :
            type_node = children[2]      # type (型)
            equals_node = children[3]    # =
            default_node = children[4]   # default_value
            
            if (name_node.type == "identifier" and 
                colon_node.type == ":" and 
                type_node.type == "type" and
                equals_node.type == "="):
                
                param_name = self.get_node_text(name_node)
                type_hint = self.get_node_text(type_node)
                return self._create_parameter_info(param_name, type_hint, True, 0)
        
        # より複雑な構造の場合
        param_name = None
        type_hint = None
        
        for child in children:
            if child.type == "identifier":
                param_name = self.get_node_text(child)
            elif child.type == "type":
                type_hint = self.get_node_text(child)
        
        if param_name:
            return self._create_parameter_info(param_name, type_hint, True, 0)
        
        return None
    
    def _print_extracted_parameters(self, parameters: List[Dict[str, Any]]) -> None:
        """抽出されたパラメータを出力"""
        print(f"\n=== 抽出されたパラメータ情報 ===")
        print(f"パラメータ数: {len(parameters)}")
        for i, param in enumerate(parameters):
            type_info = f" ({param['type_hint']})" if param['type_hint'] else ""
            optional_info = " [オプション]" if param['is_optional'] else ""
            desc_info = f" - {param['description']}" if param['description'] else ""
            print(f"  {i+1}. {param['name']}{type_info}{optional_info}{desc_info} (順序: {param['order']})")
        print("=" * 40)
    
    def extract_docstring_info(self, body_node: Node, current_func_name: str = None) -> Tuple[str, str, str, str]:
        """docstringから情報を抽出
        
        Args:
            body_node: 関数のbodyノード
            current_func_name: 現在処理中の関数名
            
        Returns:
            (description, return_type, return_description, full_docstring)
        """
        description = ""
        return_type = ""
        return_description = ""
        full_docstring = ""
        
        if body_node and body_node.children:
            first_child = body_node.children[0]
            if first_child.type == "expression_statement":
                expr = first_child.children[0]
                if expr.type == "string":
                    full_docstring = self.get_node_text(expr).strip('"\'')
                    description, return_type, return_description = self._parse_docstring(full_docstring, current_func_name)
        
        return description, return_type, return_description, full_docstring
    
    def _parse_docstring(self, docstring: str, current_func_name: str = None) -> Tuple[str, str, str]:
        """docstringを解析して情報を抽出"""
        description = ""
        return_type = ""
        return_description = ""
        
        print(f"DEBUG: 完全なdocstring: '{docstring}'")
        lines = docstring.split('\n')
        print(f"DEBUG: docstringの行数: {len(lines)}")
        
        in_args_section = False
        in_returns_section = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            print(f"DEBUG: 行 {i}: '{line}'")
            if not line:
                continue
            
            # 関数の説明を取得
            if not description and not line.startswith('Args:') and not line.startswith('Returns:'):
                description = line
            
            # Argsセクションの開始
            elif line.startswith('Args:'):
                in_args_section = True
                in_returns_section = False
                continue
            
            # Returnsセクションの開始
            elif line.startswith('Returns:'):
                in_args_section = False
                in_returns_section = True
                continue
            
            # パラメータの説明を抽出
            elif in_args_section and line and not line.startswith('Args:') and not line.startswith('Returns:'):
                self._process_parameter_line(line, current_func_name)
            
            # 戻り値の情報を抽出
            elif in_returns_section and line and not line.startswith('Args:') and not line.startswith('Returns:'):
                return_type, return_description = self._process_return_line(line)
        
        return description, return_type, return_description
    
    def _process_parameter_line(self, line: str, current_func_name: str = None) -> None:
        """パラメータ行を処理"""
        param_line = line.strip()
        print(f"DEBUG: パラメータ行: '{param_line}'")
        
        if ':' in param_line:
            # 型情報を含む場合: "VariableName (str): 説明"
            if '(' in param_line and ')' in param_line:
                # 型情報を除去してパラメータ名を取得
                param_part = param_line.split(':', 1)[0]
                param_name = param_part.split('(')[0].strip()
                param_desc = param_line.split(':', 1)[1].strip()
            else:
                param_name, param_desc = param_line.split(':', 1)
                param_name = param_name.strip()
                param_desc = param_desc.strip()
            
            print(f"DEBUG: 抽出されたパラメータ名: '{param_name}', 説明: '{param_desc}'")
            
            # 対応するパラメータに説明を設定
            found_param = False
            for func_name, func_info in self.graph_elements["functions"].items():
                for param in func_info.get("parameters", []):
                    if param['name'] == param_name:
                        param['description'] = param_desc
                        print(f"DEBUG: パラメータ '{param_name}' に説明を設定")
                        found_param = True
                        break
                if found_param:
                    break
            
            # パラメータ説明を独立したノードとして管理（重複を避ける）
            if current_func_name:
                param_desc_id = f"{current_func_name}_{param_name}_description"
                self.graph_elements["parameter_descriptions"][param_desc_id] = {
                    "function_name": current_func_name,
                    "parameter_name": param_name,
                    "description": param_desc
                }
    
    def _process_return_line(self, line: str) -> Tuple[str, str]:
        """戻り値行を処理"""
        return_info = line.strip()
        return_type = ""
        return_description = ""
        
        if ':' in return_info:
            return_type, return_desc = return_info.split(':', 1)
            return_type = return_type.strip()
            return_description = return_desc.strip()
        else:
            return_type = return_info
            return_description = ""
        
        return return_type, return_description
    
    def extract_graph_elements(self) -> Dict[str, Any]:
        """tree-sitterの構文木を解析し、グラフ構築に適した形式の辞書を返す"""
        
        # 関数とクラスの定義を抽出
        self._extract_definitions()
        
        # 関数/メソッド呼び出しを抽出
        self._extract_calls()
        
        return self.graph_elements
    
    def _extract_definitions(self) -> None:
        """関数とクラスの定義を抽出"""
        defs_query_string = """
        (class_definition name: (identifier) @class.name) @class.definition

        (function_definition
          name: (identifier) @function.name
          parameters: (parameters) @function.params
        ) @function.definition
        
        ; より詳細なパラメータ情報を取得するためのクエリ
        (function_definition
          name: (identifier) @function.name
          parameters: (parameters . (identifier) @param.name)
        ) @function.definition
        
        ; 型ヒント付きパラメータを取得
        (function_definition
          name: (identifier) @function.name
          parameters: (parameters . (typed_parameter) @typed.param)
        ) @function.definition
        
        ; デフォルト値付きパラメータを取得
        (function_definition
          name: (identifier) @function.name
          parameters: (parameters . (typed_default_parameter) @default.param)
        ) @function.definition
        """
        defs_query = Query(self.py_language, defs_query_string)
        cursor = QueryCursor(defs_query)
        defs_captures = cursor.captures(self.tree.root_node)
        
        # パラメータを一時的に格納する辞書
        func_params = defaultdict(list)
        
        # 最初に全てのキャプチャをリストに変換して複数回ループできるようにする
        all_captures = []
        for capture_name, nodes in defs_captures.items():
            for node in nodes:
                all_captures.append((node, capture_name))

        # 1回目のループ: パラメータを収集
        for node, capture_name in all_captures:
            if capture_name == "param.name":
                param_name = self.get_node_text(node)
                func_def_node = self.find_enclosing_scope(node, "function_definition")
                if func_def_node:
                    func_name_node = func_def_node.child_by_field_name("name")
                    if func_name_node:
                        func_name = self.get_node_text(func_name_node)
                        func_params[func_name].append(param_name)

        # 2回目のループ: 関数とクラスの定義を処理
        for node, capture_name in all_captures:
            if capture_name == "class.definition":
                self._process_class_definition(node)
            elif capture_name == "function.definition":
                self._process_function_definition(node, func_params)
    
    def _process_class_definition(self, node: Node) -> None:
        """クラス定義を処理"""
        name_node = node.child_by_field_name("name")
        if name_node:
            class_name = self.get_node_text(name_node)
            self.graph_elements["classes"][class_name] = {"source": self.get_node_text(node)}
    
    def _process_function_definition(self, node: Node, func_params: Dict[str, List[str]]) -> None:
        """関数定義を処理"""
        name_node = node.child_by_field_name("name")
        if name_node:
            func_name = self.get_node_text(name_node)
            
            # 辞書にまだ存在しない場合のみ追加（重複処理を避ける）
            if func_name not in self.graph_elements["functions"]:
                # クラス情報を取得
                class_name = self._get_enclosing_class_name(node)
                
                # パラメータの詳細情報を抽出
                params_node = node.child_by_field_name("parameters")
                parameters = self.extract_parameters_with_order(params_node)
                
                # docstringの抽出と構造化
                body_node = node.child_by_field_name("body")
                description, return_type, return_description, _ = self.extract_docstring_info(body_node)
                
                # パラメータ説明を独立したノードとして管理
                self._create_parameter_descriptions(func_name, parameters)
                
                # 関数情報を保存
                self.graph_elements["functions"][func_name] = {
                    "class_name": class_name,
                    "source": self.get_node_text(node),
                    "parameters": parameters,
                    "description": description,
                    "return_type": return_type,
                    "return_description": return_description
                }
    
    def _get_enclosing_class_name(self, node: Node) -> Optional[str]:
        """関数が属するクラス名を取得"""
        enclosing_class_node = self.find_enclosing_scope(node, "class_definition")
        if enclosing_class_node:
            class_name_node = enclosing_class_node.child_by_field_name("name")
            if class_name_node:
                return self.get_node_text(class_name_node)
        return None
    
    def _create_parameter_descriptions(self, func_name: str, parameters: List[Dict[str, Any]]) -> None:
        """パラメータ説明を独立したノードとして管理"""
        for param in parameters:
            if param['description']:
                param_desc_id = f"{func_name}_{param['name']}_description"
                self.graph_elements["parameter_descriptions"][param_desc_id] = {
                    "function_name": func_name,
                    "parameter_name": param['name'],
                    "description": param['description']
                }
    
    def _extract_calls(self) -> None:
        """関数/メソッド呼び出しを抽出"""
        calls_query_string = """
        (call
          function: [
            (identifier) @call.name
            (attribute attribute: (identifier) @call.name)
          ]
        ) @call.expression
        """
        calls_query = Query(self.py_language, calls_query_string)
        calls_cursor = QueryCursor(calls_query)
        calls_captures = calls_cursor.captures(self.tree.root_node)

        for capture_name, nodes in calls_captures.items():
            for node in nodes:
                if capture_name == "call.name":
                    callee_name = self.get_node_text(node)
                    enclosing_func_node = self.find_enclosing_scope(node, "function_definition")
                    if enclosing_func_node:
                        caller_name_node = enclosing_func_node.child_by_field_name("name")
                        if caller_name_node:
                            caller_name = self.get_node_text(caller_name_node)
                            self.graph_elements["calls"].append((caller_name, callee_name))


class Neo4jGraphBuilder:
    """Neo4jにグラフを構築するクラス"""
    
    def __init__(self, uri: str, username: str, password: str, database_name: str = "neo4j"):
        """初期化
        
        Args:
            uri: Neo4jのURI
            username: ユーザー名
            password: パスワード
            database_name: 使用するデータベース名（デフォルト: "neo4j"）
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.database_name = database_name
    
    def create_code_graph(self, graph_elements: Dict[str, Any]) -> None:
        """抽出した情報からNeo4jにグラフを構築する"""
        driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        
        # データベースの存在確認と作成
        self._ensure_database_exists(driver)
        
        with driver.session(database=self.database_name) as session:
            # 既存のグラフをクリア
            session.run("MATCH (n) DETACH DELETE n")
            print("既存のグラフをクリアしました。")

            # クラスノードを作成
            self._create_class_nodes(session, graph_elements["classes"])

            # 関数ノードとパラメータ関係を作成
            self._create_function_nodes(session, graph_elements["functions"])

            # パラメータ説明を独立したノードとして作成
            self._create_parameter_description_nodes(session, graph_elements["parameter_descriptions"])

            # 呼び出し関係を作成
            self._create_call_relationships(session, graph_elements["calls"])

            print("\nNeo4jの知識グラフ構築が完了しました。")
            
            # 作成されたグラフの構造を確認
            self._display_graph_structure(session)
        
        driver.close()
    
    def _ensure_database_exists(self, driver) -> None:
        """データベースの存在確認と作成"""
        try:
            # データベース名を小文字に統一（Neo4jの仕様）
            self.database_name = self.database_name.lower()
            
            # システムデータベースでデータベース一覧を確認
            with driver.session(database="system") as session:
                result = session.run("SHOW DATABASES")
                databases = [record["name"] for record in result]
                
                if self.database_name not in databases:
                    print(f"データベース '{self.database_name}' を作成しています...")
                    session.run(f"CREATE DATABASE {self.database_name}")
                    print(f"データベース '{self.database_name}' が作成されました。")
                else:
                    print(f"データベース '{self.database_name}' は既に存在します。")
        except Exception as e:
            print(f"データベース確認中にエラーが発生しました: {e}")
            print("エラーの詳細:")
            import traceback
            traceback.print_exc()
            print("デフォルトの 'neo4j' データベースを使用します。")
            self.database_name = "neo4j"
    
    def _create_class_nodes(self, session, classes: Dict[str, Any]) -> None:
        """クラスノードを作成"""
        for class_name in classes:
            session.run("MERGE (c:Class {name: $name})", name=class_name)
        print(f"{len(classes)}個のクラスノードを作成しました。")
    
    def _create_function_nodes(self, session, functions: Dict[str, Any]) -> None:
        """関数ノードとパラメータ関係を作成"""
        for func_name, details in functions.items():
            # 関数ノードを作成
            description = details.get("description", "")
            return_type = details.get("return_type", "")
            return_description = details.get("return_description", "")
            
            session.run("""
                MERGE (f:Function {name: $name})
                SET f.description = $description, f.return_type = $return_type, f.return_description = $return_description
            """, name=func_name, description=description, return_type=return_type, return_description=return_description)
            
            # パラメータを個別のノードとして作成し、関数との関係を表現
            parameters = details.get("parameters", [])
            for param_info in parameters:
                self._create_parameter_node(session, func_name, param_info)
            
            # クラスとの関係を作成
            if details.get("class_name"):
                session.run("""
                    MATCH (f:Function {name: $func_name})
                    MATCH (c:Class {name: $class_name})
                    MERGE (f)-[:PART_OF]->(c)
                """, func_name=func_name, class_name=details["class_name"])
        
        print(f"{len(functions)}個の関数ノードとパラメータ関係を作成しました。")
    
    def _create_parameter_node(self, session, func_name: str, param_info: Dict[str, Any]) -> None:
        """パラメータノードを作成"""
        param_name = param_info["name"]
        param_order = param_info["order"]
        type_hint = param_info.get("type_hint", "")
        is_optional = param_info.get("is_optional", False)
        
        # パラメータノードを作成
        session.run("""
            MERGE (p:Parameter {name: $param_name})
            SET p.order = $param_order, p.type_hint = $type_hint, p.is_optional = $is_optional
        """, param_name=param_name, param_order=param_order, type_hint=type_hint, is_optional=is_optional)
        
        # 関数とパラメータの関係を作成
        session.run("""
            MATCH (f:Function {name: $func_name})
            MATCH (p:Parameter {name: $param_name})
            MERGE (f)-[:HAS_PARAMETER {order: $param_order}]->(p)
        """, func_name=func_name, param_name=param_name, param_order=param_order)
    
    def _create_parameter_description_nodes(self, session, parameter_descriptions: Dict[str, Any]) -> None:
        """パラメータ説明を独立したノードとして作成"""
        for desc_id, desc_info in parameter_descriptions.items():
            session.run("""
                MERGE (d:ParameterDescription {id: $desc_id})
                SET d.function_name = $func_name, d.parameter_name = $param_name, d.description = $description
            """, desc_id=desc_id, func_name=desc_info["function_name"], 
                 param_name=desc_info["parameter_name"], description=desc_info["description"])
            
            # パラメータ説明とパラメータの関係を作成
            session.run("""
                MATCH (d:ParameterDescription {id: $desc_id})
                MATCH (p:Parameter {name: $param_name})
                MERGE (d)-[:DESCRIBES]->(p)
            """, desc_id=desc_id, param_name=desc_info["parameter_name"])
        
        print(f"{len(parameter_descriptions)}個のパラメータ説明ノードを作成しました。")
    
    def _create_call_relationships(self, session, calls: List[Tuple[str, str]]) -> None:
        """呼び出し関係を作成"""
        for caller, callee in calls:
            session.run("""
                MATCH (caller:Function {name: $caller_name})
                MATCH (callee:Function {name: $callee_name})
                MERGE (caller)-[:CALLS]->(callee)
            """, caller_name=caller, callee_name=callee)
        print(f"{len(calls)}個の呼び出し関係を作成しました。")
    
    def _display_graph_structure(self, session) -> None:
        """作成されたグラフの構造を表示"""
        print(f"\n=== TreeSitterDB '{self.database_name}' のグラフ構造 ===")
        
        # ノード数の確認
        result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count")
        print("ノード数:")
        for record in result:
            labels = record["labels"]
            count = record["count"]
            print(f"  {labels}: {count}個")
        
        # 関係数の確認
        result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")
        print("\n関係数:")
        for record in result:
            rel_type = record["type"]
            count = record["count"]
            print(f"  {rel_type}: {count}個")
        
        # サンプルデータの表示
        print("\n=== サンプルデータ ===")
        
        # クラスの例
        result = session.run("MATCH (c:Class) RETURN c.name as name LIMIT 3")
        print("クラス:")
        for record in result:
            print(f"  - {record['name']}")
        
        # 関数の例
        result = session.run("""
            MATCH (f:Function) 
            RETURN f.name as name, f.description as description 
            LIMIT 3
        """)
        print("\n関数:")
        for record in result:
            name = record['name']
            description = record['description'][:50] + "..." if len(record['description']) > 50 else record['description']
            print(f"  - {name}: {description}")
        
        # パラメータの例
        result = session.run("""
            MATCH (p:Parameter) 
            RETURN p.name as name, p.type_hint as type_hint, p.is_optional as is_optional 
            LIMIT 3
        """)
        print("\nパラメータ:")
        for record in result:
            name = record['name']
            type_hint = record['type_hint']
            is_optional = record['is_optional']
            print(f"  - {name}: {type_hint} (オプション: {is_optional})")
        
        print(f"\n=== TreeSitterDB '{self.database_name}' のグラフ構造確認完了 ===")
    
    def save_to_treesitter_db(self, graph_elements: Dict[str, Any]) -> None:
        """TreeSitterDBにデータを保存する専用メソッド"""
        print(f"TreeSitterDB '{self.database_name}' にデータを保存しています...")
        self.create_code_graph(graph_elements)
        print(f"TreeSitterDB '{self.database_name}' への保存が完了しました。")
    
    def clear_treesitter_db(self) -> None:
        """TreeSitterDBのデータをクリアする"""
        driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        
        try:
            with driver.session(database=self.database_name) as session:
                session.run("MATCH (n) DETACH DELETE n")
                print(f"TreeSitterDB '{self.database_name}' のデータをクリアしました。")
        except Exception as e:
            print(f"データクリア中にエラーが発生しました: {e}")
        finally:
            driver.close()
    
    def get_treesitter_db_stats(self) -> Dict[str, Any]:
        """TreeSitterDBの統計情報を取得する"""
        driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        stats = {}
        
        try:
            with driver.session(database=self.database_name) as session:
                # ノード数の統計
                result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count")
                node_stats = {}
                for record in result:
                    labels = record["labels"]
                    count = record["count"]
                    node_stats[str(labels)] = count
                stats["nodes"] = node_stats
                
                # 関係数の統計
                result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")
                relationship_stats = {}
                for record in result:
                    rel_type = record["type"]
                    count = record["count"]
                    relationship_stats[rel_type] = count
                stats["relationships"] = relationship_stats
                
                # 関数一覧
                result = session.run("MATCH (f:Function) RETURN f.name as name, f.description as description")
                functions = []
                for record in result:
                    functions.append({
                        "name": record["name"],
                        "description": record["description"]
                    })
                stats["functions"] = functions
                
        except Exception as e:
            print(f"統計情報取得中にエラーが発生しました: {e}")
            stats = {"error": str(e)}
        finally:
            driver.close()
        
        return stats


def main():
    """メイン処理"""
    # サンプルとなるPythonコード
    source_code = """
from typing import Literal, Union, Optional

def CreateVariable(
    VariableName: str, 
    VariableValue: float, 
    VariableUnit: Literal["mm", "cm", "m", "in", "ft", "pt", "deg", "rad", "", "num"], 
    VariableElementGroup: str = ""
) -> str:
    \"\"\"
    変数要素の作成
    
    Args:
        VariableName (str): 作成する変数名称（空文字不可）
            - 変数の識別子として使用される
            - 例: "LENGTH", "ANGLE1", "THICKNESS"
        VariableValue (float): 変数の値（浮動小数点）
            - 数値として設定する値
            - 例: 100.0, 45.5, 0.001
        VariableUnit (Literal): 変数単位（必須）
            - "mm": ミリメートル
            - "cm": センチメートル  
            - "m": メートル
            - "in": インチ
            - "ft": フィート
            - "pt": ポイント
            - "deg": 度
            - "rad": ラジアン
            - "": 単位なし
            - "num": 数値
        VariableElementGroup (str, optional): 要素グループ（空文字可）
            - 変数を格納する要素グループ名
            - 階層構造は "/" で区切る（例: "GROUP1/SUBGROUP1"）
            - 空文字の場合はデフォルトグループに格納
    
    Returns:
        str: 作成された変数要素の要素ID
            - 形式: "ID@xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            - 例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"
    
    Raises:
        ValueError: VariableNameが空文字の場合
        ValueError: VariableUnitが無効な値の場合
    
    Example:
        >>> var_id = CreateVariable("LENGTH", 100.0, "mm", "DIMENSIONS")
        >>> print(var_id)  # "ID@xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    \"\"\"
    pass

def CreateSketchPlane(
    ElementName: str = "", 
    ElementGroup: str = "", 
    PlaneDef: str = "", 
    PlaneOffset: Union[str, float] = "", 
    bRevPlane: bool = False, 
    bRevUV: bool = False, 
    StyleName: str = "", 
    OriginPoint: str = "", 
    AxisDirection: str = "", 
    bDefAxisIsX: bool = True, 
    bUpdate: bool = False
) -> str:
    \"\"\"
    スケッチ平面の作成
    
    Args:
        ElementName (str, optional): 作成するスケッチ平面名称（空文字可）
            - スケッチ平面の識別名
            - 例: "SKETCH_PLANE_1", "FRONT_PLANE"
        ElementGroup (str, optional): 要素グループ（空文字可）
            - スケッチ平面を格納する要素グループ名
            - 階層構造は "/" で区切る
        PlaneDef (str): 平面定義（必須）
            - 書式: "PL,基準平面[,オフセット,方向]"
            - 例: "PL,Z" (グローバルXY平面)
            - 例: "PL,O,500.0,X" (グローバルYZ平面をX方向に500移動)
            - 基準平面: "X"(グローバルYZ), "Y"(グローバルZX), "Z"(グローバルXY)
        PlaneOffset (Union[str, float], optional): 平面からのオフセット距離（空文字可）
            - 数値、変数要素名、式文字列で指定
            - 例: "100.0", "L1", "L1 / 2.0"
        bRevPlane (bool): スケッチ平面を反転するかどうかのフラグ
            - True: 平面を反転
            - False: 平面を反転しない（デフォルト）
        bRevUV (bool): スケッチ平面のX,Y軸を交換するかどうかのフラグ
            - True: X,Y軸を交換
            - False: 軸を交換しない（デフォルト）
        StyleName (str, optional): 注記スタイル名称（空文字可）
            - EVO.SHIPに設定されている注記スタイルの名称
        OriginPoint (str, optional): スケッチ平面の原点（空文字可）
            - 書式: "x,y,z" または "x,y" (2Dの場合)
            - 例: "0.0,0.0,0.0", "FRM1,0.0,1000.0"
        AxisDirection (str, optional): スケッチ平面の軸方向（空文字可）
            - 方向指定: "+X", "-X", "+Y", "-Y", "+Z", "-Z"
            - または数値ベクトル: "1.0,0.0,0.0"
        bDefAxisIsX (bool): スケッチ平面のX軸を指定する場合はTrue
            - True: 指定した方向をX軸とする
            - False: 指定した方向をY軸とする（デフォルト）
        bUpdate (bool): 更新フラグ（未実装、使用しない）
            - 常にFalseを指定
    
    Returns:
        str: 作成されたスケッチ平面要素の要素ID
            - 形式: "ID@xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            - 作成される要素: スケッチ平面要素
    
    Raises:
        ValueError: PlaneDefが無効な形式の場合
        ValueError: PlaneOffsetが無効な値の場合
        ValueError: OriginPointが無効な座標の場合
    
    Example:
        >>> plane_id = CreateSketchPlane(
        ...     ElementName="FRONT_PLANE",
        ...     ElementGroup="SKETCHES",
        ...     PlaneDef="PL,Z",
        ...     PlaneOffset="100.0"
        ... )
        >>> print(plane_id)  # "ID@xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    \"\"\"
    pass
"""

    print("--- ステップ1: コード構造の解析 ---")
    analyzer = PythonCodeAnalyzer(source_code)
    graph_elements = analyzer.extract_graph_elements()
    
    print("抽出されたグラフ要素:")
    print(json.dumps(graph_elements, indent=2, ensure_ascii=False))
    print("-" * 20)

    print("\n--- ステップ2: Neo4jへのグラフ構築 ---")
    if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
        print("Neo4jの接続情報が.envファイルに設定されていません。グラフ構築をスキップします。")
        print("以下の環境変数を.envファイルに設定してください:")
        print("NEO4J_URI=bolt://localhost:7687")
        print("NEO4J_USERNAME=neo4j")
        print("NEO4J_PASSWORD=your_password")
    else:
        # 接続テストを実行
        if test_neo4j_connection(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, "TreeSitterDB"):
            try:
                # グラフ構築を実行（TreeSitterDBデータベースに保存）
                graph_builder = Neo4jGraphBuilder(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, database_name="TreeSitterDB")
                # TreeSitterDB専用メソッドを使用
                graph_builder.save_to_treesitter_db(graph_elements)
                
                # 保存後の統計情報を表示
                print("\n=== TreeSitterDB保存後の統計 ===")
                stats = graph_builder.get_treesitter_db_stats()
                if "error" not in stats:
                    total_nodes = sum(stats["nodes"].values())
                    total_relationships = sum(stats["relationships"].values())
                    print(f"総ノード数: {total_nodes}")
                    print(f"総関係数: {total_relationships}")
                    print(f"保存された関数数: {len(stats['functions'])}")
                else:
                    print(f"統計情報取得エラー: {stats['error']}")
                    
            except Exception as e:
                print(f"グラフ構築中にエラーが発生しました: {e}")
                print("詳細なエラー情報:")
                import traceback
                traceback.print_exc()
        else:
            print("接続テストに失敗したため、グラフ構築をスキップします。")
            print("上記の対処法を参考に、Neo4jの接続設定を確認してください。")


if __name__ == "__main__":
    import sys
    
    # コマンドライン引数で接続テスト専用モードを選択
    if len(sys.argv) > 1 and sys.argv[1] == "--test-connection":
        test_connection_only()
    elif len(sys.argv) > 1 and sys.argv[1] == "--manage-db":
        manage_treesitter_db()
    else:
        main()