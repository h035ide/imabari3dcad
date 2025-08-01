#%%
import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query, Node, QueryCursor
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import json
from collections import defaultdict

# .envファイルから環境変数を読み込む
load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
# auth = (username, password)
# --------------------------------

# 1. サンプルとなるPythonコード
source_code = """
def CreateVariable(VariableName: str, VariableValue: float, VariableUnit: str, VariableElementGroup: str = ""):
    \"\"\"
    変数要素の作成
    
    Args:
        VariableName (str): 作成する変数名称（空文字不可）
        VariableValue (float): 変数の値（浮動小数点）
        VariableUnit (str): 変数単位（"mm", "cm", "m", "in", "ft", "pt", "deg", "rad", "", "num"のいずれか）
        VariableElementGroup (str, optional): 要素グループ（空文字可）
    
    Returns:
        str: 作成された変数要素の要素ID
    \"\"\"
    pass

def CreateSketchPlane(ElementName: str = "", ElementGroup: str = "", PlaneDef: str = "", PlaneOffset: str = "", bRevPlane: bool = False, bRevUV: bool = False, StyleName: str = "", OriginPoint: str = "", AxisDirection: str = "", bDefAxisIsX: bool = True, bUpdate: bool = False):
    \"\"\"
    スケッチ平面の作成
    
    Args:
        ElementName (str, optional): 作成するスケッチ平面名称（空文字可）
        ElementGroup (str, optional): 要素グループ（空文字可）
        PlaneDef (str): 平面（"PL,Z"など）
        PlaneOffset (str): 平面からのオフセット距離（長さ）
        bRevPlane (bool): スケッチ平面を反転するかどうかのフラグ
        bRevUV (bool): スケッチ平面のX,Y軸を交換するかどうかのフラグ
        StyleName (str, optional): 注記スタイル名称（空文字可）
        OriginPoint (str, optional): スケッチ平面の原点（空文字可）
        AxisDirection (str, optional): スケッチ平面の軸方向（空文字可）
        bDefAxisIsX (bool): スケッチ平面のX軸を指定する場合はTrue
        bUpdate (bool): 更新フラグ（未実装、使用しない）
    
    Returns:
        str: 作成されたスケッチ平面要素の要素ID
    \"\"\"
    pass
"""

# 2. tree-sitterのパーサーをセットアップ
PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)
tree = parser.parse(bytes(source_code, "utf8"))
source_code_bytes = bytes(source_code, "utf8")

def get_node_text(node: Node) -> str:
    """指定されたノードのテキストをソースコードから取得するヘルパー関数"""
    return source_code_bytes[node.start_byte:node.end_byte].decode('utf8')

def find_enclosing_scope(start_node: Node, scope_type: str):
    """指定されたノードから親をたどり、特定のスコープ（クラスや関数）を見つける"""
    current_node = start_node.parent
    while current_node:
        if current_node.type == scope_type:
            return current_node
        current_node = current_node.parent
    return None

