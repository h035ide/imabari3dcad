from tree_sitter import Language, Parser
import tree_sitter_python as tspython

from pathlib import Path
import re
import json
from typing import List, Dict, Any, Optional, Tuple
import shutil

from langchain_openai import ChatOpenAI

import config, logging
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

llm = ChatOpenAI(temperature=1, model_name="gpt-5", openai_api_key=OPENAI_API_KEY) 

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

def _normalize_text(text: str) -> str:
    text = text.replace("\ufeff", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = text.replace("\t", " ")
    text = re.sub(r"[ \u00A0\u3000]+", " ", text)
    return text

def _to_object_id_from_header(header: str) -> str:
    s = header.strip()
    s = re.sub(r"^■", "", s)
    s = s.replace("のメソッド", "")
    s = s.replace("オブジェクト", "")
    return s.strip()

def _guess_return_type_from_desc(desc: str) -> str:
    d = desc or ""
    if re.search(r"\bID\b", d, flags=re.IGNORECASE) or ("要素ID" in d):
        return "ID"
    return "不明"


def _preprocess_text_with_llm(raw_text: str) -> str:
    """LLMを使ってAPI仕様書テキストを解析しやすいMarkdown形式に変換する"""
    prompt = f"""
    以下のAPI仕様書テキストを、後続のプログラムで解析しやすいように、一貫したMarkdown形式に整形してください。

    ルール:
    - オブジェクト定義行「■〇〇のメソッド」はそのまま維持する。
    - 各メソッド定義は、元の「〇 日本語説明」と「MethodName(」を統合し、「### `MethodName` (日本語説明)」の形式に変換する。
    - 返り値は「**返り値:**」で始める。
    - パラメータは箇条書きリストにする。各項目は「- `引数名` // 型: 説明」の形式にする。
    - 元のテキストに含まれる情報は、コメントアウトも含めて可能な限り保持してください。

    --- 元のテキスト ---
    {raw_text}
    --- ここまで ---

    整形後のテキスト:
    """
    try:
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"      ⚠ LLMによる前処理中にエラー: {e}")
        return raw_text # エラー時は元のテキストを返す

def _parse_api_specs(text: str) -> List[Dict[str, Any]]:
    """LLMで整形されたMarkdown形式のAPI仕様書テキストを解析する"""
    lines = text.split("\n")
    
    # 整形されたMarkdown形式に合わせた正規表現
    header_pat = re.compile(r"^■(.+のメソッド)$")
    method_pat = re.compile(r"^###\s+`([A-Za-z_][A-Za-z0-9_]*)`\s*\((.+)\)$")
    ret_pat = re.compile(r"^\*\*返り値[:：]\*\*\s*(.+)$")
    param_pat = re.compile(r"^\s*-\s+`([A-Za-z_][A-Za-z0-9_]+)`\s*//\s*(.+?)\s*[:：]\s*(.+)$")

    entries: List[Dict[str, Any]] = []
    current_object = "Object"  # デフォルト値
    current_entry: Optional[Dict[str, Any]] = None

    # 最初にヘッダー（■...）を探して、どのオブジェクトのメソッドかを特定
    for line in lines:
        m_header = header_pat.match(line.strip())
        if m_header:
            current_object = _to_object_id_from_header(line.strip())
            break

    for line in lines:
        line = line.strip()
        if not line:
            continue

        m_method = method_pat.match(line)
        if m_method:
            if current_entry:
                entries.append(current_entry)
            
            method_name, title_jp = m_method.groups()
            current_entry = {
                "object": current_object,
                "title_jp": title_jp.strip(),
                "name": method_name.strip(),
                "return_desc": "",
                "return_type": "不明",
                "params": [],
            }
            continue

        if current_entry is None:
            continue

        m_ret = ret_pat.match(line)
        if m_ret:
            return_desc = m_ret.group(1).strip()
            current_entry["return_desc"] = return_desc
            current_entry["return_type"] = _guess_return_type_from_desc(return_desc)
            continue
            
        m_param = param_pat.match(line)
        if m_param:
            pname, ptype, pdesc = m_param.groups()
            current_entry["params"].append(
                {"name": pname.strip(), "type": ptype.strip(), "description": pdesc.strip()}
            )
            continue
    
    if current_entry:
        entries.append(current_entry)
        
    return entries


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

