from pathlib import Path
import re
import shutil
from typing import List, Tuple, Dict, Any

import config
from langchain_core.documents import Document
from langchain_neo4j import Neo4jGraph
from neo4j.exceptions import ServiceUnavailable
from langchain_community.graphs.graph_document import GraphDocument
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_experimental.graph_transformers import LLMGraphTransformer

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

# --- データベース操作関数 (変更なし) ---

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

# --- ChromaDB構築関数 (修正) ---

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
    LLMGraphTransformerを使用してドキュメントからグラフを構築し、Neo4jにロードする
    """
    # --- 1. ドキュメントの読み込み ---
    print("📄 API仕様書とスクリプト例を読み込み中...")
    api_text = _normalize_text(_read_api_text())
    api_arg_text = _normalize_text(_read_api_arg_text())
    script_files = _read_script_files()
    
    # LangChain Documentオブジェクトに変換
    documents = [
        Document(page_content=api_text, metadata={"source": "api.txt"}),
        Document(page_content=api_arg_text, metadata={"source": "api_arg.txt"})
    ]
    for script_name, script_content in script_files:
        documents.append(Document(page_content=script_content, metadata={"source": script_name}))
    
    print(f"✔ 合計 {len(documents)} 件のドキュメントを処理対象とします。")

    # --- 2. LLMによるグラフ抽出 ---
    print("\n🤖 LLMを使用してドキュメントからグラフデータを抽出中...")
    llm = ChatOpenAI(temperature=1, model_name="gpt-5-mini", openai_api_key=OPENAI_API_KEY)
    llm_transformer = LLMGraphTransformer(llm=llm)

    gdocs = llm_transformer.convert_to_graph_documents(documents)
    print(f"✔ LLMによるグラフ抽出が完了しました。")

    # --- 3. Neo4jへのデータ投入 ---
    try:
        node_count, rel_count = _rebuild_graph_in_neo4j(gdocs)
        print(f"✔ グラフデータベースの再構築が完了しました: ノード={node_count}, リレーションシップ={rel_count}")
    except ServiceUnavailable as se:
        print(f"⚠ Neo4j への接続に失敗しました: {se}")
        print("   Neo4jサーバーが起動しているか、接続情報を確認してください。")
    except Exception as e:
        print(f"⚠ グラフデータベースの構築中にエラーが発生しました: {e}")

# --- main関数 (修正) ---

def main() -> None:
    """
    メイン処理
    """
    # グラフデータベース (Neo4j) を構築
    _build_and_load_neo4j()

    # ベクトルデータベース (Chroma) を構築
    print("\n--- ChromaDB構築プロセス ---")
    api_text = _read_api_text()
    script_files = _read_script_files()
    
    docs_for_vectorstore: List[Document] = []

    # 1. API仕様からドキュメントを生成
    content_api = _normalize_text(api_text)
    docs_for_vectorstore.append(Document(
        page_content=content_api, 
        metadata={"source": "api_spec"}
    ))
    print(f"✔ API仕様書からドキュメントを1件作成しました。")
    
    # 2. スクリプト例からドキュメントを生成
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
    _build_and_load_chroma(docs_for_vectorstore)


if __name__ == "__main__":
    main()