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

# 構造化データの抽出精度を高めるため、temperatureを0に設定
llm = ChatOpenAI(temperature=0, model_name="gpt-5", openai_api_key=OPENAI_API_KEY)

def _split_script_into_chunks(script_content: str) -> List[str]:
    """
    スクリプトを連続する2つ以上の改行で分割し、コードチャンクのリストを返す。
    """
    chunks = re.split(r'\n\s*\n', script_content.strip())
    return [chunk.strip() for chunk in chunks if chunk.strip()]

def _get_chunk_purpose(chunk_content: str) -> str:
    """LLMを使ってコードチャンクの目的を生成する"""
    prompt = f"""
    以下のPythonコードの断片が、APIを呼び出して何を行おうとしているのか、その目的を簡潔な日本語の一文で説明してください。

    ```python
    {chunk_content}
    ```
    このコードの目的:
    """
    try:
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"      ⚠ コードチャンクの目的生成中にエラー: {e}")
        return "目的の生成に失敗しました。"

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

    chunks = _split_script_into_chunks(script_text)
    
    all_methods_in_script = set()

    for i, chunk_text in enumerate(chunks):
        print(f"      - チャンク {i+1}/{len(chunks)} の目的を抽出中...")
        purpose = _get_chunk_purpose(chunk_text)

        chunk_node_id = f"{script_path}_chunk_{i}"
        node_props[chunk_node_id] = {
            "type": "CodeChunk",
            "properties": {"purpose": purpose, "code": chunk_text, "order": i}
        }
        triples.append({
            "source": script_node_id, "source_type": "ScriptExample",
            "label": "HAS_CHUNK", "target": chunk_node_id, "target_type": "CodeChunk"
        })

        method_calls_in_chunk = _extract_method_calls_from_script(chunk_text)
        prev_call_node_id_in_chunk = None

        for j, call in enumerate(method_calls_in_chunk):
            method_name = call["method_name"]
            all_methods_in_script.add(method_name)
            
            call_node_id = f"{script_path}_chunk_{i}_call_{j}"
            node_props[call_node_id] = {
                "type": "MethodCall",
                "properties": {"code": call["full_text"], "order": j}
            }
            
            triples.append({
                "source": chunk_node_id, "source_type": "CodeChunk",
                "label": "CONTAINS", "target": call_node_id, "target_type": "MethodCall"
            })
            
            triples.append({
                "source": call_node_id, "source_type": "MethodCall",
                "label": "CALLS", "target": method_name, "target_type": "Method"
            })

            if prev_call_node_id_in_chunk:
                triples.append({
                    "source": prev_call_node_id_in_chunk, "source_type": "MethodCall",
                    "label": "NEXT", "target": call_node_id, "target_type": "MethodCall"
                })
            
            prev_call_node_id_in_chunk = call_node_id

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

