from pathlib import Path
import re
import shutil
from typing import List, Tuple, Dict, Any, Optional

from bs4 import BeautifulSoup
# ▼▼▼ 変更 ▼▼▼
from langchain_core.prompts import BasePromptTemplate, ChatPromptTemplate
# ▲▲▲ 変更 ▲▲▲
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_experimental.graph_transformers import LLMGraphTransformer
import config
from langchain_core.documents import Document
from langchain_neo4j import Neo4jGraph
from neo4j.exceptions import ServiceUnavailable
from langchain_community.graphs.graph_document import GraphDocument
from langchain_community.vectorstores import Chroma


# --- 定数定義 ---
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

# ▼▼▼ 変更 ▼▼▼
# --- LLMGraphTransformer用カスタムプロンプト定義 ---
# カスタムプロンプトを使用しない場合は、この値を None に設定してください。
# None に設定すると、LLMGraphTransformerのデフォルトプロンプトが使用されます。
CUSTOM_GRAPH_TRANSFORMER_PROMPT: Optional[BasePromptTemplate] = None

# --- カスタムプロンプトの記述例 ---
# 以下はプロンプトのサンプルです。使用する場合は、CUSTOM_GRAPH_TRANSFORMER_PROMPT に代入してください。
# 例: CUSTOM_GRAPH_TRANSFORMER_PROMPT = custom_prompt_example

