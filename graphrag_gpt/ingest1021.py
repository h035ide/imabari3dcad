from tree_sitter import Language, Parser
import tree_sitter_python as tspython

from pathlib import Path
import re
import json
from typing import List, Dict, Any, Tuple
import shutil

from langchain_openai import ChatOpenAI

import config
from langchain_core.documents import Document
from langchain_neo4j import Neo4jGraph
from neo4j.exceptions import ServiceUnavailable
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

DATA_DIR = Path("data")
NEO4J_URI = config.NEO4J_URI
NEO4J_USER = config.NEO4J_USER
NEO4J_PASSWORD = config.NEO4J_PASSWORD
NEO4J_DATABASE = getattr(config, "NEO4J_DATABASE", "neo4j")

API_TXT_CANDIDATES = [
    Path("/mnt/data/api.txt"),
    Path("api.txt"),
    DATA_DIR / "api.txt",
]

API_ARG_TXT_CANDIDATES = [
    Path("/mnt/data/api_arg.txt"),
    Path("api_arg.txt"),
    DATA_DIR / "api_arg.txt",
]

PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

CHROMA_PERSIST_DIR = DATA_DIR / "chroma_db"
OPENAI_API_KEY = config.OPENAI_API_KEY

# モデル名を "gpt-4-turbo" など、利用可能なモデルに変更してください
llm = ChatOpenAI(temperature=0, model_name="gpt-5", openai_api_key=OPENAI_API_KEY) 