def extract_graph_elements(tree: Node):
    """
    tree-sitterの構文木を解析し、グラフ構築に適した形式の辞書を返す
    """
    graph_elements = {
        "functions": {},
        "classes": {},
        "calls": []
    }

    # ★★★ ステップ1: Tree-sitterクエリの拡張 ★★★
    # パラメータをキャプチャするクエリを追加
    defs_query_string = """
    (class_definition name: (identifier) @class.name) @class.definition

    (function_definition
      name: (identifier) @function.name
      parameters: (parameters . (identifier) @param.name)
    ) @function.definition
    
    ; パラメータがない関数定義もキャプチャするためのルール
    (function_definition
      name: (identifier) @function.name
    ) @function.definition
    
    ; より詳細なパラメータ情報を取得するためのクエリ
    (function_definition
      name: (identifier) @function.name
      parameters: (parameters) @function.params
    ) @function.definition
    """
    defs_query = Query(PY_LANGUAGE, defs_query_string)
    cursor = QueryCursor(defs_query)
    defs_captures = cursor.captures(tree.root_node)

    # ★★★ ステップ2: データ抽出ロジックの修正 ★★★
    # パラメータの詳細情報を抽出する関数
    def extract_parameters_with_order(params_node):
        """パラメータノードから順序付きのパラメータリストを抽出"""
        parameters = []
        if params_node:
            print(f"パラメータノードの子要素:")
            for i, child in enumerate(params_node.children):
                print(f"  {i}: {child.type} - {get_node_text(child)}")
                if child.type == "identifier":
                    param_name = get_node_text(child)
                    parameters.append({
                        "name": param_name,
                        "order": len(parameters),  # 実際のパラメータの順序
                        "type": "parameter",
                        "type_hint": None,
                        "description": "",
                        "is_optional": False
                    })
                elif child.type == "typed_parameter":
                    # 型ヒント付きパラメータの処理
                    name_node = child.child_by_field_name("name")
                    type_node = child.child_by_field_name("type")
                    if name_node and type_node:
                        param_name = get_node_text(name_node)
                        type_hint = get_node_text(type_node)
                        parameters.append({
                            "name": param_name,
                            "order": len(parameters),
                            "type": "parameter",
                            "type_hint": type_hint,
                            "description": "",
                            "is_optional": False
                        })
                elif child.type == "typed_default_parameter":
                    # デフォルト値付き型ヒントパラメータの処理
                    name_node = child.child_by_field_name("name")
                    type_node = child.child_by_field_name("type")
                    if name_node and type_node:
                        param_name = get_node_text(name_node)
                        type_hint = get_node_text(type_node)
                        # デフォルト値がある場合はオプショナル
                        is_optional = True
                        parameters.append({
                            "name": param_name,
                            "order": len(parameters),
                            "type": "parameter",
                            "type_hint": type_hint,
                            "description": "",
                            "is_optional": is_optional
                        })
        return parameters
    
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
            param_name = get_node_text(node)
            func_def_node = find_enclosing_scope(node, "function_definition")
            if func_def_node:
                func_name_node = func_def_node.child_by_field_name("name")
                if func_name_node:
                    func_name = get_node_text(func_name_node)
                    func_params[func_name].append(param_name)

    # 2回目のループ: 関数とクラスの定義を処理し、収集したパラメータをマージ
    for node, capture_name in all_captures:
        if capture_name == "class.definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                class_name = get_node_text(name_node)
                graph_elements["classes"][class_name] = {"source": get_node_text(node)}
        elif capture_name == "function.definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                func_name = get_node_text(name_node)
                # 辞書にまだ存在しない場合のみ追加（重複処理を避ける）
                if func_name not in graph_elements["functions"]:
                    enclosing_class_node = find_enclosing_scope(node, "class_definition")
                    class_name = None
                    if enclosing_class_node:
                        class_name_node = enclosing_class_node.child_by_field_name("name")
                        if class_name_node:
                            class_name = get_node_text(class_name_node)
                    
                    # パラメータの詳細情報を抽出
                    params_node = node.child_by_field_name("parameters")
                    parameters = extract_parameters_with_order(params_node)
                    
                    # docstringの抽出と構造化
                    docstring = ""
                    description = ""
                    return_type = ""
                    return_description = ""
                    body_node = node.child_by_field_name("body")
                    if body_node and body_node.children:
                        first_child = body_node.children[0]
                        if first_child.type == "expression_statement":
                            expr = first_child.children[0]
                            if expr.type == "string":
                                full_docstring = get_node_text(expr).strip('"\'')
                                docstring = full_docstring
                                
                                # docstringから情報を抽出
                                print(f"DEBUG: 完全なdocstring: '{full_docstring}'")
                                lines = full_docstring.split('\n')
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
                                    elif in_args_section and line.startswith('    '):
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
                                            for param in parameters:
                                                if param['name'] == param_name:
                                                    param['description'] = param_desc
                                                    print(f"DEBUG: パラメータ '{param_name}' に説明を設定")
                                                    break
                                    
                                    # 戻り値の情報を抽出
                                    elif in_returns_section and line.startswith('    '):
                                        return_info = line.strip()
                                        if ':' in return_info:
                                            return_type, return_desc = return_info.split(':', 1)
                                            return_type = return_type.strip()
                                            return_description = return_desc.strip()
                                        else:
                                            return_type = return_info
                                            return_description = ""
                    
                    graph_elements["functions"][func_name] = {
                        "class_name": class_name,
                        "source": get_node_text(node),
                        "parameters": parameters,  # 詳細なパラメータ情報を追加
                        "description": description,  # 関数の説明
                        "return_type": return_type,  # 戻り値の型
                        "return_description": return_description # 戻り値の説明
                    }

    # --- 関数/メソッド呼び出しの抽出 ---
    calls_query_string = """
    (call
      function: [
        (identifier) @call.name
        (attribute attribute: (identifier) @call.name)
      ]
    ) @call.expression
    """
    calls_query = Query(PY_LANGUAGE, calls_query_string)
    calls_cursor = QueryCursor(calls_query)
    calls_captures = calls_cursor.captures(tree.root_node)

    for capture_name, nodes in calls_captures.items():
        for node in nodes:
            if capture_name == "call.name":
                callee_name = get_node_text(node)
                enclosing_func_node = find_enclosing_scope(node, "function_definition")
                if enclosing_func_node:
                    caller_name_node = enclosing_func_node.child_by_field_name("name")
                    if caller_name_node:
                        caller_name = get_node_text(caller_name_node)
                        graph_elements["calls"].append((caller_name, callee_name))

    return graph_elements

