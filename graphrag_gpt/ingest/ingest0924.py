from tree_sitter import Language, Parser
import tree_sitter_python as tspython

from pathlib import Path
import re
import json
from typing import List, Dict, Any, Optional, Tuple
import shutil
# ★★★ 変更点 ★★★
from datetime import datetime # タイムスタンプのためにdatetimeをインポート

from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.prompts import ChatPromptTemplate

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

# tree-sitterのPython用パーサーをセットアップ
PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)


CHROMA_PERSIST_DIR = DATA_DIR / "chroma_db"
OPENAI_API_KEY = config.OPENAI_API_KEY

# LLMのインスタンスをグローバルに定義 (HTML解析とコードチャンクの目的抽出で使用)
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

def _read_html_files() -> List[Tuple[str, str]]:
    """data ディレクトリ内の .html ファイルをすべて読み込む"""
    html_files = []
    if not DATA_DIR.exists():
        return []
    
    for p in DATA_DIR.glob("*.html"):
        if p.is_file():
            try:
                content = p.read_text(encoding="shift_jis")
            except UnicodeDecodeError:
                content = p.read_text(encoding="utf-8")
            html_files.append((p.name, content))
            
    return html_files

def _extract_graph_from_html(
    file_name: str, html_content: str
    ) -> List[GraphDocument]:
    """
    LLMGraphTransformer を使用してHTMLコンテンツからグラフドキュメントを抽出する。
    スキーマをシンプルにするためのカスタムプロンプトを設定。
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                あなたは、既存のAPI知識グラフを補強するために、技術ドキュメントから情報を抽出するエキスパートです。
                私たちのデータベースには、API仕様書からルールベースで生成された、以下のスキーマを持つグラフが既に存在します。
                - **ノードラベル**: `Object`, `Method`, `Parameter`, `DataType`, `ScriptExample`, `MethodCall`
                - **リレーションタイプ**: `BELONGS_TO`, `HAS_PARAMETER`, `CALLS`, `IS_EXAMPLE_OF` など

                あなたのタスクは、提供されたHTMLドキュメントを読み解き、この既存グラフを補完するための**概念**、**機能説明**、**制約事項**などを抽出し、既存のノードに接続することです。

                以下のガイドラインを厳守してください。

                1.  **既存エンティティへのリンク**:
                    - ドキュメントが、明らかに既存のAPIメソッド（例: `CreatePlate`）やオブジェクト（例: `Part`）について言及している場合、**新しいノードは絶対に作らないでください**。
                    - 代わりに、そのエンティティを `id` と `type`（例: {{"id": "CreatePlate", "type": "Method"}}）で正確に指定し、後述する新しい`Concept`ノードと接続してください。これにより、既存のノードに新しい情報がリンクされます。

                2.  **新しい情報の抽出（Conceptノード）**:
                    - APIの**機能**、**コンセプト**（例：「剛体の作成」、「座標系」）、**ベストプラクティス**、**制約事項**など、ルールベースでは抽出できない補足的な情報を抽出してください。
                    - これらの新しい情報は、必ず `Concept` というラベル（`type`）を持つノードとして表現します。
                    - `Concept` ノードの `id` には、その概念を簡潔に表す名称（例：「プレートの厚み設定」）を指定してください。

                3.  **リレーションの定義**:
                    - 抽出したノード間の関係性は、以下のいずれかのタイプで表現してください。
                      - **EXPLAINS** (説明する): ある`Concept`が、特定の`Method`や`Object`の機能・使い方を説明している場合。
                        (例: `(Concept:プレートの厚み設定) -[:EXPLAINS]-> (Method:CreatePlate)`)
                      - **RELATES_TO** (関連する): 2つのノードが関連しているが、直接的な説明関係ではない場合。
                        (例: `(Method:CreatePlate) -[:RELATES_TO]-> (Concept:座標系)`)
                      - **HAS_CONSTRAINT** (制約を持つ): ある`Method`や`Object`に特定の制約事項（`Concept`）がある場合。
                        (例: `(Method:GetSolidID) -[:HAS_CONSTRAINT]-> (Concept:事前にソリッドの選択が必要)`)

                4.  **出力**:
                    - 指示された形式（ノードリストとリレーションシップリスト）で、抽出した情報のみを出力してください。余分な説明は不要です。
                """,
            ),
            (
                "human",
                "以下のドキュメントから、上記のガイドラインに従って知識グラフを抽出してください:\n\n{input}",
            ),
        ]
    )

    llm_transformer = LLMGraphTransformer(llm=llm, prompt=prompt)

    soup = BeautifulSoup(html_content, 'lxml')
    
    content_div = soup.find('div', class_='contents')
    if content_div:
        text_content = content_div.get_text(separator='\n', strip=True)
    else:
        text_content = soup.body.get_text(separator='\n', strip=True) if soup.body else ""

    doc = Document(
        page_content=text_content,
        metadata={"source": "html_document", "file_name": file_name}
    )
    
    return llm_transformer.convert_to_graph_documents([doc])


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

