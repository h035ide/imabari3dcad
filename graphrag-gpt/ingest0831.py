from tree_sitter import Language, Parser
import tree_sitter_python as tspython

from pathlib import Path
import re
import json
from typing import List, Dict, Any, Optional, Tuple
import shutil

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
    
    # data ディレクトリ内の .py ファイルを探索
    for p in DATA_DIR.glob("*.py"):
        if p.is_file():
            # (ファイル名, ファイルの内容) のタプルを追加
            script_files.append((p.name, p.read_text(encoding="utf-8")))
            
    return script_files

def _normalize_text(text: str) -> str:
    """
    改行/タブ/空白の揺れを正規化。
    - Windows系改行を \n に
    - 行末の空白除去
    - タブ→半角スペース
    - 連続空白（NBSP, 全角スペース含む）→半角スペース1個
    - BOM除去
    """
    text = text.replace("\ufeff", "")  # BOM
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = text.replace("\t", " ")
    text = re.sub(r"[ \u00A0\u3000]+", " ", text)
    return text

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
    api.txt から以下の構造の配列を返す:
    [
      {
        "object": "Part",
        "title_jp": "船殻のプレートソリッド要素を作成する",
        "name": "CreatePlate",
        "return_desc": "作成したソリッド要素のID",
        "return_type": "ID",
        "params": [
          {"name": "...", "type": "...", "description": "..."},
          ...
        ],
      },
      ...
    ]
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
    """
    api_arg.txt を解析し、データ型名とその説明の辞書を返す。
    例: {"文字列": "通常の文字列", "浮動小数点": "通常の数値", ...}
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
    DataTypeノードにはapi_arg.txtから抽出した説明(description)を追加する。
    返却:
      triples: [
        {"source": "...", "source_type": "...", "label": "HAS_PARAMETER", "target": "...", "target_type": "..."},
        ...
      ]
      node_props: {
        "Part": {"type": "Object", "properties": {...}},
        "CreatePlate": {"type": "Method", "properties": {...}},
        "文字列": {"type": "DataType", "properties": {"name": "文字列", "description": "通常の文字列"}},
        ...
      }
    """
    entries = _parse_api_specs(api_text)

    triples: List[Dict[str, Any]] = []
    node_props: Dict[str, Dict[str, Any]] = {}

    def _clean_type_name(type_name: str) -> str:
        """'点(2D)' -> '点', '要素(配列)' -> '要素' のように型名から括弧書きを削除する"""
        return re.sub(r"\s*\(.+\)$", "", type_name).strip()

    def create_data_type_node(raw_type_name: str) -> str:
        """
        DataTypeノードの定義を作成し、クリーンな型名を返す。
        ノードが既に存在する場合は何もしない。
        """
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

        # ノード定義
        node_props.setdefault(obj_name, {"type": "Object", "properties": {"name": obj_name}})
        node_props.setdefault(method_name, {"type": "Method", "properties": {"name": method_name, "description": title_jp}})
        ret_node_id = f"{method_name}_ReturnValue"
        node_props.setdefault(ret_node_id, {"type": "ReturnValue", "properties": {"description": ret_desc}})
        
        # 返り値のDataTypeノードを作成
        cleaned_ret_type = create_data_type_node(ret_type_raw)

        # 関係: Method -> Object
        triples.append({
            "source": method_name, "source_type": "Method",
            "label": "BELONGS_TO", "target": obj_name, "target_type": "Object"
        })

        # 関係: Method -HAS_RETURNS-> ReturnValue
        triples.append({
            "source": method_name, "source_type": "Method",
            "label": "HAS_RETURNS", "target": ret_node_id, "target_type": "ReturnValue"
        })

        # 関係: ReturnValue -HAS_TYPE-> DataType
        triples.append({
            "source": ret_node_id, "source_type": "ReturnValue",
            "label": "HAS_TYPE", "target": cleaned_ret_type, "target_type": "DataType"
        })

        # パラメータ
        for i, p in enumerate(params):
            pname = p.get("name") or "Param"
            ptype_raw = p.get("type") or "型"
            pdesc = p.get("description") or ""

            param_node_id = f"{method_name}_{pname}"

            # パラメータノードを定義
            node_props.setdefault(param_node_id, {
                "type": "Parameter",
                "properties": {
                    "name": pname,
                    "description": pdesc,
                    "order": i
                }
            })
            
            # パラメータのDataTypeノードを作成
            cleaned_ptype = create_data_type_node(ptype_raw)

            # 関係: Method -> Parameter
            triples.append({
                "source": method_name, "source_type": "Method",
                "label": "HAS_PARAMETER", "target": param_node_id, "target_type": "Parameter"
            })
            # 関係: Parameter -> DataType
            triples.append({
                "source": param_node_id, "source_type": "Parameter",
                "label": "HAS_TYPE", "target": cleaned_ptype, "target_type": "DataType"
            })

    return triples, node_props