def create_code_graph(graph_elements):
    """
    抽出した情報からNeo4jにグラフを構築する
    """
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        print("既存のグラフをクリアしました。")

        for class_name in graph_elements["classes"]:
            session.run("MERGE (c:Class {name: $name})", name=class_name)
        print(f"{len(graph_elements['classes'])}個のクラスノードを作成しました。")

        for func_name, details in graph_elements["functions"].items():
            # ★★★ ステップ3: Neo4jへの書き込み処理の修正 ★★★
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
                param_name = param_info["name"]
                param_order = param_info["order"]
                
                # パラメータノードを作成
                type_hint = param_info.get("type_hint", "")
                description = param_info.get("description", "")
                is_optional = param_info.get("is_optional", False)
                session.run("""
                    MERGE (p:Parameter {name: $param_name})
                    SET p.order = $param_order, p.type_hint = $type_hint, p.description = $description, p.is_optional = $is_optional
                """, param_name=param_name, param_order=param_order, type_hint=type_hint, description=description, is_optional=is_optional)
                
                # 関数とパラメータの関係を作成
                session.run("""
                    MATCH (f:Function {name: $func_name})
                    MATCH (p:Parameter {name: $param_name})
                    MERGE (f)-[:HAS_PARAMETER {order: $param_order}]->(p)
                """, func_name=func_name, param_name=param_name, param_order=param_order)
            
            if details.get("class_name"):
                session.run("""
                    MATCH (f:Function {name: $func_name})
                    MATCH (c:Class {name: $class_name})
                    MERGE (f)-[:PART_OF]->(c)
                """, func_name=func_name, class_name=details["class_name"])
        print(f"{len(graph_elements['functions'])}個の関数ノードとパラメータ関係を作成しました。")

        for caller, callee in graph_elements["calls"]:
            session.run("""
                MATCH (caller:Function {name: $caller_name})
                MATCH (callee:Function {name: $callee_name})
                MERGE (caller)-[:CALLS]->(callee)
            """, caller_name=caller, callee_name=callee)
        print(f"{len(graph_elements['calls'])}個の呼び出し関係を作成しました。")

        print("\nNeo4jの知識グラフ構築が完了しました。")
        
        # 作成されたグラフの構造を確認するクエリを実行
        print("\n--- グラフ構造の確認 ---")
        result = session.run("""
            MATCH (f:Function)-[:HAS_PARAMETER]->(p:Parameter)
            RETURN f.name as function_name, f.description as description, f.return_type as return_type, f.return_description as return_description, p.name as parameter_name, p.order as parameter_order, p.type_hint as type_hint, p.description as param_description, p.is_optional as is_optional
            ORDER BY f.name, p.order
        """)
        
        print("関数とパラメータの関係:")
        current_function = None
        for record in result:
            if current_function != record['function_name']:
                current_function = record['function_name']
                print(f"\n関数: {record['function_name']}")
                if record['description']:
                    print(f"  説明: {record['description']}")
                if record['return_type']:
                    return_info = f"{record['return_type']}"
                    if record['return_description']:
                        return_info += f": {record['return_description']}"
                    print(f"  戻り値: {return_info}")
            
            type_info = f" ({record['type_hint']})" if record['type_hint'] else ""
            optional_info = " [オプション]" if record['is_optional'] else ""
            param_desc = f" - {record['param_description']}" if record['param_description'] else ""
            print(f"  パラメータ: {record['parameter_name']}{type_info}{optional_info}{param_desc} (順序: {record['parameter_order']})")
    
    driver.close()

# --- メイン処理 ---
if __name__ == "__main__":
    print("--- ステップ1: コード構造の解析 ---")
    graph_elements = extract_graph_elements(tree)
    
    print("抽出されたグラフ要素:")
    print(json.dumps(graph_elements, indent=2, ensure_ascii=False))
    print("-" * 20)

    print("\n--- ステップ2: Neo4jへのグラフ構築 ---")
    if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
        print("Neo4jの接続情報が.envファイルに設定されていません。グラフ構築をスキップします。")
    else:
        try:
            # 接続確認用のドライバーを作成
            driver_check = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
            driver_check.verify_connectivity()
            print("Neo4jデータベースへの接続を確認しました。")
            driver_check.close()
            
            # グラフ構築を実行
            create_code_graph(graph_elements)
        except Exception as e:
            print(f"Neo4jへの接続またはグラフ構築中にエラーが発生しました: {e}")
            print("`.env`ファイルの接続情報が正しいか確認してください。")