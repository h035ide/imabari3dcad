from tree_sitter import Language, Parser
import tree_sitter_python as tspython

from pathlib import Path
import re
from typing import List, Dict, Optional, Tuple, Protocol, Union, Any
import shutil
import logging
import json
from datetime import datetime

from langchain_core.documents import Document
from langchain_neo4j import Neo4jGraph
from neo4j.exceptions import ServiceUnavailable
from langchain_neo4j.graphs.graph_document import GraphDocument, Node, Relationship
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# tree-sitterのPython用パーサーをセットアップ
PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

logger = logging.getLogger(__name__)


class IngestConfigProtocol(Protocol):
    @property
    def neo4j_uri(self) -> str: ...

    @property
    def neo4j_user(self) -> str: ...

    @property
    def neo4j_password(self) -> str: ...

    @property
    def neo4j_database(self) -> str: ...

    @property
    def api_document_dir(self) -> Union[str, Path]: ...

    @property
    def chroma_persist_directory(self) -> Union[str, Path]: ...

    @property
    def langchain_embedding_config(self) -> Dict[str, Any]: ...

    @property
    def openai_api_key(self) -> Optional[str]: ...


# Entity抽出用のキーワードを定義
# グラフをリッチ化するために、APIドキュメントから抽出するCAD関連の専門用語を定義
ENTITY_KEYWORDS = [
    "プレート",
    "ソリッド",
    "要素",
    "座標",
    "点",
    "線",
    "カーブ",
    "平面",
    "船殻",
    "部材",
    "ブロック",
    "パネル",
    "ドキュメント",
    "パート",
    "オブジェクト",
]


def _read_api_text(data_dir: Path) -> str:
    """api.txt を候補パスから読み込む"""
    api_txt_candidates = [
        data_dir / "api.txt",
        Path("api.txt"),
        Path("/mnt/data/api.txt"),
    ]
    for p in api_txt_candidates:
        if p.exists():
            return p.read_text(encoding="utf-8")
    raise FileNotFoundError(
        "api.txt が見つかりませんでした。次のパスを確認してください: "
        f"{[str(p) for p in api_txt_candidates]}"
    )


def _read_api_arg_text(data_dir: Path) -> str:
    """api_arg.txt を候補パスから読み込む"""
    api_arg_txt_candidates = [
        data_dir / "api_arg.txt",
        Path("api_arg.txt"),
        Path("/mnt/data/api_arg.txt"),
    ]
    for p in api_arg_txt_candidates:
        if p.exists():
            return p.read_text(encoding="utf-8")
    raise FileNotFoundError(
        "api_arg.txt が見つかりませんでした。次のパスを確認してください: "
        f"{[str(p) for p in api_arg_txt_candidates]}"
    )


def _read_script_files(data_dir: Path) -> List[Tuple[str, str]]:
    """data ディレクトリ内の .py ファイルをすべて読み込む"""
    script_files = []
    if not data_dir.exists():
        logger.warning(
            f"{data_dir} ディレクトリが存在しません。スクリプト例の解析をスキップします。"
        )
        return []

    # data ディレクトリ内の .py ファイルを探索
    for p in data_dir.glob("*.py"):
        if p.is_file():
            try:
                # (ファイル名, ファイルの内容) のタプルを追加
                script_files.append((p.name, p.read_text(encoding="utf-8")))
            except Exception as e:
                print(f"⚠ ファイル {p.name} の読み込みに失敗しました: {e}")
                continue

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
                        {
                            "name": pname,
                            "type": ptype.strip(),
                            "description": pdesc.strip(),
                        }
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


