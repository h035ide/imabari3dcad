from tree_sitter import Language, Parser
import tree_sitter_python as tspython

import re
import json
from typing import List, Dict, Any, Tuple
import shutil

import config
from langchain_core.documents import Document
from langchain_neo4j import Neo4jGraph
from neo4j.exceptions import ServiceUnavailable
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

# 設定をconfigモジュールから取得
DATA_DIR = config.DATA_DIR
NEO4J_URI = config.NEO4J_URI
NEO4J_USER = config.NEO4J_USER
NEO4J_PASSWORD = config.NEO4J_PASSWORD
NEO4J_DATABASE = config.NEO4J_DATABASE
API_ARG_TXT_CANDIDATES = config.API_ARG_TXT_CANDIDATES
CHROMA_PERSIST_DIR = config.CHROMA_PERSIST_DIR
OPENAI_API_KEY = config.OPENAI_API_KEY

PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

# LLM設定をconfigモジュールから取得
llm_kwargs = {
    "temperature": config.LLM_TEMPERATURE,
    "model_name": config.LLM_MODEL_NAME,
    "openai_api_key": OPENAI_API_KEY,
}
if config.LLM_REQUEST_TIMEOUT is not None:
    llm_kwargs["request_timeout"] = config.LLM_REQUEST_TIMEOUT

llm = ChatOpenAI(**llm_kwargs)


def _read_api_arg_text() -> str:
    """api_arg.txt を候補パスから読み込む"""
    for p in API_ARG_TXT_CANDIDATES:
        if p.exists():
            return p.read_text(encoding="utf-8")
    raise FileNotFoundError("api_arg.txt が見つかりませんでした。")


def _read_script_files() -> List[Tuple[str, str]]:
    """data ディレクトリ内の .py ファイルをすべて読み込む"""
    script_files = []
    if not DATA_DIR.exists():
        return []

    for p in DATA_DIR.glob("*.py"):
        if p.is_file():
            script_files.append((p.name, p.read_text(encoding="utf-8")))

    return script_files


def extract_triples_from_script(
    script_path: str, script_text: str
) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """スクリプト例のテキストから、ノード/リレーションのトリプルを生成する"""
    triples: List[Dict[str, Any]] = []
    node_props: Dict[str, Dict[str, Any]] = {}

    script_node_id = script_path
    node_props[script_node_id] = {
        "type": "ScriptExample",
        "properties": {"name": script_path, "code": script_text},
    }

    all_methods_in_script = set()

    # データフローを追跡するため、スクリプト内で変数がどのメソッド呼び出しから生成されたかを記録する
    # { "変数名": "生成元のMethodCallノードID" }
    variable_to_source_call_id: Dict[str, str] = {}

    method_calls_in_script = _extract_method_calls_from_script(script_text)
    prev_call_node_id = None

    for i, call in enumerate(method_calls_in_script):
        method_name = call["method_name"]
        all_methods_in_script.add(method_name)

        call_node_id = f"{script_path}_call_{i}"
        node_props[call_node_id] = {
            "type": "MethodCall",
            "properties": {"code": call["full_text"], "order": i},
        }

        # ScriptExampleノードに直接CONTAINSリレーションで関連付ける
        triples.append(
            {
                "source": script_node_id,
                "source_type": "ScriptExample",
                "label": "CONTAINS",
                "target": call_node_id,
                "target_type": "MethodCall",
            }
        )

        triples.append(
            {
                "source": call_node_id,
                "source_type": "MethodCall",
                "label": "CALLS",
                "target": method_name,
                "target_type": "Method",
            }
        )

        # --- データフロー解析 ---
        # 1. 現在のメソッド呼び出しの引数を解析する
        arguments_node = call["node"].child_by_field_name("arguments")
        if arguments_node:
            # 引数ノード内のすべての変数名（identifier）を再帰的に探索
            arg_vars = []

            def find_identifiers(n):
                if n.type == "identifier":
                    arg_vars.append(n.text.decode("utf8"))
                for child in n.children:
                    find_identifiers(child)

            find_identifiers(arguments_node)

            # 見つかった変数について、それが以前のメソッド呼び出しの結果であるかチェック
            for var_name in set(arg_vars):  # setで重複したリレーションを防止
                if var_name in variable_to_source_call_id:
                    source_call_node_id = variable_to_source_call_id[var_name]
                    # データフローを示す PASSES_RESULT_TO リレーションを追加
                    triples.append(
                        {
                            "source": source_call_node_id,
                            "source_type": "MethodCall",
                            "label": "PASSES_RESULT_TO",
                            "target": call_node_id,
                            "target_type": "MethodCall",
                        }
                    )

        # 2. 現在のメソッド呼び出しの結果が変数に代入されているかチェック
        if call["assigned_to"]:
            # 変数名と現在の呼び出しIDをマッピングし、後続の呼び出しで参照できるようにする
            variable_to_source_call_id[call["assigned_to"]] = call_node_id
        # --- データフロー解析ここまで ---

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

    return triples, node_props