def _extract_method_calls_from_script(script_text: str) -> List[Dict[str, str]]:
    """
    tree-sitter を使ってスクリプトからAPIメソッドの呼び出しを抽出する
    """
    tree = parser.parse(bytes(script_text, "utf8"))
    root_node = tree.root_node
    
    calls = []
    
    def find_calls(node):
        if node.type == 'call':
            # `object.method()` の形式を特定
            function_node = node.child_by_field_name('function')
            if function_node and function_node.type == 'attribute':
                obj_node = function_node.child_by_field_name('object')
                method_node = function_node.child_by_field_name('attribute')
                args_node = node.child_by_field_name('arguments')
                
                if obj_node and method_node and args_node:
                    call_info = {
                        "object_name": obj_node.text.decode('utf8'),
                        "method_name": method_node.text.decode('utf8'),
                        "arguments": args_node.text.decode('utf8'),
                        "full_text": node.text.decode('utf8'),
                    }
                    calls.append(call_info)

        for child in node.children:
            find_calls(child)

    find_calls(root_node)
    return calls

def extract_triples_from_script(
    script_path: str, script_text: str
) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """
    スクリプト例のテキストから、ノード/リレーションのトリプルを生成する
    """
    method_calls = _extract_method_calls_from_script(script_text)

    triples: List[Dict[str, Any]] = []
    node_props: Dict[str, Dict[str, Any]] = {}
    
    # スクリプト全体を表すノード
    script_node_id = script_path
    node_props[script_node_id] = {
        "type": "ScriptExample",
        "properties": {"name": script_path}
    }
    
    prev_call_node_id = None
    
    for i, call in enumerate(method_calls):
        method_name = call["method_name"]
        call_node_id = f"{script_path}_call_{i}"
        
        ### ▼▼▼ ここから修正 ▼▼▼
        # メソッド呼び出しノード
        # プロパティを'code'に一本化し、冗長な'arguments'を削除
        node_props[call_node_id] = {
            "type": "MethodCall",
            "properties": {
                "code": call["full_text"], # プロパティ名を 'name' から 'code' に変更し、完全なテキストを格納
                "order": i
                # "arguments": call["arguments"] <-- この行を削除
            }
        }
        ### ▲▲▲ 修正ここまで ▲▲▲
        
        # 関係: ScriptExample -CONTAINS-> MethodCall
        triples.append({
            "source": script_node_id, "source_type": "ScriptExample",
            "label": "CONTAINS", "target": call_node_id, "target_type": "MethodCall"
        })
        
        # 関係: MethodCall -CALLS-> Method (API仕様書で定義されたメソッド)
        # 既存のMethodノードに接続する
        triples.append({
            "source": call_node_id, "source_type": "MethodCall",
            "label": "CALLS", "target": method_name, "target_type": "Method"
        })
        
        # 関係: MethodCall -NEXT-> MethodCall (呼び出し順序)
        if prev_call_node_id:
            triples.append({
                "source": prev_call_node_id, "source_type": "MethodCall",
                "label": "NEXT", "target": call_node_id, "target_type": "MethodCall"
            })
        
        prev_call_node_id = call_node_id

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