# グラフデータのリッチ化を行う関数をリファクタリング
def extract_triples_from_specs(
    api_text: str, type_descriptions: Dict[str, str]
) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """
    仕様テキストからノード/リレーションのトリプルを生成する。
    DataTypeノードにはapi_arg.txtから抽出した説明(description)を追加する。
    変更点: ConceptノードとEntityノードを追加し、グラフをリッチ化
    """
    entries = _parse_api_specs(api_text)

    triples: List[Dict[str, Any]] = []
    node_props: Dict[str, Dict[str, Any]] = {}

    def _clean_type_name(type_name: str) -> str:
        """'点(2D)' -> '点', '要素(配列)' -> '要素' のように型名から括弧書きを削除する"""
        return re.sub(r"\s*\(.+\)$", "", type_name).strip()

    def create_data_type_node(raw_type_name: str) -> str:
        """DataTypeノードの定義を作成し、クリーンな型名を返す。"""
        cleaned_type_name = _clean_type_name(raw_type_name)
        if cleaned_type_name not in node_props:
            properties = {"name": cleaned_type_name}
            description = type_descriptions.get(cleaned_type_name)
            if description:
                properties["description"] = description
            node_props[cleaned_type_name] = {
                "type": "DataType",
                "properties": properties,
            }
        return cleaned_type_name

    def _extract_concept_from_title(title: str) -> Optional[str]:
        """メソッドの日本語説明から、目的となるコンセプトを簡易的に抽出する"""
        if not title:
            return None
        # 例: 「船殻のプレートソリッド要素を作成する」 -> 「船殻プレートソリッド要素作成」
        #      「座標を取得する」 -> 「座標取得」
        verbs_to_remove = [
            "を作成する",
            "を取得する",
            "を設定する",
            "にする",
            "を返す",
            "する",
        ]
        processed_title = title
        for verb in verbs_to_remove:
            if processed_title.endswith(verb):
                processed_title = processed_title[: -len(verb)]
                break
        return processed_title.replace("の", "") + "機能"  # コンセプト名を明確化

    def _find_entities_in_text(text: str) -> List[str]:
        """テキスト内から定義済みのEntityキーワードを探す"""
        found_entities = set()
        for keyword in ENTITY_KEYWORDS:
            if keyword in text:
                found_entities.add(keyword)
        return list(found_entities)

    for e in entries:
        obj_name = e["object"] or "Object"
        method_name = e["name"]
        title_jp = e.get("title_jp", "")
        ret_desc = e.get("return_desc", "")
        ret_type_raw = e.get("return_type", "不明")
        params = e.get("params", [])

        # --- 基本的なノード定義 ---
        node_props.setdefault(
            obj_name, {"type": "Object", "properties": {"name": obj_name}}
        )
        node_props.setdefault(
            method_name,
            {
                "type": "Method",
                "properties": {"name": method_name, "description": title_jp},
            },
        )
        ret_node_id = f"{method_name}_ReturnValue"
        node_props.setdefault(
            ret_node_id,
            {"type": "ReturnValue", "properties": {"description": ret_desc}},
        )
        cleaned_ret_type = create_data_type_node(ret_type_raw)

        # --- 基本的な関係定義 ---
        triples.append(
            {
                "source": method_name,
                "source_type": "Method",
                "label": "BELONGS_TO",
                "target": obj_name,
                "target_type": "Object",
            }
        )
        triples.append(
            {
                "source": method_name,
                "source_type": "Method",
                "label": "HAS_RETURNS",
                "target": ret_node_id,
                "target_type": "ReturnValue",
            }
        )
        triples.append(
            {
                "source": ret_node_id,
                "source_type": "ReturnValue",
                "label": "HAS_TYPE",
                "target": cleaned_ret_type,
                "target_type": "DataType",
            }
        )

        # --- Conceptノードの追加 ---
        concept_name = _extract_concept_from_title(title_jp)
        if concept_name:
            node_props.setdefault(
                concept_name, {"type": "Concept", "properties": {"name": concept_name}}
            )
            triples.append(
                {
                    "source": method_name,
                    "source_type": "Method",
                    "label": "PERFORMS_ACTION",
                    "target": concept_name,
                    "target_type": "Concept",
                }
            )

        # --- Entityノードの追加 (Method) ---
        method_entities = _find_entities_in_text(title_jp)
        for entity_name in method_entities:
            node_props.setdefault(
                entity_name, {"type": "Entity", "properties": {"name": entity_name}}
            )
            triples.append(
                {
                    "source": method_name,
                    "source_type": "Method",
                    "label": "RELATES_TO",
                    "target": entity_name,
                    "target_type": "Entity",
                }
            )

        # --- パラメータと関連Entityの処理 ---
        for i, p in enumerate(params):
            pname = p.get("name") or "Param"
            ptype_raw = p.get("type") or "型"
            pdesc = p.get("description") or ""
            param_node_id = f"{method_name}_{pname}"

            # パラメータノードを定義
            node_props.setdefault(
                param_node_id,
                {
                    "type": "Parameter",
                    "properties": {"name": pname, "description": pdesc, "order": i},
                },
            )
            cleaned_ptype = create_data_type_node(ptype_raw)

            # 関係: Method -> Parameter, Parameter -> DataType
            triples.append(
                {
                    "source": method_name,
                    "source_type": "Method",
                    "label": "HAS_PARAMETER",
                    "target": param_node_id,
                    "target_type": "Parameter",
                }
            )
            triples.append(
                {
                    "source": param_node_id,
                    "source_type": "Parameter",
                    "label": "HAS_TYPE",
                    "target": cleaned_ptype,
                    "target_type": "DataType",
                }
            )

            # --- Entityノードの追加 (Parameter) ---
            param_entities = _find_entities_in_text(pdesc)
            for entity_name in param_entities:
                node_props.setdefault(
                    entity_name, {"type": "Entity", "properties": {"name": entity_name}}
                )
                triples.append(
                    {
                        "source": param_node_id,
                        "source_type": "Parameter",
                        "label": "RELATES_TO",
                        "target": entity_name,
                        "target_type": "Entity",
                    }
                )

    return triples, node_props