def _extract_graph_from_specs_with_llm(
    raw_text: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """LLMを使ってAPI仕様書の生テキストからノードとリレーションを抽出する"""
    prompt = f"""
        あなたはAPI仕様書を解析し、知識グラフを構築する専門家です。
        以下のAPI仕様書テキストから、指定されたスキーマに従ってノードとリレーションを抽出し、JSON形式で出力してください。

        --- グラフのスキーマ定義 ---
        1.  **ノードの種類とプロパティ:**
            - `Object`: APIの操作対象となるオブジェクト。 (例: "Part")
                - `id`: オブジェクト名 (例: "Part")
                - `properties`: {{ "name": "オブジェクト名" }}
            - `Method`: オブジェクトに属するメソッド。
                - `id`: メソッド名 (例: "CreateVariable")
                - `properties`: {{ "name": "メソッド名", "description": "メソッドの日本語説明" }}
            - `Parameter`: メソッドが受け取る引数。
                - `id`: `メソッド名_引数名` (例: "CreateVariable_VariableName")
                - `properties`: {{ "name": "引数名", "description": "引数の説明", "order": 引数の順番(0から) }}
            - `ReturnValue`: メソッドの戻り値。
                - `id`: `メソッド名_ReturnValue` (例: "CreateVariable_ReturnValue")
                - `properties`: {{ "description": "戻り値の説明" }}
            - `DataType`: 引数や戻り値、属性の型。
                - `id`: データ型名 (例: "文字列", "長さ", "bool", "ブラケット要素のパラメータオブジェクト", "整数")
                - `properties`: {{ "name": "データ型名" }} # 説明は後で別のプロンプトで付与します
            - `Attribute`: パラメータオブジェクトが持つ属性。
                - `id`: `データ型名_属性名` (例: "ブラケット要素のパラメータオブジェクト_DefinitionType")
                - `properties`: {{ "name": "属性名", "description": "属性の日本語説明 (型情報を除いたもの)" }}

        2.  **リレーションの種類:**
            - `BELONGS_TO`: (Method) -> (Object)
            - `HAS_PARAMETER`: (Method) -> (Parameter)
            - `HAS_RETURNS`: (Method) -> (ReturnValue)
            - `HAS_TYPE`: (Parameter) -> (DataType), (ReturnValue) -> (DataType), (Attribute) -> (DataType)
            - `HAS_ATTRIBUTE`: (DataType) -> (Attribute)
        
        --- 抽出ルール ---
        1.  `■オブジェクト名` は `Object` ノードとし、後続の `Method` は `BELONGS_TO` で接続してください。
        2.  `〇〇パラメータオブジェクト` というセクションは `DataType` ノードとしてください。
        3.  上記 `DataType` に続く `属性` (例: `DefinitionType //s整数: ...`) は `Attribute` ノード (`id: DataType_Attr`) とし、`DataType` に `HAS_ATTRIBUTE` で接続してください。
        4.  `Attribute` の `description` には型情報 (例: `整数:`, `文字列：`) を *除いた* 説明文 (例: "ブラケットの作成方法指定...") を格納してください。
        5.  `//` の後の説明文に型情報 (例: `整数:`) が含まれる場合、(Attribute)から該当`DataType` (例: "整数") へ `HAS_TYPE` リレーションを張ってください。
        6.  `Create[... ]Param` (例: `CreateBracketParam`) メソッドは、対応する `〇〇パラメータオブジェクト` (例: "ブラケット要素のパラメータオブジェクト") を `DataType` とする `ReturnValue` を持つ `Method` として抽出してください。
        7.  Parameterノードのdescriptionには、`：`の後の文章をそのまま指定してください。

        --- 出力形式 ---
        - 全体を1つのJSONオブジェクトで出力してください。
        - **`nodes`** の値は、以下の形式の**ノードオブジェクト**のリストです:
        `{{"id": "一意のID", "type": "ノードの種類", "properties": {{...}} }}`
        - **`relationships`** の値は、以下の形式の**リレーションオブジェクト**のリストです:
        `{{"source": "ソースノードID", "target": "ターゲットノードID", "type": "リレーションの種類"}}`

        --- API仕様書テキスト ---
        {raw_text}
        --- ここまで ---

        抽出後のJSON:
    """
    try:
        response = llm.invoke(prompt)
        # マークダウンのコードブロックからJSON部分を抽出
        match = re.search(r"```json\s*([\s\S]+?)\s*```", response.content)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
        else:
            # コードブロックがない場合、直接パースを試みる
            return json.loads(response.content)
    except Exception as e:
        print(f"      ⚠ LLMによるグラフ抽出またはJSONパース中にエラー: {e}")
        return {"nodes": [], "relationships": []}


def _extract_datatype_descriptions_with_llm(raw_text: str) -> Dict[str, str]:
    """LLMを使ってapi_arg.txtからデータ型の説明を抽出し、辞書形式で返す"""
    prompt = f"""
    あなたはAPI仕様書のデータ型定義を解析する専門家です。
    以下のテキストから、データ型とその説明文を抽出し、JSON形式で出力してください。

    --- 解析ルール ---
    1.  `■` (U+25A0) で始まる行は、新しいデータ型の定義開始を示します。
    2.  `■` の後に続くテキストが「データ型名」です (例: `■文字列` -> "文字列")。
    3.  データ型名の次の行から、次の `■` が出現する直前まで、またはファイルの終わりまでが、そのデータ型の「説明文」です。
    4.  説明文は、改行を含めてそのまま連結してください。

    --- 出力形式 ---
    - 全体を1つのJSONオブジェクトで出力してください。
    - キーを「データ型名」、値を「説明文」とした辞書(マップ)形式とします。
    - 例: {{"文字列": "通常の文字列", "浮動小数点": "通常の数値\n\n例: 3.14"}}
    - JSONはマークダウンのコードブロック(` ```json ... ``` `)で囲んでください。
    - JSONオブジェクトにはコメントをいれないでください。
    - 必ずJSONオブジェクトで出力してください。

    --- データ型定義テキスト ---
    {raw_text}
    --- ここまで ---

    抽出後のJSON:
    """
    try:
        response = llm.invoke(prompt)
        # マークダウンのコードブロックからJSON部分を抽出
        match = re.search(r"```json\s*([\s\S]+?)\s*```", response.content)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
        else:
            # コードブロックがない場合、直接パースを試みる
            return json.loads(response.content)
    except Exception as e:
        print(f"      ⚠ LLMによるデータ型説明の抽出またはJSONパース中にエラー: {e}")
        return {}


def extract_triples_from_specs(
    graph_data: Dict[str, List[Dict[str, Any]]], type_descriptions: Dict[str, str]
) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """LLMが抽出したグラフデータから、後続処理で利用するトリプル形式を生成する"""

    triples: List[Dict[str, Any]] = []
    node_props: Dict[str, Dict[str, Any]] = {}

    nodes = graph_data.get("nodes", [])
    relationships = graph_data.get("relationships", [])

    node_type_map = {}

    # 1. ノード情報を node_props と node_type_map に格納
    for node in nodes:
        node_id = node["id"]
        node_type = node["type"]
        properties = node.get("properties", {})

        # DataTypeノードへの説明追加は呼び出し元で行う
        # if node_type == "DataType" and properties.get("name") in type_descriptions:
        #     properties["description"] = type_descriptions[properties["name"]]

        node_props[node_id] = {"type": node_type, "properties": properties}
        node_type_map[node_id] = node_type

    # 2. リレーション情報からトリプルを生成
    for rel in relationships:
        source_id = rel["source"]
        target_id = rel["target"]

        # マップに存在しないノードIDの場合はスキップ
        if source_id not in node_type_map or target_id not in node_type_map:
            continue

        triples.append(
            {
                "source": source_id,
                "source_type": node_type_map[source_id],
                "label": rel["type"],
                "target": target_id,
                "target_type": node_type_map[target_id],
            }
        )

    return triples, node_props


def _extract_method_calls_from_script(script_text: str) -> List[Dict[str, Any]]:
    """
    スクリプトテキストを解析し、メソッド呼び出しの詳細情報を抽出する。
    提案1の実装：メソッド呼び出しの結果が代入される変数名も取得する。
    """
    tree = parser.parse(bytes(script_text, "utf8"))
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
                        "node": node,  # データフロー解析のためにnodeオブジェクト自体を保持
                        "assigned_to": None,  # 結果が代入される変数名（デフォルトはNone）
                    }

                    # この呼び出しが代入文の一部かチェック (e.g., var = obj.method())
                    parent = node.parent
                    if parent and parent.type == "assignment":
                        left_node = parent.child_by_field_name("left")
                        if left_node:
                            call_details["assigned_to"] = left_node.text.decode("utf8")

                    calls.append(call_details)

        # 再帰的に子ノードを探索
        for child in node.children:
            find_calls(child)

    find_calls(root_node)
    return calls