def _parse_api_specs(text: str) -> List[Dict[str, Any]]:
    lines = text.split("\n")
    closing_pat = re.compile(r"\)\s*;?(?:\s*//.*)?$")
    param_pat = re.compile(
        r"^([A-Za-z_][A-Za-z0-9_]*)\s*,?\s*//\s*([^:：]+)\s*[:：]\s*(.*)$"
    )
    method_start_pat = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*\($")
    header_pat = re.compile(r"^■.+のメソッド$")
    title_pat = re.compile(r"^〇(.+)$")
    ret_pat = re.compile(r"^返り値[:：]\s*(.+)$")

    current_object = None
    current_title = None
    current_return_desc = None
    collecting_params = False
    current_entry: Optional[Dict[str, Any]] = None
    entries: List[Dict[str, Any]] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].strip()
        if header_pat.match(line):
            current_object = _to_object_id_from_header(line)
            current_title = None
            current_return_desc = None
            i += 1
            continue
        m_title = title_pat.match(line)
        if m_title:
            current_title = m_title.group(1).strip()
            i += 1
            if i < n:
                m_ret = ret_pat.match(lines[i].strip())
                if m_ret:
                    current_return_desc = m_ret.group(1).strip()
                    i += 1
            continue
        m_start = method_start_pat.match(line)
        if m_start:
            method_name = m_start.group(1)
            current_entry = {
                "object": current_object or "Object",
                "title_jp": current_title or "",
                "name": method_name,
                "return_desc": current_return_desc or "",
                "return_type": _guess_return_type_from_desc(current_return_desc or ""),
                "params": [],
            }
            collecting_params = True
            i += 1
            continue
        if collecting_params and current_entry is not None:
            pm = param_pat.match(line)
            if pm:
                pname, ptype, pdesc = pm.groups()
                current_entry["params"].append(
                    {"name": pname, "type": ptype.strip(), "description": pdesc.strip()}
                )
                if closing_pat.search(line):
                    entries.append(current_entry)
                    current_entry = None
                    collecting_params = False
                i += 1
                continue
            if closing_pat.search(line):
                idx_close = line.rfind(")")
                before = line[:idx_close]
                token = before.split(",")[-1].strip()
                token = re.sub(r"[;,\s]+$", "", token)
                comment = line.split("//", 1)[1].strip() if "//" in line else ""
                synth = f"{token} // {comment}" if comment else token
                pm2 = param_pat.match(synth)
                if pm2:
                    pname, ptype, pdesc = pm2.groups()
                    current_entry["params"].append(
                        {"name": pname, "type": ptype.strip(), "description": pdesc.strip()}
                    )
                entries.append(current_entry)
                current_entry = None
                collecting_params = False
                i += 1
                continue
            i += 1
            continue
        i += 1
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


def _build_and_load_chroma(
    api_entries: List[Dict[str, Any]], script_files: List[Tuple[str, str]]
    ) -> None:
    print("\n🚀 ChromaDBのベクトルデータを生成・保存中...")

    if CHROMA_PERSIST_DIR.exists():
        shutil.rmtree(CHROMA_PERSIST_DIR)
    CHROMA_PERSIST_DIR.mkdir(exist_ok=True)

    docs_for_vectorstore: List[Document] = []

    for entry in api_entries:
        content_parts = [
            f"オブジェクト: {entry['object']}",
            f"メソッド名: {entry['name']}",
            f"説明: {entry['title_jp']}",
            f"返り値: {entry['return_desc']}",
        ]
        if entry["params"]:
            param_texts = [
                f"- {p['name']} ({p['type']}): {p['description']}"
                for p in entry["params"]
            ]
            content_parts.append("パラメータ:\n" + "\n".join(param_texts))
        content = "\n".join(content_parts)
        metadata = {
            "source": "api_spec", "object": entry["object"], "method_name": entry["name"],
        }
        docs_for_vectorstore.append(Document(page_content=content, metadata=metadata))

    for script_name, script_content in script_files:
        content = f"スクリプト例: {script_name}\n\n```python\n{script_content}\n```"
        metadata = {"source": "script_example", "script_name": script_name}
        docs_for_vectorstore.append(Document(page_content=content, metadata=metadata))

    html_files = _read_html_files()
    for file_name, html_content in html_files:
        soup = BeautifulSoup(html_content, 'lxml')
        content_div = soup.find('div', class_='contents')
        if content_div:
            text_content = content_div.get_text(separator='\n', strip=True)
        else:
            text_content = soup.body.get_text(separator='\n', strip=True) if soup.body else ""
        content = f"ドキュメント: {file_name}\n\n{text_content}"
        metadata = {"source": "html_document", "file_name": file_name}
        docs_for_vectorstore.append(Document(page_content=content, metadata=metadata))

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