def _extract_method_calls_from_script(script_text: str) -> List[Dict[str, str]]:
    """
    tree-sitter を使ってスクリプトからAPIメソッドの呼び出しを抽出する
    """
    tree = parser.parse(bytes(script_text, "utf8"))
    root_node = tree.root_node

    calls = []

    def find_calls(node):
        if node.type == "call":
            # `object.method()` の形式を特定
            function_node = node.child_by_field_name("function")
            if function_node and function_node.type == "attribute":
                obj_node = function_node.child_by_field_name("object")
                method_node = function_node.child_by_field_name("attribute")
                args_node = node.child_by_field_name("arguments")

                if obj_node and method_node and args_node:
                    call_info = {
                        "object_name": obj_node.text.decode("utf8"),
                        "method_name": method_node.text.decode("utf8"),
                        "arguments": args_node.text.decode("utf8"),
                        "full_text": node.text.decode("utf8"),
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
        "properties": {"name": script_path},
    }

    prev_call_node_id = None

    for i, call in enumerate(method_calls):
        method_name = call["method_name"]
        call_node_id = f"{script_path}_call_{i}"

        # メソッド呼び出しノード
        node_props[call_node_id] = {
            "type": "MethodCall",
            "properties": {"code": call["full_text"], "order": i},
        }

        # 関係: ScriptExample -CONTAINS-> MethodCall
        triples.append(
            {
                "source": script_node_id,
                "source_type": "ScriptExample",
                "label": "CONTAINS",
                "target": call_node_id,
                "target_type": "MethodCall",
            }
        )

        # 関係: MethodCall -CALLS-> Method (API仕様書で定義されたメソッド)
        triples.append(
            {
                "source": call_node_id,
                "source_type": "MethodCall",
                "label": "CALLS",
                "target": method_name,
                "target_type": "Method",
            }
        )

        # 関係: MethodCall -NEXT-> MethodCall (呼び出し順序)
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

    return triples, node_props


def _triples_to_graph_documents(
    triples: List[Dict[str, Any]], node_props: Dict[str, Dict[str, Any]]
) -> List[GraphDocument]:
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
                source=source_node, target=target_node, type=t["label"], properties={}
            )
        )

    doc = Document(page_content="API Spec and Example graph")
    gdoc = GraphDocument(nodes=list(node_map.values()), relationships=rels, source=doc)
    return [gdoc]