def _extract_graph_from_specs_with_llm(api_spec_text: str, api_arg_text: str) -> Dict[str, List[Dict[str, Any]]]:
    """LLMを使ってAPI仕様書(api.txt)とデータ型定義(api_arg.txt)からノードとリレーションを抽出する"""
    prompt = f"""
    あなたはAPI仕様書を解析し、知識グラフを構築する専門家です。
    以下のAPI仕様書とデータ型定義の両方を解析し、指定されたスキーマに従ってノードとリレーションを抽出し、JSON形式で出力してください。

    --- グラフのスキーマ定義 ---
    1.  **ノードの種類とプロパティ:**
        - `Object`: APIの操作対象となるオブジェクト。
            - `id`: オブジェクト名 (例: "Part")
            - `properties`: {{ "name": "オブジェクト名" }}
        - `Method`: オブジェクトに属するメソッド。
            - `id`: メソッド名 (例: "CreateSketchPlane")
            - `properties`: {{ "name": "メソッド名", "description": "メソッドの日本語説明 (返り値の行などから抽出)" }}
        - `Parameter`: メソッドが受け取る引数。
            - `id`: `メソッド名_引数名` (例: "CreateSketchPlane_ElementName")
            - `properties`: {{ "name": "引数名", "description": "引数の説明", "order": 引数の順番(0から) }}
        - `ReturnValue`: メソッドの戻り値。
            - `id`: `メソッド名_ReturnValue` (例: "CreateSketchPlane_ReturnValue")
            - `properties`: {{ "description": "戻り値の説明" }}
        - `DataType`: 引数や戻り値の型。
            - `id`: データ型名 (例: "文字列", "ID", "数値")
            - `properties`: {{ "name": "データ型名", "description": "データ型の詳細な説明" }}

    2.  **リレーションの種類:**
        - `BELONGS_TO`: (Method) -> (Object)
        - `HAS_PARAMETER`: (Method) -> (Parameter)
        - `HAS_RETURNS`: (Method) -> (ReturnValue)
        - `HAS_TYPE`: (Parameter) -> (DataType)

    --- 出力形式 ---
    - 全体を1つのJSONオブジェクトで出力してください。
    - `nodes` と `relationships` の2つのキーを持ちます。
    - `nodes` の値はノードオブジェクトのリストです。
    - `relationships` の値はリレーションオブジェクトのリストです。
    - 各オブジェクトの形式は以下の通りです。
    - ノード: `{{"id": "一意のID", "type": "ノードの種類", "properties": {{...}} }}`
    - リレーション: `{{"source": "ソースノードID", "target": "ターゲットノードID", "type": "リレーションの種類"}}`

    --- 指示 ---
    - このAPIは、API仕様書とデータ型定義を参考に、APIを呼び出すスクリプトを生成するためのAPIです。
    - 情報の漏れは許されません。
    - `id`はスキーマ定義に従って一意に命名してください。
    - `API仕様書`から、オブジェクト、メソッド、引数、戻り値をすべて抽出してください。
    - `■<オブジェクト名>オブジェクトのメソッド`という行から`Object`ノードを作成してください。
    - メソッドの定義は `〇<メソッドの説明>\\n返り値:<返り値の説明>\\n<メソッド名>(...);` の形式です。
    - メソッドの引数は `<引数名>, // <データ型>：<引数の説明>` の形式です。これを正確に解析してください。
    - `返り値:`で始まる行から`ReturnValue`ノードを生成し、メソッドと関連付けてください。返り値の型は説明文から推測してください（例：「要素ID」なら「ID」型）。
    - `データ型定義`を参考にして、`DataType`ノードをすべて生成してください。`description`プロパティには、`データ型定義`に書かれている説明を必ず含めてください。
    - `Parameter`や`ReturnValue`から`DataType`への`HAS_TYPE`リレーションを必ず作成してください。
    - JSONはマークダウンのコードブロック(` ```json ... ``` `)で囲んでください。

    --- API仕様書 (api.txt) ---
    {api_spec_text}
    --- ここまで ---

    --- データ型定義 (api_arg.txt) ---
    {api_arg_text}
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
    graph_data: Dict[str, List[Dict[str, Any]]]
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


def _extract_method_calls_from_script(script_text: str) -> List[Dict[str, str]]:
    tree = parser.parse(bytes(script_text, "utf8"))
    root_node = tree.root_node
    calls = []
    
    def find_calls(node):
        if node.type == 'call':
            function_node = node.child_by_field_name('function')
            if function_node and function_node.type == 'attribute':
                obj_node = function_node.child_by_field_name('object')
                method_node = function_node.child_by_field_name('attribute')
                args_node = node.child_by_field_name('arguments')
                if obj_node and method_node and args_node:
                    calls.append({
                        "object_name": obj_node.text.decode('utf8'),
                        "method_name": method_node.text.decode('utf8'),
                        "arguments": args_node.text.decode('utf8'),
                        "full_text": node.text.decode('utf8'),
                    })
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
        elif node.type == "CodeChunk":
            content = f"コードチャンク\n目的: {props.get('purpose', '')}\nコード:\n```python\n{props.get('code', '')}\n```"
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
    print("📄 API仕様書とデータ型定義を解析中...")
    api_text = _read_api_text()
    api_arg_text = _read_api_arg_text()
    
    # --- ここからが修正箇所 ---
    # LLMでAPI仕様書とデータ型定義から直接グラフ構造(ノード/リレーション)を抽出
    print("🤖 LLMによるAPI仕様書からのグラフ抽出を実行中...")
    graph_data_from_llm = _extract_graph_from_specs_with_llm(api_text, api_arg_text)
    
    # LLMの出力を後続処理用のトリプル形式に変換
    spec_triples, spec_node_props = extract_triples_from_specs(graph_data_from_llm)
    # --- 修正箇所はここまで ---
    print(f"✔ API仕様書からトリプルを生成: {len(spec_triples)} 件")

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
    
    # Neo4jに投入する前のデータをJSONファイルとして保存
    if gdocs:
        graph_doc_to_save = gdocs[0] # 通常は1つの要素しか含まれない
        nodes_to_save = [
            {"id": node.id, "type": node.type, "properties": node.properties}
            for node in graph_doc_to_save.nodes
        ]
        relationships_to_save = [
            {
                "source": rel.source.id,
                "target": rel.target.id,
                "type": rel.type,
                "properties": rel.properties,
            }
            for rel in graph_doc_to_save.relationships
        ]
        with open("neo4j_data.json", "w", encoding="utf-8") as f:
            json.dump(
                {"nodes": nodes_to_save, "relationships": relationships_to_save},
                f,
                indent=2,
                ensure_ascii=False,
            )
        print("💾 Neo4j投入前のデータを 'neo4j_data.json' に保存しました。")

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