def _triples_to_graph_documents(
    triples: List[Dict[str, Any]], node_props: Dict[str, Dict[str, Any]]
) -> List[GraphDocument]:
    node_map: Dict[str, Node] = {}
    for node_id, meta in node_props.items():
        if node_id in node_map:
            existing_node = node_map[node_id]
            existing_node.properties.update(meta.get("properties", {}))
        else:
            ntype = meta["type"]
            props = meta.get("properties", {})
            node_map[node_id] = Node(id=node_id, type=ntype, properties=props)

    rels: List[Relationship] = []
    for t in triples:
        source_node = node_map.get(t["source"])
        if not source_node:
            source_node = Node(id=t["source"], type=t["source_type"])
            node_map[t["source"]] = source_node

        target_node = node_map.get(t["target"])
        if not target_node:
            target_node = Node(id=t["target"], type=t["target_type"])
            node_map[t["target"]] = target_node

        rels.append(
            Relationship(
                source=source_node, target=target_node, type=t["label"], properties={}
            )
        )

    doc = Document(page_content="API Spec and Example graph")
    gdoc = GraphDocument(nodes=list(node_map.values()), relationships=rels, source=doc)
    return [gdoc]


def _rebuild_graph_in_neo4j(graph_docs: List[GraphDocument]) -> Tuple[int, int]:
    graph = Neo4jGraph(
        url=NEO4J_URI,
        username=NEO4J_USER,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE,
    )

    print("🧹 Neo4jの既存データを削除中...")
    delete_query = "MATCH (n) DETACH DELETE n"
    graph.query(delete_query)

    print(f"\n🚀 Neo4jにデータを投入中...")

    graph.add_graph_documents(graph_docs)

    res_nodes = graph.query("MATCH (n) RETURN count(n) AS c")
    res_rels = graph.query("MATCH ()-[r]->() RETURN count(r) AS c")
    return int(res_nodes[0]["c"]), int(res_rels[0]["c"])