def _rebuild_graph_in_neo4j(
    graph_docs: List[GraphDocument], config: IngestConfigProtocol
) -> Tuple[int, int]:
    """
    Neo4j をリセットしてから GraphDocument を投入する
    """
    # 設定の確認
    if not all([config.neo4j_uri, config.neo4j_user, config.neo4j_password]):
        raise ValueError(
            "Neo4j接続情報が設定されていません。設定を確認してください。"
        )

    try:
        graph = Neo4jGraph(
            url=config.neo4j_uri,
            username=config.neo4j_user,
            password=config.neo4j_password,
            database=config.neo4j_database,
        )

        print("🧹 Neo4jの既存データを削除中...")
        delete_query = "MATCH (n) DETACH DELETE n"
        graph.query(delete_query)

        print("\n🚀 Neo4jにデータを投入中...")

        graph.add_graph_documents(graph_docs)

        res_nodes = graph.query("MATCH (n) RETURN count(n) AS c")
        res_rels = graph.query("MATCH ()-[r]->() RETURN count(r) AS c")
        return int(res_nodes[0]["c"]), int(res_rels[0]["c"])
    except Exception as e:
        print(f"⚠ Neo4j接続エラー: {e}")
        raise


def _export_neo4j_to_text(
    config: IngestConfigProtocol, out_dir: Path
) -> Tuple[Path, Path]:
    """Neo4j内のノード/リレーションをJSONLでエクスポートする。

    nodes.jsonl: {id, labels, properties}
    relationships.jsonl: {id, type, start, end, properties}
    """
    if not all([config.neo4j_uri, config.neo4j_user, config.neo4j_password]):
        raise ValueError("Neo4j接続情報が未設定です")

    graph = Neo4jGraph(
        url=config.neo4j_uri,
        username=config.neo4j_user,
        password=config.neo4j_password,
        database=config.neo4j_database,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    nodes_path = out_dir / f"nodes_{ts}.jsonl"
    rels_path = out_dir / f"relationships_{ts}.jsonl"

    # ノードをエクスポート（elementId を使用）
    with nodes_path.open("w", encoding="utf-8") as f_nodes:
        result = graph.query(
            "MATCH (n) RETURN elementId(n) AS element_id, labels(n) AS labels, properties(n) AS props"
        )
        for row in result:
            rec = {
                "element_id": row["element_id"],
                "labels": row["labels"],
                "properties": row["props"],
            }
            f_nodes.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # リレーションをエクスポート（elementId を使用）
    with rels_path.open("w", encoding="utf-8") as f_rels:
        query = (
            "MATCH (a)-[r]->(b) "
            "RETURN elementId(r) AS element_id, type(r) AS type, "
            "elementId(a) AS start_element_id, elementId(b) AS end_element_id, properties(r) AS props"
        )
        result = graph.query(query)
        for row in result:
            rec = {
                "element_id": row["element_id"],
                "type": row["type"],
                "start_element_id": row["start_element_id"],
                "end_element_id": row["end_element_id"],
                "properties": row["props"],
            }
            f_rels.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return nodes_path, rels_path


def _build_and_load_chroma(
    api_entries: List[Dict[str, Any]],
    script_files: List[Tuple[str, str]],
    config: IngestConfigProtocol
) -> None:
    """
    API仕様とスクリプト例からベクトルDB (Chroma) を構築・永続化する
    """
    logger.info("ChromaDBのベクトルデータを生成・保存中...")

    # OpenAI APIキーの確認
    if not config.openai_api_key:
        logger.warning("OpenAI APIキーが設定されていません。ChromaDBの作成をスキップします。")
        return

    chroma_persist_dir = Path(config.chroma_persist_directory)
    if chroma_persist_dir.exists():
        shutil.rmtree(chroma_persist_dir)
    chroma_persist_dir.mkdir(exist_ok=True)

    docs_for_vectorstore: List[Document] = []

    # 1. API仕様からドキュメントを生成
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
            "source": "api_spec",
            "object": entry["object"],
            "method_name": entry["name"],
        }
        docs_for_vectorstore.append(Document(page_content=content, metadata=metadata))

    # 2. スクリプト例からドキュメントを生成
    for script_name, script_content in script_files:
        content = f"スクリプト例: {script_name}\n\n```python\n{script_content}\n```"
        metadata = {
            "source": "script_example",
            "script_name": script_name,
        }
        docs_for_vectorstore.append(Document(page_content=content, metadata=metadata))

    try:
        embeddings = OpenAIEmbeddings(**config.langchain_embedding_config)  # type: ignore[arg-type]
        # 設定のコレクション名に統一（存在しない場合は既定値を使用）
        collection_name = getattr(config, "chroma_collection_name", "api_documentation")
        Chroma.from_documents(
            documents=docs_for_vectorstore,
            embedding=embeddings,
            persist_directory=str(chroma_persist_dir),
            collection_name=collection_name,
        )
        logger.info(
            f"Chroma DB created and persisted with {len(docs_for_vectorstore)} documents at: "
            f"{chroma_persist_dir} (collection={collection_name})"
        )
    except Exception as e:
        msg = f"Chroma DBの作成に失敗しました: {e}"
        logger.error(msg)