def extract_triples_from_specs(
    api_text: str, type_descriptions: Dict[str, str]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    # _parse_api_specsは書き換え済みのものが呼ばれる
    entries = _parse_api_specs(api_text)

    triples: List[Dict[str, Any]] = []
    node_props: Dict[str, Dict[str, Any]] = {}

    def _clean_type_name(type_name: str) -> str:
        return re.sub(r"\s*\(.+\)$", "", type_name).strip()

    def create_data_type_node(raw_type_name: str) -> str:
        cleaned_type_name = _clean_type_name(raw_type_name)
        if cleaned_type_name not in node_props:
            properties = {"name": cleaned_type_name}
            description = type_descriptions.get(cleaned_type_name)
            if description:
                properties["description"] = description
            node_props[cleaned_type_name] = {"type": "DataType", "properties": properties}
        return cleaned_type_name

    for e in entries:
        obj_name = e["object"] or "Object"
        method_name = e["name"]
        title_jp = e.get("title_jp", "")
        ret_desc = e.get("return_desc", "")
        ret_type_raw = e.get("return_type", "不明")
        params = e.get("params", [])

        node_props.setdefault(obj_name, {"type": "Object", "properties": {"name": obj_name}})
        node_props.setdefault(method_name, {"type": "Method", "properties": {"name": method_name, "description": title_jp}})
        ret_node_id = f"{method_name}_ReturnValue"
        node_props.setdefault(ret_node_id, {"type": "ReturnValue", "properties": {"description": ret_desc}})
        
        cleaned_ret_type = create_data_type_node(ret_type_raw)

        triples.append({
            "source": method_name, "source_type": "Method",
            "label": "BELONGS_TO", "target": obj_name, "target_type": "Object"
        })
        triples.append({
            "source": method_name, "source_type": "Method",
            "label": "HAS_RETURNS", "target": ret_node_id, "target_type": "ReturnValue"
        })
        triples.append({
            "source": ret_node_id, "source_type": "ReturnValue",
            "label": "HAS_TYPE", "target": cleaned_ret_type, "target_type": "DataType"
        })

        for i, p in enumerate(params):
            pname = p.get("name") or "Param"
            ptype_raw = p.get("type") or "型"
            pdesc = p.get("description") or ""
            param_node_id = f"{method_name}_{pname}"
            node_props.setdefault(param_node_id, {
                "type": "Parameter",
                "properties": {"name": pname, "description": pdesc, "order": i}
            })
            cleaned_ptype = create_data_type_node(ptype_raw)
            triples.append({
                "source": method_name, "source_type": "Method",
                "label": "HAS_PARAMETER", "target": param_node_id, "target_type": "Parameter"
            })
            triples.append({
                "source": param_node_id, "source_type": "Parameter",
                "label": "HAS_TYPE", "target": cleaned_ptype, "target_type": "DataType"
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
    print("📄 API仕様書を解析中...")
    api_text = _read_api_text()
    
    # --- 提案4：ここからが修正箇所 ---
    # LLMで前処理を実行
    print("🤖 LLMによるAPI仕様書の前処理を実行中...")
    processed_api_text = _preprocess_text_with_llm(api_text)
    # --- 提案4：修正箇所はここまで ---

    api_arg_text = _read_api_arg_text()
    type_descriptions = _parse_data_type_descriptions(api_arg_text)
    
    # 整形されたテキスト(processed_api_text)をパーサーに渡す
    spec_triples, spec_node_props = extract_triples_from_specs(processed_api_text, type_descriptions)
    print(f"✔ API仕様書からトリプルを抽出: {len(spec_triples)} 件")

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