def extract_triples_from_script(
    script_path: str, script_text: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """スクリプト例のテキストから、ノード/リレーションのトリプルを生成する"""
    triples: List[Dict[str, Any]] = []
    node_props: Dict[str, Dict[str, Any]] = {}

    script_node_id = script_path
    node_props[script_node_id] = {
        "type": "ScriptExample",
        "properties": {
            "name": script_path,
            "code": script_text
        }
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
            "properties": {"code": call["full_text"], "order": i}
        }
        
        # ScriptExampleノードに直接CONTAINSリレーションで関連付ける
        triples.append({
            "source": script_node_id, "source_type": "ScriptExample",
            "label": "CONTAINS", "target": call_node_id, "target_type": "MethodCall"
        })
        
        triples.append({
            "source": call_node_id, "source_type": "MethodCall",
            "label": "CALLS", "target": method_name, "target_type": "Method"
        })

        # --- データフロー解析 ---
        # 1. 現在のメソッド呼び出しの引数を解析する
        arguments_node = call["node"].child_by_field_name("arguments")
        if arguments_node:
            # 引数ノード内のすべての変数名（identifier）を再帰的に探索
            arg_vars = []
            def find_identifiers(n):
                if n.type == 'identifier':
                    arg_vars.append(n.text.decode('utf8'))
                for child in n.children:
                    find_identifiers(child)
            find_identifiers(arguments_node)
            
            # 見つかった変数について、それが以前のメソッド呼び出しの結果であるかチェック
            for var_name in set(arg_vars): # setで重複したリレーションを防止
                if var_name in variable_to_source_call_id:
                    source_call_node_id = variable_to_source_call_id[var_name]
                    # データフローを示す PASSES_RESULT_TO リレーションを追加
                    triples.append({
                        "source": source_call_node_id, "source_type": "MethodCall",
                        "label": "PASSES_RESULT_TO", 
                        "target": call_node_id, "target_type": "MethodCall"
                    })

        # 2. 現在のメソッド呼び出しの結果が変数に代入されているかチェック
        if call["assigned_to"]:
            # 変数名と現在の呼び出しIDをマッピングし、後続の呼び出しで参照できるようにする
            variable_to_source_call_id[call["assigned_to"]] = call_node_id
        # --- データフロー解析ここまで ---

        if prev_call_node_id:
            triples.append({
                "source": prev_call_node_id, "source_type": "MethodCall",
                "label": "NEXT", "target": call_node_id, "target_type": "MethodCall"
            })
        
        prev_call_node_id = call_node_id

    for method_name in all_methods_in_script:
        triples.append({
            "source": script_node_id, "source_type": "ScriptExample",
            "label": "IS_EXAMPLE_OF", "target": method_name, "target_type": "Method"
        })

    return triples, node_props

def _read_api_text() -> str:
    """api.txt を候補パスから読み込む"""
    for p in API_TXT_CANDIDATES:
        if p.exists():
            return p.read_text(encoding="utf-8")
    raise FileNotFoundError("api.txt が見つかりませんでした。/mnt/data/api.txt または ./api.txt を用意してください。")

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

def _normalize_text(text: str) -> str:
    text = text.replace("\ufeff", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = text.replace("\t", " ")
    text = re.sub(r"[ \u00A0\u3000]+", " ", text)
    return text

def _parse_data_type_descriptions(text: str) -> Dict[str, str]:
    descriptions = {}
    current_type = None
    current_desc_lines = []
    
    normalized_text = _normalize_text(text)
    
    for line in normalized_text.split("\n"):
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("■"):
            if current_type and current_desc_lines:
                descriptions[current_type] = "\n".join(current_desc_lines).strip()
            
            current_type = line.replace("■", "").strip()
            current_desc_lines = []
        elif current_type:
            current_desc_lines.append(line)
            
    if current_type and current_desc_lines:
        descriptions[current_type] = "\n".join(current_desc_lines).strip()
        
    return descriptions


def _extract_graph_from_specs_with_llm(raw_text: str) -> Dict[str, List[Dict[str, Any]]]:
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
            - `properties`: {{ "name": "データ型名" }}
        - `Attribute`: パラメータオブジェクトが持つ属性。
            - `id`: `データ型名_属性名` (例: "ブラケット要素のパラメータオブジェクト_DefinitionType")
                    - `properties`: {{ "name": "属性名", "description": "属性の日本語説明 (型情報を除いたもの)" }}

            2.  **リレーションの種類:**
                - `BELONGS_TO`: (Method) -> (Object)
                - `HAS_PARAMETER`: (Method) -> (Parameter)
                - `HAS_RETURNS`: (Method) -> (ReturnValue)
                - `HAS_TYPE`: (Parameter) -> (DataType), (ReturnValue) -> (DataType), (Attribute) -> (DataType)
                - `HAS_ATTRIBUTE`: (DataType) -> (Attribute)

        --- 出力形式 ---
        - 全体を1つのJSONオブジェクトで出力してください。
        - `nodes` と `relationships` の2つのキーを持ちます。
        - `nodes` の値はノードオブジェクトのリストです。
        - `relationships` の値はリレーションオブジェクトのリストです。
        - 各オブジェクトの形式は以下の通りです。
        - ノード: `{{"id": "一意のID", "type": "ノードの種類", "properties": {{...}} }}`
        - リレーション: `{{"source": "ソースノードID", "target": "ターゲットノードID", "type": "リレーションの種類"}}`

        --- 指示 ---
        - テキスト全体を解析し、登場するすべてのオブジェクト、メソッド、引数、戻り値を抽出してください。
        - 「■Partオブジェクトのメソッド」 のように定義されている場合、"Part" を `Object` ノードとし、後続の `Method` ノードは "Part" に `BELONGS_TO` させてください。
        - `id`はスキーマ定義に従って一意に命名してください。
        - DataTypeノードは、仕様書に登場するすべての型を重複なくリストアップしてください。もし型が明記されていない場合は、そのまま空文字列を指定してください。
        - JSONはマークダウンのコードブロック(` ```json ... ``` `)で囲んでください。
        - JSONオブジェクトにはコメントをいれないでください。
        - 必ずJSONオブジェクトで出力してください。
        - Parameterノードのdescriptionについて、`：`の後の文章を抽出し、要約や言い換えをせずにそのまま指定してください。
        - `〇〇パラメータオブジェクト` というセクションを見つけたら、その名前 (例: "ブラケット要素のパラメータオブジェクト") で `DataType` ノードを抽出してください。
        - 上記 `DataType` ノードに続く `属性` リスト内の各項目 (例: `DefinitionType //s整数: ...`) は、`Attribute` ノードとして抽出してください。
        - `Attribute` ノードの `id` は `DataType名_属性名` (例: "ブラケット要素のパラメータオブジェクト_DefinitionType") としてください。
        - `Attribute` ノードの `description` には、`//` の後の説明文から型情報 (例: `整数:`, `文字列：`) を *除いた* 説明文 (例: "ブラケットの作成方法指定 0: 面指定 1:基準要素指定") を格納してください。
        - `//` の後の説明文に `型名:` (例: `整数:`) が含まれている場合、その `型名` (例: "整数") を `id` とする `DataType` ノードを作成（または参照）し、`Attribute` ノードからその `DataType` ノードへ `HAS_TYPE` リレーションを張ってください。
        - 説明文に `型名:` が含まれていない場合 (例: `BasePlane //面指定の場合の基準平面`)、`description` には説明文全体 (例: "面指定の場合の基準平面") を格納し、`HAS_TYPE` リレーションは作成しないでください。
        - 各 `Attribute` ノードから、それが属する `DataType` ノード (パラメータオブジェクト) へ `HAS_ATTRIBUTE` リレーションを張ってください。 (このリレーションは `HAS_TYPE` とは別です)
        - `Create[... ]Param` (例: `CreateBracketParam`) のようなメソッドは、対応する `〇〇パラメータオブジェクト` (例: "ブラケット要素のパラメータオブジェクト") を `DataType` とする `ReturnValue` を持つ `Method` ノードとして抽出してください。

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

def extract_triples_from_specs(
    graph_data: Dict[str, List[Dict[str, Any]]], 
    type_descriptions: Dict[str, str]
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
            
        triples.append({
            "source": source_id,
            "source_type": node_type_map[source_id],
            "label": rel["type"],
            "target": target_id,
            "target_type": node_type_map[target_id],
        })
        
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
        if node.type == 'call':
            function_node = node.child_by_field_name('function')
            # obj.method() の形式 (`attribute`ノード) であることを確認
            if function_node and function_node.type == 'attribute':
                obj_node = function_node.child_by_field_name('object')
                method_node = function_node.child_by_field_name('attribute')
                
                if obj_node and method_node:
                    call_details = {
                        "object_name": obj_node.text.decode('utf8'),
                        "method_name": method_node.text.decode('utf8'),
                        "full_text": node.text.decode('utf8'),
                        "node": node,  # データフロー解析のためにnodeオブジェクト自体を保持
                        "assigned_to": None, # 結果が代入される変数名（デフォルトはNone）
                    }
                    
                    # この呼び出しが代入文の一部かチェック (e.g., var = obj.method())
                    parent = node.parent
                    if parent and parent.type == 'assignment':
                        left_node = parent.child_by_field_name('left')
                        if left_node:
                            call_details["assigned_to"] = left_node.text.decode('utf8')
                            
                    calls.append(call_details)

        # 再帰的に子ノードを探索
        for child in node.children:
            find_calls(child)

    find_calls(root_node)
    return calls

def _triples_to_graph_documents(triples: List[Dict[str, Any]], node_props: Dict[str, Dict[str, Any]]) -> List[GraphDocument]:
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
                source=source_node,
                target=target_node,
                type=t["label"],
                properties={}
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
        print("⚠ グラフドキュメントが見つからないため、ChromaDBの構築をスキップします。")
        return

    # gdoc (GraphDocument) のノードをベクトル化の対象にする
    print(f"✔ グラフから {len(graph_docs[0].nodes)} 個のノードをベクトル化の対象とします。")
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
            content = f"ノードタイプ: {node.type}\nID: {node.id}\nプロパティ:\n{prop_text}"
        
        metadata = {
            "source": "graph_node",
            "node_id": node.id,
            "node_type": node.type,
        }
        docs_for_vectorstore.append(Document(page_content=content.strip(), metadata=metadata))

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
        print(f"✔ Chroma DB created and persisted with {len(docs_for_vectorstore)} documents at: {CHROMA_PERSIST_DIR}")
    except Exception as e:
        print(f"⚠ Chroma DBの作成に失敗しました: {e}")

def _build_and_load_neo4j() -> List[GraphDocument]:
    """
    API仕様とスクリプト例を解析し、Neo4jにグラフを構築する。
    構築したグラフドキュメントを返す。
    """
    # --- 1. API仕様書 (api.txt, api_arg.txt) の解析 ---
    print("📄 API仕様書を解析中...")
    api_text = _read_api_text()
    
    # --- ここからが修正箇所 ---
    # LLMでAPI仕様書から直接グラフ構造(ノード/リレーション)を抽出
    print("🤖 LLMによるAPI仕様書からのグラフ抽出を実行中...")
    graph_data_from_llm = _extract_graph_from_specs_with_llm(api_text)
    
    # データ型の説明テキストを読み込む
    api_arg_text = _read_api_arg_text()
    type_descriptions = _parse_data_type_descriptions(api_arg_text)
    
    # LLMが生成したデータにデータ型の説明を追加
    for node in graph_data_from_llm.get("nodes", []):
        if node.get("type") == "DataType" and node.get("properties", {}).get("name") in type_descriptions:
            node["properties"]["description"] = type_descriptions[node["properties"]["name"]]

    # LLMの出力を後続処理用のトリプル形式に変換
    spec_triples, spec_node_props = extract_triples_from_specs(graph_data_from_llm, type_descriptions)
    # --- 修正箇所はここまで ---
    print(f"✔ API仕様書からトリプルを生成: {len(spec_triples)} 件")

    # Neo4jに投入する前のAPI仕様書由来のデータをJSONファイルとして保存
    with open("neo4j_data.json", "w", encoding="utf-8") as f:
        json.dump(
            graph_data_from_llm,
            f,
            indent=2,
            ensure_ascii=False,
        )
    print("💾 API仕様書解析後のデータを 'neo4j_data.json' に保存しました。")

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
    gdocs = _triples_to_graph_documents(spec_triples + script_triples, {**spec_node_props, **script_node_props})
    
    try:
        node_count, rel_count = _rebuild_graph_in_neo4j(gdocs)
        print(f"✔ グラフデータベースの再構築が完了しました: ノード={node_count}, リレーションシップ={rel_count}")
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