def _build_and_load_neo4j_from_docs(
    graph_docs: List[GraphDocument], config: IngestConfigProtocol
) -> None:
    """準備済みの GraphDocument を Neo4j に投入する"""
    try:
        node_count, rel_count = _rebuild_graph_in_neo4j(graph_docs, config)
        logger.info(
            f"グラフデータベースの再構築が完了しました: ノード={node_count}, リレーションシップ={rel_count}"
        )
    except ServiceUnavailable as se:
        logger.error(f"Neo4j への接続に失敗しました: {se}")
        logger.error("Neo4jサーバーが起動しているか確認してください。")
    except Exception as e:
        logger.error(f"グラフデータベースの構築中にエラーが発生しました: {e}")
        logger.error(f"エラー詳細: {str(e)}")


def _dump_preprocessed_artifacts(
    out_dir: Path,
    api_entries: List[Dict[str, Any]],
    type_descriptions: Dict[str, str],
    spec_triples: List[Dict[str, Any]],
    spec_node_props: Dict[str, Dict[str, Any]],
    script_triples: List[Dict[str, Any]],
    script_node_props: Dict[str, Dict[str, Any]],
) -> None:
    """前処理の成果物をJSONで書き出す。

    - api_entries.json: _parse_api_specs の結果
    - type_descriptions.json: _parse_data_type_descriptions の結果
    - graph_specs.json: 仕様由来のトリプル/ノード
    - graph_scripts.json: スクリプト由来のトリプル/ノード
    - graph_all.json: 統合（トリプル/ノード）
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    def _dump(obj: Any, name: str) -> None:
        (out_dir / name).write_text(
            json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    _dump(api_entries, "api_entries.json")
    _dump(type_descriptions, "type_descriptions.json")
    _dump({"triples": spec_triples, "nodes": spec_node_props}, "graph_specs.json")
    _dump({"triples": script_triples, "nodes": script_node_props}, "graph_scripts.json")

    # 統合ビュー
    all_triples = list(spec_triples) + list(script_triples)
    all_nodes = dict(spec_node_props)
    all_nodes.update(script_node_props)
    _dump({"triples": all_triples, "nodes": all_nodes}, "graph_all.json")


def build_databases(config: IngestConfigProtocol) -> bool:
    """データベース構築のメイン処理（Configベース）"""
    logger.info("データベース構築プロセスを開始します...")

    try:
        # Config の api_document_dir は文字列の可能性があるため Path に正規化
        data_dir = Path(config.api_document_dir)

        # --- 1. API仕様書と型定義の読み込み・解析（1回だけ） ---
        logger.info("API仕様書を解析中...")
        api_text = _normalize_text(_read_api_text(data_dir))
        api_arg_text = _read_api_arg_text(data_dir)
        type_descriptions = _parse_data_type_descriptions(api_arg_text)
        api_entries = _parse_api_specs(api_text)
        logger.info(f"{len(api_entries)}件のAPI仕様を解析しました。")

        # 仕様からトリプル生成
        spec_triples, spec_node_props = extract_triples_from_specs(
            api_text, type_descriptions
        )

        # --- 2. スクリプト例の読み込み・解析（1回だけ） ---
        logger.info("スクリプト例 (data/*.py) を解析中...")
        script_files = _read_script_files(data_dir)
        if script_files:
            logger.info(f"{len(script_files)}件のスクリプト例を読み込みました。")
            all_script_triples: List[Dict[str, Any]] = []
            all_script_node_props: Dict[str, Dict[str, Any]] = {}
            for script_path, script_text in script_files:
                logger.info(f"ファイルを解析中: {script_path}")
                triples, node_props = extract_triples_from_script(
                    script_path, script_text
                )
                all_script_triples.extend(triples)
                all_script_node_props.update(node_props)
            script_triples = all_script_triples
            script_node_props = all_script_node_props
            logger.info(f"スクリプト例からトリプルを総計: {len(script_triples)} 件")
        else:
            logger.warning("data ディレクトリに解析対象の .py ファイルが見つかりませんでした。スクリプト例の解析をスキップします。")
            script_triples, script_node_props = [], {}

        # --- 3. 前処理結果をファイル出力（Neo4j投入の前） ---
        try:
            dump_dir = Path(config.api_document_dir) / "preprocessed"
            _dump_preprocessed_artifacts(
                out_dir=dump_dir,
                api_entries=api_entries,
                type_descriptions=type_descriptions,
                spec_triples=spec_triples,
                spec_node_props=spec_node_props,
                script_triples=script_triples,
                script_node_props=script_node_props,
            )
            logger.info(f"前処理成果物を出力しました: {dump_dir}")
        except Exception as e:
            logger.warning(f"前処理成果物の出力に失敗しました: {e}")

        # --- 4. データ統合 → GraphDocument 構築 → Neo4j投入 ---
        logger.info("データを統合してグラフを構築中...")
        all_triples = spec_triples + script_triples
        all_node_props = spec_node_props
        all_node_props.update(script_node_props)
        gdocs = _triples_to_graph_documents(all_triples, all_node_props)
        _build_and_load_neo4j_from_docs(gdocs, config)

        # --- 4. Neo4jの内容をテキスト(JSONL)でエクスポート ---
        try:
            export_dir = Path(config.api_document_dir) / "preprocessed" / "neo4j_export"
            nodes_fp, rels_fp = _export_neo4j_to_text(config, export_dir)
            logger.info(f"Neo4jをエクスポートしました: {nodes_fp.name}, {rels_fp.name}")
        except Exception as e:
            logger.warning(f"Neo4jエクスポートに失敗しました: {e}")

        # --- 5. ベクトルデータベース (Chroma) を構築（読み済みデータを再利用） ---
        logger.info("ChromaDB構築プロセス")
        _build_and_load_chroma(api_entries, script_files, config)

        logger.info("データベース構築プロセスが完了しました！")
        return True

    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        logger.error("設定やファイルの存在を確認してください。")
        return False


def main() -> None:
    """従来の互換性のためのメイン処理（非推奨）"""
    # 従来のconfig.pyベースの実行（互換性のため残す）
    # import config

    class LegacyConfig:
        def __init__(self):
            self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
            self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
            self.neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
            self.neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            self.api_document_dir = "data/src"
            self.chroma_persist_directory = "chroma_db_store"
            self.langchain_embedding_config = {
                "model": "text-embedding-3-small",
                "api_key": self.openai_api_key
            }

    legacy_config = LegacyConfig()
    build_databases(legacy_config)  # type: ignore[arg-type]


if __name__ == "__main__":
    # 環境変数を読み込み
    from dotenv import load_dotenv
    import os
    load_dotenv()
    main()