def _build_and_load_chroma(graph_docs: List[GraphDocument]) -> None:
    """
    グラフドキュメントのノード情報からベクトルを生成し、ChromaDBに保存する
    """
    print("\n🚀 ChromaDBのベクトルデータを生成・保存中...")

    if CHROMA_PERSIST_DIR.exists():
        shutil.rmtree(CHROMA_PERSIST_DIR)
    CHROMA_PERSIST_DIR.mkdir(exist_ok=True)

    docs_for_vectorstore: List[Document] = []

    if not graph_docs:
        print(
            "⚠ グラフドキュメントが見つからないため、ChromaDBの構築をスキップします。"
        )
        return

    # gdoc (GraphDocument) のノードをベクトル化の対象にする
    print(
        f"✔ グラフから {len(graph_docs[0].nodes)} 個のノードをベクトル化の対象とします。"
    )
    for node in graph_docs[0].nodes:
        props = node.properties
        content = ""
        # ノードのタイプに応じて、ベクトル化するテキストの内容を整形
        if node.type == "Method":
            content = f"APIメソッド\nメソッド名: {props.get('name', '')}\n説明: {props.get('description', '')}"
        elif node.type == "ScriptExample":
            content = f"スクリプト例\nファイル名: {props.get('name', '')}\n全文コード:\n```python\n{props.get('code', '')}\n```"
        else:
            # その他のノードタイプはプロパティを平文化
            prop_text = "\n".join([f"- {key}: {value}" for key, value in props.items()])
            content = (
                f"ノードタイプ: {node.type}\nID: {node.id}\nプロパティ:\n{prop_text}"
            )

        metadata = {
            "source": "graph_node",
            "node_id": node.id,
            "node_type": node.type,
        }
        docs_for_vectorstore.append(
            Document(page_content=content.strip(), metadata=metadata)
        )

    # ChromaDBに投入する前のデータをJSONファイルとして保存
    chroma_data_to_save = [
        {"page_content": doc.page_content, "metadata": doc.metadata}
        for doc in docs_for_vectorstore
    ]
    with open("chroma_data.json", "w", encoding="utf-8") as f:
        json.dump(chroma_data_to_save, f, indent=2, ensure_ascii=False)
    print("💾 ChromaDB投入前のデータを 'chroma_data.json' に保存しました。")

    try:
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        vectorstore = Chroma.from_documents(
            documents=docs_for_vectorstore,
            embedding=embeddings,
            persist_directory=str(CHROMA_PERSIST_DIR),
        )
        print(
            f"✔ Chroma DB created and persisted with {len(docs_for_vectorstore)} documents at: {CHROMA_PERSIST_DIR}"
        )
    except Exception as e:
        print(f"⚠ Chroma DBの作成に失敗しました: {e}")