def _build_and_load_chroma_from_specs(entries: List[Dict[str, Any]]) -> None:
    """
    仕様エントリからベクトルDB (Chroma) を構築・永続化する
    """
    print("\n🚀 ChromaDBのベクトルデータを生成・保存中...")

    if CHROMA_PERSIST_DIR.exists():
        shutil.rmtree(CHROMA_PERSIST_DIR)
    CHROMA_PERSIST_DIR.mkdir(exist_ok=True)

    docs_for_vectorstore: List[Document] = []
    for entry in entries:
        content_parts = [
            f"オブジェクト: {entry['object']}",
            f"メソッド名: {entry['name']}",
            f"説明: {entry['title_jp']}",
            f"返り値: {entry['return_desc']}",
        ]
        if entry['params']:
            param_texts = [f"- {p['name']} ({p['type']}): {p['description']}" for p in entry['params']]
            content_parts.append("パラメータ:\n" + "\n".join(param_texts))
        
        content = "\n".join(content_parts)

        metadata = {
            "object": entry['object'],
            "method_name": entry['name'],
        }
        
        docs_for_vectorstore.append(Document(page_content=content, metadata=metadata))

    try:
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        vectorstore = Chroma.from_documents(
            documents=docs_for_vectorstore,
            embedding=embeddings,
            persist_directory=str(CHROMA_PERSIST_DIR)
        )
        print(f"✔ Chroma DB created and persisted with {len(docs_for_vectorstore)} documents at: {CHROMA_PERSIST_DIR}")
    except Exception as e:
        print(f"⚠ Chroma DBの作成に失敗しました: {e}")

### ▼▼▼ 変更点 2: グラフ構築処理の修正 ▼▼▼
def _build_and_load_neo4j() -> None:
    # --- 1. API仕様書 (api.txt, api_arg.txt) の解析 ---
    print("📄 API仕様書を解析中...")
    api_text = _read_api_text()
    api_text = _normalize_text(api_text)
    api_arg_text = _read_api_arg_text()
    type_descriptions = _parse_data_type_descriptions(api_arg_text)
    
    # API仕様書からトリプルとノードプロパティを抽出
    spec_triples, spec_node_props = extract_triples_from_specs(api_text, type_descriptions)
    print(f"✔ API仕様書からトリプルを抽出: {len(spec_triples)} 件")

    # --- 2. スクリプト例 (data/*.py) の解析 ---
    print("\n🐍 スクリプト例 (data/*.py) を解析中...")
    script_files = _read_script_files()
    
    # .py ファイルが存在しない場合はスキップ
    if not script_files:
        print("⚠ data ディレクトリに解析対象の .py ファイルが見つかりませんでした。スクリプト例の解析をスキップします。")
        script_triples, script_node_props = [], {}
    else:
        # 見つかった全スクリプトの情報を集約する変数
        all_script_triples = []
        all_script_node_props = {}
        
        # 各スクリプトファイルをループで解析
        for script_path, script_text in script_files:
            print(f"  - ファイルを解析中: {script_path}")
            # スクリプトからトリプルとノードプロパティを抽出
            triples, node_props = extract_triples_from_script(script_path, script_text)
            all_script_triples.extend(triples)
            all_script_node_props.update(node_props)
            
        script_triples = all_script_triples
        script_node_props = all_script_node_props
        print(f"✔ スクリプト例からトリプルを総計: {len(script_triples)} 件")


    # --- 3. データの統合とグラフ構築 ---
    print("\n🔗 データを統合してグラフを構築中...")
    # API仕様とスクリプト例のデータを結合
    all_triples = spec_triples + script_triples
    # ノードプロパティをマージ (スクリプト例のデータで上書き)
    all_node_props = spec_node_props
    all_node_props.update(script_node_props)

    gdocs = _triples_to_graph_documents(all_triples, all_node_props)

    try:
        node_count, rel_count = _rebuild_graph_in_neo4j(gdocs)
        print(f"✔ グラフデータベースの再構築が完了しました: ノード={node_count}, リレーションシップ={rel_count}")
    except ServiceUnavailable as se:
        print(f"⚠ Neo4j への接続に失敗しました: {se}")
        print("   Neo4jサーバーが起動しているか確認してください。")
    except Exception as e:
        print(f"⚠ グラフデータベースの構築中にエラーが発生しました: {e}")
### ▲▲▲ 変更ここまで ▲▲▲

def main() -> None:
    # グラフデータベース (Neo4j) を構築
    _build_and_load_neo4j()

    # ベクトルデータベース (Chroma) を構築
    # (これはAPI仕様書の情報のみで行う)
    api_text = _read_api_text()
    api_text = _normalize_text(api_text)
    api_entries = _parse_api_specs(api_text)
    _build_and_load_chroma_from_specs(api_entries)

if __name__ == "__main__":
    main()