def _build_and_load_neo4j() -> None:
    # --- 1. API仕様書 (api.txt, api_arg.txt) の解析 ---
    print("📄 API仕様書を解析中...")
    api_text = _read_api_text()
    api_text = _normalize_text(api_text)
    api_arg_text = _read_api_arg_text()
    type_descriptions = _parse_data_type_descriptions(api_arg_text)
    spec_triples, spec_node_props = extract_triples_from_specs(api_text, type_descriptions)
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

    # --- 3. データの統合準備 ---
    gdocs = _triples_to_graph_documents(spec_triples + script_triples, {**spec_node_props, **script_node_props})
    
    # --- 4. 非構造化データ (HTML) の解析 ---
    print("\n📄 HTMLドキュメントをLLMで解析中...")
    html_files = _read_html_files()
    # ★★★ 変更点 ★★★ JSON出力用にHTMLからの抽出結果を保持するリスト
    serializable_html_data = []
    if not html_files:
        print("⚠ data ディレクトリに解析対象の .html ファイルが見つかりませんでした。")
        html_graph_docs = []
    else:
        html_graph_docs = []
        for file_name, html_content in html_files:
            print(f"  - ファイルを解析中: {file_name}")
            try:
                graph_docs_from_html = _extract_graph_from_html(file_name, html_content)
                print(f"    - LLMが抽出したデータ from '{file_name}':")
                if not graph_docs_from_html or (not graph_docs_from_html[0].nodes and not graph_docs_from_html[0].relationships):
                    print("      - データは抽出されませんでした。")
                else:
                    # ★★★ 変更点 ★★★ 抽出結果をJSONシリアライズ可能な形式に変換
                    for doc in graph_docs_from_html:
                        serializable_html_data.append({
                            "file_name": file_name,
                            "nodes": [node.__dict__ for node in doc.nodes],
                            "relationships": [
                                {
                                    "source": rel.source.id,
                                    "target": rel.target.id,
                                    "type": rel.type,
                                    "properties": rel.properties
                                }
                                for rel in doc.relationships
                            ]
                        })
                        if doc.nodes:
                            print("      - Nodes:")
                            for node in doc.nodes:
                                print(f"        - (ID: {node.id}, Type: {node.type}, Properties: {node.properties})")
                        if doc.relationships:
                            print("      - Relationships:")
                            for rel in doc.relationships:
                                print(f"        - ({rel.source.id}) -[:{rel.type}]-> ({rel.target.id})")
                html_graph_docs.extend(graph_docs_from_html)
            except Exception as e:
                print(f"  ⚠ ファイル '{file_name}' の解析中にエラーが発生しました: {e}")
        print(f"✔ HTMLドキュメントからグラフ情報を抽出しました。")

    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    # ★★★ 新機能: 抽出した全トリプル情報をJSONファイルに出力 ★★★
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    print("\n💾 抽出したトリプルをJSONファイルに出力中...")
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "sources": {
            "api_specifications": {
                "triples": spec_triples,
                "node_properties": spec_node_props
            },
            "script_examples": {
                "triples": script_triples,
                "node_properties": script_node_props
            },
            "html_documents": serializable_html_data
        }
    }
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"extracted_triples_{timestamp_str}.json"
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"✔ データを '{output_filename}' に保存しました。")
    except Exception as e:
        print(f"⚠ JSONファイルの保存中にエラーが発生しました: {e}")


    # --- 5. グラフDBへのデータ投入 ---
    print("\n🔗 データを統合してグラフを構築中...")
    gdocs.extend(html_graph_docs)
    try:
        node_count, rel_count = _rebuild_graph_in_neo4j(gdocs)
        print(f"✔ グラフデータベースの再構築が完了しました: ノード={node_count}, リレーションシップ={rel_count}")
    except ServiceUnavailable as se:
        print(f"⚠ Neo4j への接続に失敗しました: {se}")
        print("   Neo4jサーバーが起動しているか確認してください。")
    except Exception as e:
        print(f"⚠ グラフデータベースの構築中にエラーが発生しました: {e}")


def main() -> None:
    _build_and_load_neo4j()

    print("\n--- ChromaDB構築プロセス ---")
    api_text = _read_api_text()
    api_text = _normalize_text(api_text)
    api_entries = _parse_api_specs(api_text)
    print(f"✔ {len(api_entries)}件のAPI仕様を解析しました。")
    script_files = _read_script_files()
    if script_files:
        print(f"✔ {len(script_files)}件のスクリプト例を読み込みました。")
    else:
        print("⚠ スクリプト例ファイルが見つかりませんでした。")
    _build_and_load_chroma(api_entries, script_files)

if __name__ == "__main__":
    main()