custom_prompt_example = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            # Role: 知識グラフ抽出エキスパート
            あなたは、テキストからエンティティとリレーションシップを抽出し、知識グラフを構築する専門家です。
            提供されたドキュメントに基づいて、主要なエンティティとそれらの間の関連性を特定することがあなたの役割です。

            ## 指示
            1.  **エンティティの特定**: テキストから主要なエンティティ（ノード）を抽出します。各エンティティには一意の`id`と`type`（種類）が必要です。
            2.  **リレーションシップの特定**: エンティティ間の関係性（エッジ）を抽出します。各リレーションシップには`source`（始点ノード）、`target`（終点ノード）、`type`（関係性の種類）が必要です。
            3.  **厳密なフォーマット**: レスポンスは "nodes" と "relationships" を含むJSON形式のみで返却してください。説明や謝罪などの追加テキストは一切含めないでください。

            ## 例
            テキスト: "A社の田中は、B社の鈴木と協力してプロジェクトXを進めている。このプロジェクトは東京で行われている。"
            JSON:
            {
                "nodes": [
                    {"id": "田中", "type": "Person"},
                    {"id": "A社", "type": "Company"},
                    {"id": "鈴木", "type": "Person"},
                    {"id": "B社", "type": "Company"},
                    {"id": "プロジェクトX", "type": "Project"},
                    {"id": "東京", "type": "Location"}
                ],
                "relationships": [
                    {"source": "田中", "target": "A社", "type": "BELONGS_TO"},
                    {"source": "鈴木", "target": "B社", "type": "BELONGS_TO"},
                    {"source": "田中", "target": "鈴木", "type": "COOPERATES_WITH"},
                    {"source": "田中", "target": "プロジェクトX", "type": "WORKS_ON"},
                    {"source": "鈴木", "target": "プロジェクトX", "type": "WORKS_ON"},
                    {"source": "プロジェクトX", "target": "東京", "type": "LOCATED_IN"}
                ]
            }
            """,
        ),
        (
            "human",
            "以下のテキストから知識グラフを抽出してください:\n-----\n{text}",
        ),
    ]
)
# ▲▲▲ 変更 ▲▲▲


# --- ファイル読み込み・テキスト正規化関数 (変更なし) ---

def _read_api_text() -> str:
    """api.txt を候補パスから読み込む"""
    for p in API_TXT_CANDIDATES:
        if p.exists():
            return p.read_text(encoding="utf-8")
    raise FileNotFoundError("api.txt が見つかりませんでした。")

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

def _normalize_text(text: str) -> str:
    """改行/タブ/空白の揺れを正規化。"""
    text = text.replace("\ufeff", "")  # BOM
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = text.replace("\t", " ")
    text = re.sub(r"[ \u00A0\u3000]+", " ", text)
    return text


# --- データベース操作関数 (変更なし) ---

def _rebuild_graph_in_neo4j(graph_docs: List[GraphDocument]) -> Tuple[int, int]:
    """Neo4j をリセットしてから GraphDocument を投入する"""
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
    """ドキュメントリストからベクトルDB (Chroma) を構築・永続化する"""
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


# --- メインのグラフ構築・ロード関数 ---

def _build_and_load_neo4j() -> None:
    """LLMGraphTransformerを使用してすべてのドキュメントからグラフを構築し、Neo4jにロードする"""
    
    # --- 1. すべてのドキュメントを読み込み、Documentオブジェクトに変換 ---
    print("📄 API仕様書、スクリプト例、HTMLドキュメントを読み込み中...")
    documents = []
    
    try:
        documents.append(Document(page_content=_normalize_text(_read_api_text()), metadata={"source": "api.txt"}))
        documents.append(Document(page_content=_normalize_text(_read_api_arg_text()), metadata={"source": "api_arg.txt"}))
    except FileNotFoundError as e:
        print(f"⚠ {e}")
        
    for script_name, script_content in _read_script_files():
        documents.append(Document(page_content=script_content, metadata={"source": "script_example", "file_name": script_name}))
        
    for file_name, html_content in _read_html_files():
        soup = BeautifulSoup(html_content, 'lxml')
        content_div = soup.find('div', class_='contents')
        text_content = content_div.get_text(separator='\n', strip=True) if content_div else (soup.body.get_text(separator='\n', strip=True) if soup.body else "")
        documents.append(Document(page_content=text_content, metadata={"source": "html_document", "file_name": file_name}))
        
    if not documents:
        print("⚠ 処理対象のドキュメントが見つかりませんでした。処理を終了します。")
        return

    print(f"✔ 合計 {len(documents)} 件のドキュメントを処理対象とします。")

    # --- 2. LLMによるグラフ抽出 ---
    print("\n🤖 LLMを使用してドキュメントからグラフデータを抽出中...")
    llm = ChatOpenAI(temperature=0, model_name="gpt-5", openai_api_key=OPENAI_API_KEY)

    # ▼▼▼ 変更 ▼▼▼
    # CUSTOM_GRAPH_TRANSFORMER_PROMPT が設定されていればそれを使用し、
    # 設定されていなければ (Noneの場合) デフォルトのプロンプトを使用します。
    if CUSTOM_GRAPH_TRANSFORMER_PROMPT:
        print("  - カスタムプロンプトを使用してグラフを抽出します。")
        llm_transformer = LLMGraphTransformer(
            llm=llm, prompt=CUSTOM_GRAPH_TRANSFORMER_PROMPT
        )
    else:
        print("  - デフォルトプロンプトを使用してグラフを抽出します。")
        llm_transformer = LLMGraphTransformer(llm=llm)
    # ▲▲▲ 変更 ▲▲▲

    try:
        gdocs = llm_transformer.convert_to_graph_documents(documents)
        print(f"✔ LLMによるグラフ抽出が完了しました。")
    except Exception as e:
        print(f"⚠ LLMによるグラフ抽出中にエラーが発生しました: {e}")
        return

    # --- 3. Neo4jへのデータ投入 ---
    try:
        node_count, rel_count = _rebuild_graph_in_neo4j(gdocs)
        print(f"✔ グラフデータベースの再構築が完了しました: ノード={node_count}, リレーションシップ={rel_count}")
    except ServiceUnavailable as se:
        print(f"⚠ Neo4j への接続に失敗しました: {se}\n   Neo4jサーバーが起動しているか、接続情報を確認してください。")
    except Exception as e:
        print(f"⚠ グラフデータベースの構築中にエラーが発生しました: {e}")


def main() -> None:
    """メイン処理"""
    
    # 1. グラフデータベース (Neo4j) を構築
    # この関数内で全てのテキストがLLMによってグラフ化される
    _build_and_load_neo4j()

    # 2. ベクトルデータベース (Chroma) を構築
    print("\n--- ChromaDB構築プロセス ---")
    docs_for_vectorstore: List[Document] = []
    
    # API仕様書
    try:
        docs_for_vectorstore.append(Document(page_content=_normalize_text(_read_api_text()), metadata={"source": "api_spec"}))
    except FileNotFoundError:
        pass # Neo4j構築時にエラーが出ているはずなのでここでは無視
        
    # スクリプト例
    script_files = _read_script_files()
    for script_name, script_content in script_files:
        docs_for_vectorstore.append(Document(page_content=f"スクリプト例: {script_name}\n\n```python\n{script_content}\n```", metadata={"source": "script_example", "script_name": script_name}))
    
    # HTMLドキュメント
    for file_name, html_content in _read_html_files():
        soup = BeautifulSoup(html_content, 'lxml')
        content_div = soup.find('div', class_='contents')
        text_content = content_div.get_text(separator='\n', strip=True) if content_div else (soup.body.get_text(separator='\n', strip=True) if soup.body else "")
        docs_for_vectorstore.append(Document(page_content=f"ドキュメント: {file_name}\n\n{text_content}", metadata={"source": "html_document", "file_name": file_name}))

    if docs_for_vectorstore:
        print(f"✔ ChromaDB用に {len(docs_for_vectorstore)} 件のドキュメントを準備しました。")
        _build_and_load_chroma(docs_for_vectorstore)
    else:
        print("⚠ ChromaDBに入れるドキュメントがないため、処理をスキップします。")


if __name__ == "__main__":
    main()