def _build_and_load_neo4j() -> List[GraphDocument]:
    """
    API仕様とスクリプト例を解析し、Neo4jにグラフを構築する。
    構築したグラフドキュメントを返す。
    """
    # --- 1. API仕様書 (api*.txt, api_arg.txt) の解析 ---
    print("📄 API仕様書を解析中...")

    # --- ここからが修正箇所 ---
    # 4つのAPI仕様書ファイルを定義
    api_txt_files = [
        DATA_DIR / "api1.txt",
        DATA_DIR / "api2.txt",
        DATA_DIR / "api3.txt",
        DATA_DIR / "api4.txt",
        DATA_DIR / "api5.txt",
    ]

    all_nodes = []
    all_relationships = []

    # LLMでAPI仕様書から直接グラフ構造(ノード/リレーション)を抽出
    print("🤖 LLMによるAPI仕様書からのグラフ抽出を実行中...")

    for api_file_path in api_txt_files:
        if not api_file_path.exists():
            print(f"⚠ 警告: {api_file_path} が見つかりません。スキップします。")
            continue

        print(f"  - ファイルを解析中: {api_file_path.name}")
        try:
            api_text = api_file_path.read_text(encoding="utf-8")
            # 各ファイルからグラフデータを抽出
            partial_api_data = _extract_graph_from_specs_with_llm(api_text)

            nodes = partial_api_data.get("nodes", [])
            rels = partial_api_data.get("relationships", [])

            print(f"    -> 抽出結果: ノード={len(nodes)}件, リレーション={len(rels)}件")

            all_nodes.extend(nodes)
            all_relationships.extend(rels)

        except FileNotFoundError:
            print(f"⚠ 警告: {api_file_path} が見つかりませんでした。")
        except Exception as e:
            print(f"⚠ {api_file_path.name} の処理中にエラーが発生しました: {e}")

    # 抽出したデータを統合
    # 重複ノードをIDに基づいてマージする（後勝ち）
    merged_nodes_dict = {}
    for node in all_nodes:
        node_id = node.get("id")
        if node_id:
            if node_id in merged_nodes_dict:
                # 既存のノードプロパティを更新（マージ）
                merged_nodes_dict[node_id].setdefault("properties", {}).update(
                    node.get("properties", {})
                )
            else:
                merged_nodes_dict[node_id] = node

    merged_nodes = list(merged_nodes_dict.values())

    # 重複リレーション（source, target, typeが同一）を削除
    seen_rels = set()
    merged_relationships = []
    for rel in all_relationships:
        rel_tuple = (rel.get("source"), rel.get("target"), rel.get("type"))
        if (
            rel.get("source")
            and rel.get("target")
            and rel.get("type")
            and rel_tuple not in seen_rels
        ):
            merged_relationships.append(rel)
            seen_rels.add(rel_tuple)

    api_data_from_llm = {"nodes": merged_nodes, "relationships": merged_relationships}

    print(
        f"✔ 統合後のAPI仕様書データ: ノード={len(merged_nodes)}件, リレーション={len(merged_relationships)}件"
    )

    # データ型の説明テキストを読み込む
    api_arg_text = _read_api_arg_text()
    print("🤖 LLMによるデータ型説明 (api_arg.txt) の抽出を実行中...")
    type_descriptions = _extract_datatype_descriptions_with_llm(api_arg_text)

    # LLMが生成したデータにデータ型の説明を追加
    for node in api_data_from_llm.get("nodes", []):
        if (
            node.get("type") == "DataType"
            and node.get("properties", {}).get("name") in type_descriptions
        ):
            node["properties"]["description"] = type_descriptions[
                node["properties"]["name"]
            ]

    # LLMの出力を後続処理用のトリプル形式に変換
    spec_triples, spec_node_props = extract_triples_from_specs(
        api_data_from_llm, type_descriptions
    )

    print(f"✔ API仕様書からトリプルを生成: {len(spec_triples)} 件")

    # Neo4jに投入する前のAPI仕様書由来のデータ(トリプルとノードプロパティ)をJSONファイルとして保存
    data_to_save = {"relationships": spec_triples, "nodes": spec_node_props}
    with open("neo4j_data.json", "w", encoding="utf-8") as f:
        json.dump(
            data_to_save,
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(
        "💾 API仕様書解析後のデータ(トリプル/ノード)を 'neo4j_data.json' に保存しました。"
    )

    # --- 2. スクリプト例 (data/*.py) の解析 ---
    print("\n🐍 スクリプト例 (data/*.py) を解析中...")
    script_files = _read_script_files()
    if not script_files:
        print("⚠ data ディレクトリに解析対象の .py ファイルが見つかりませんでした。")
        script_triples, script_node_props = [], {}
    else:
        all_script_triples = []
        all_script_node_props = {}
        for script_path, script_text in script_files:
            print(f"  - ファイルを解析中: {script_path}")
            triples, node_props = extract_triples_from_script(script_path, script_text)
            all_script_triples.extend(triples)
            all_script_node_props.update(node_props)
        script_triples = all_script_triples
        script_node_props = all_script_node_props
        print(f"✔ スクリプト例からトリプルを総計: {len(script_triples)} 件")

    # --- 3. データの統合とグラフDBへの投入 ---
    print("\n🔗 データを統合してグラフを構築中...")
    gdocs = _triples_to_graph_documents(
        spec_triples + script_triples, {**spec_node_props, **script_node_props}
    )

    try:
        node_count, rel_count = _rebuild_graph_in_neo4j(gdocs)
        print(
            f"✔ グラフデータベースの再構築が完了しました: ノード={node_count}, リレーションシップ={rel_count}"
        )
    except ServiceUnavailable as se:
        print(f"⚠ Neo4j への接続に失敗しました: {se}")
        print("   Neo4jサーバーが起動しているか確認してください。")
    except Exception as e:
        print(f"⚠ グラフデータベースの構築中にエラーが発生しました: {e}")

    return gdocs


def main() -> None:
    # --- Neo4j構築プロセス ---
    # Neo4jを構築し、その過程で生成されたグラフドキュメント(gdocs)を受け取る
    gdocs = _build_and_load_neo4j()

    # --- ChromaDB構築プロセス ---
    # 受け取ったgdocsを使ってChromaDBを構築する
    _build_and_load_chroma(gdocs)


if __name__ == "__main__":
    main()
