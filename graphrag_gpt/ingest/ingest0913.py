from pathlib import Path
import re
import shutil
from typing import List, Tuple, Dict, Any, Optional

import config
from langchain_core.documents import Document
from langchain_neo4j import Neo4jGraph
from neo4j.exceptions import ServiceUnavailable
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.prompts import ChatPromptTemplate

# --- 定数定義 (変更なし) ---
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

CHROMA_PERSIST_DIR = DATA_DIR / "chroma_db"
OPENAI_API_KEY = config.OPENAI_API_KEY

# --- ファイル読み込み・テキスト正規化関数 (変更なし) ---

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
    """
    改行/タブ/空白の揺れを正規化。
    """
    text = text.replace("\ufeff", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = text.replace("\t", " ")
    text = re.sub(r"[ \u00A0\u3000]+", " ", text)
    return text

# --- ここから: ingest0901.py を参考にしたプログラムによるAPI仕様書解析関数 ---

def _to_object_id_from_header(header: str) -> str:
    """
    '■Partオブジェクトのメソッド' → 'Part'
    末尾の 'オブジェクト' や 'のメソッド' を適宜落として Object 名を抽出
    """
    s = header.strip()
    s = re.sub(r"^■", "", s)
    s = s.replace("のメソッド", "")
    s = s.replace("オブジェクト", "")
    return s.strip()

def _guess_return_type_from_desc(desc: str) -> str:
    """
    返り値説明からおおまかに型を推定。
    ・'ID' / 'Id' / '要素ID' 含む → 'ID'
    ・それ以外は '不明'
    """
    d = desc or ""
    if re.search(r"\bID\b", d, flags=re.IGNORECASE) or ("要素ID" in d):
        return "ID"
    return "不明"

def _parse_api_specs(text: str) -> List[Dict[str, Any]]:
    """
    api.txt から構造化された配列を返す
    """
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
            i += 1
            # パラメータ収集開始
            while i < n:
                param_line = lines[i].strip()
                if closing_pat.search(param_line):
                    # 最後の行の処理
                    idx_close = param_line.rfind(")")
                    before = param_line[:idx_close]
                    if "//" in before: # パラメータがカッコ内にある場合
                         pm = param_pat.match(before)
                         if pm:
                            pname, ptype, pdesc = pm.groups()
                            current_entry["params"].append({"name": pname, "type": ptype.strip(), "description": pdesc.strip()})
                    entries.append(current_entry)
                    current_entry = None
                    break
                
                pm = param_pat.match(param_line)
                if pm:
                    pname, ptype, pdesc = pm.groups()
                    current_entry["params"].append(
                        {"name": pname, "type": ptype.strip(), "description": pdesc.strip()}
                    )
                i += 1
            i += 1
            continue
        i += 1
    return entries

def _parse_data_type_descriptions(text: str) -> Dict[str, str]:
    """
    api_arg.txt を解析し、データ型名とその説明の辞書を返す。
    """
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
    """
    仕様テキストからノード/リレーションのトリプルを生成する。
    """
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

        triples.append({"source": method_name, "source_type": "Method", "label": "BELONGS_TO", "target": obj_name, "target_type": "Object"})
        triples.append({"source": method_name, "source_type": "Method", "label": "HAS_RETURNS", "target": ret_node_id, "target_type": "ReturnValue"})
        triples.append({"source": ret_node_id, "source_type": "ReturnValue", "label": "HAS_TYPE", "target": cleaned_ret_type, "target_type": "DataType"})

        for i, p in enumerate(params):
            pname, ptype_raw, pdesc = p.get("name", "Param"), p.get("type", "型"), p.get("description", "")
            param_node_id = f"{method_name}_{pname}"
            node_props.setdefault(param_node_id, {"type": "Parameter", "properties": {"name": pname, "description": pdesc, "order": i}})
            cleaned_ptype = create_data_type_node(ptype_raw)
            triples.append({"source": method_name, "source_type": "Method", "label": "HAS_PARAMETER", "target": param_node_id, "target_type": "Parameter"})
            triples.append({"source": param_node_id, "source_type": "Parameter", "label": "HAS_TYPE", "target": cleaned_ptype, "target_type": "DataType"})
    return triples, node_props

def _triples_to_graph_documents(triples: List[Dict[str, Any]], node_props: Dict[str, Dict[str, Any]]) -> List[GraphDocument]:
    """
    トリプルとノード属性から GraphDocument 群を作る
    """
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
        source_node = node_map.get(t["source"]) or Node(id=t["source"], type=t["source_type"])
        target_node = node_map.get(t["target"]) or Node(id=t["target"], type=t["target_type"])
        rels.append(Relationship(source=source_node, target=target_node, type=t["label"], properties={}))
    
    doc = Document(page_content="API Spec and Example graph")
    gdoc = GraphDocument(nodes=list(node_map.values()), relationships=rels, source=doc)
    return [gdoc]

# --- ここまで: ingest0901.py を参考にしたプログラムによるAPI仕様書解析関数 ---
def _rebuild_graph_in_neo4j(graph_docs: List[GraphDocument]) -> Tuple[int, int]:
    """
    Neo4j をリセットしてから GraphDocument を投入する
    """
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


def _build_and_load_chroma(docs_for_vectorstore: List[Document]) -> None:
    """
    ドキュメントリストからベクトルDB (Chroma) を構築・永続化する
    """
    print("\n🚀 ChromaDBのベクトルデータを生成・保存中...")

    if CHROMA_PERSIST_DIR.exists():
        shutil.rmtree(CHROMA_PERSIST_DIR)
    CHROMA_PERSIST_DIR.mkdir(exist_ok=True)

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

# --- Neo4jグラフ構築関数 (修正) ---

def _build_and_load_neo4j() -> None:
    """
    API仕様書をプログラムで、スクリプト例をLLMで解析し、グラフを構築してNeo4jにロードする
    """
    gdocs = []  # 抽出したグラフデータを格納するリスト

    # --- 1. API仕様書をプログラムで解析 ---
    print("📄 API仕様書をプログラムで解析中...")
    try:
        api_text = _normalize_text(_read_api_text())
        api_arg_text = _normalize_text(_read_api_arg_text())
        
        type_descriptions = _parse_data_type_descriptions(api_arg_text)
        spec_triples, spec_node_props = extract_triples_from_specs(api_text, type_descriptions)
        
        spec_gdocs = _triples_to_graph_documents(spec_triples, spec_node_props)
        gdocs.extend(spec_gdocs)
        print(f"✔ API仕様書からプログラムでトリプルを抽出: {len(spec_triples)} 件")
    except FileNotFoundError as e:
        print(f"⚠ API仕様書ファイルが見つからないため、解析をスキップします: {e}")

    # --- 2. スクリプト例をLLMで解析 ---
    print("\n🐍 スクリプト例を読み込み、LLMで解析中...")
    script_docs = []
    script_files = _read_script_files()
    for script_name, script_content in script_files:
        script_docs.append(Document(page_content=script_content, metadata={"source": script_name}))
    
    if script_docs:
        print(f"   - {len(script_docs)}件のスクリプトを対象にグラフデータを抽出中...")
        llm = ChatOpenAI(temperature=1, model_name="gpt-5-mini", openai_api_key=OPENAI_API_KEY)
        
        # スクリプト例用のプロンプト
        script_prompt = ChatPromptTemplate.from_messages(
            [
                ("system",
                 """
                 あなたは、Pythonスクリプトを解析し、関数やクラスの利用関係を知識グラフとして抽出する専門家です。
                 どのスクリプトがどの関数を呼び出しているかを特定してください。

                 # 知識グラフのスキーマ定義
                 - ノード "Script": 処理が記述されたスクリプトファイル。
                 - ノード "Function": スクリプト内で使用される関数。
                 - 関係 "USES": Script -> Function (スクリプトが関数を使用する)
                 - 関係 "CALLS": Function -> Function (関数が別の関数を呼び出す)
                 
                 # 指示
                 - 上記のスキーマに厳密に従ってください。
                 - スクリプトファイル名と、そこで利用されている関数名の関係を抽出することに集中してください。
                 """),
                ("human", "以下のスクリプトから知識グラフを生成してください:\n\n{input}"),
            ]
        )
        script_transformer = LLMGraphTransformer(llm=llm, prompt=script_prompt)
        script_gdocs = script_transformer.convert_to_graph_documents(script_docs)
        gdocs.extend(script_gdocs)
        print(f"✔ スクリプト例からグラフデータを抽出しました。")
    else:
        print("   - 解析対象のスクリプト例が見つかりませんでした。")

    # --- 3. Neo4jへのデータ投入 ---
    if not gdocs:
        print("\n⚠ グラフデータが生成されなかったため、Neo4jの更新をスキップします。")
        return
        
    try:
        node_count, rel_count = _rebuild_graph_in_neo4j(gdocs)
        print(f"✔ グラフデータベースの再構築が完了しました: ノード={node_count}, リレーションシップ={rel_count}")
    except ServiceUnavailable as se:
        print(f"⚠ Neo4j への接続に失敗しました: {se}")
        print("   Neo4jサーバーが起動しているか、接続情報を確認してください。")
    except Exception as e:
        print(f"⚠ グラフデータベースの構築中にエラーが発生しました: {e}")

# --- main関数 (変更なし) ---

def main() -> None:
    """
    メイン処理
    """
    # グラフデータベース (Neo4j) を構築
    _build_and_load_neo4j()

    # ベクトルデータベース (Chroma) を構築
    print("\n--- ChromaDB構築プロセス ---")
    
    docs_for_vectorstore: List[Document] = []
    
    # 1. API仕様からドキュメントを生成
    try:
        api_text = _read_api_text()
        content_api = _normalize_text(api_text)
        docs_for_vectorstore.append(Document(
            page_content=content_api, 
            metadata={"source": "api_spec"}
        ))
        print(f"✔ API仕様書からドキュメントを1件作成しました。")
    except FileNotFoundError:
        print("⚠ API仕様書が見つからないため、Chromaへの登録をスキップします。")

    # 2. スクリプト例からドキュメントを生成
    script_files = _read_script_files()
    if script_files:
        for script_name, script_content in script_files:
            content = (
                f"スクリプト例: {script_name}\n\n```python\n{script_content}\n```"
            )
            metadata = {
                "source": "script_example",
                "script_name": script_name,
            }
            docs_for_vectorstore.append(Document(page_content=content, metadata=metadata))
        print(f"✔ {len(script_files)}件のスクリプト例からドキュメントを作成しました。")
    else:
        print("⚠ スクリプト例ファイルが見つかりませんでした。")
    
    # 情報を渡してChromaDBを構築
    if docs_for_vectorstore:
        _build_and_load_chroma(docs_for_vectorstore)
    else:
        print("⚠ ChromaDBに登録するドキュメントがありませんでした。")


if __name__ == "__main__":
    main()