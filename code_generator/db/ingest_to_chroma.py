import os
import sys
import logging
from dotenv import load_dotenv

# --- [Path Setup] ---
# This script is intended to be run from the project root.
# Example: python -m code_generator.db.ingest_to_chroma
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- [End Path Setup] ---

from neo4j import GraphDatabase
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# .envファイルを明示的に読み込む
load_dotenv(dotenv_path=os.path.join(project_root, '.env'))

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 定数定義 ---
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CHROMA_PERSIST_DIRECTORY = os.path.join(project_root, "chroma_db_store")
CHROMA_COLLECTION_NAME = "api_functions"

def check_env_vars():
    """必要な環境変数がすべて設定されているか確認します。"""
    required_vars = ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"以下の環境変数が設定されていません: {', '.join(missing_vars)}")
        logger.error("スクリプトを実行する前に、プロジェクトルートの.envファイルを設定してください。")
        return False
    return True

def fetch_data_from_neo4j():
    """Neo4jからベクトル化するデータを取得します。"""
    logger.info(f"Neo4jデータベース ({NEO4J_URI}) に接続しています...")
    try:
        with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver:
            with driver.session(database=NEO4J_DATABASE) as session:
                # APIFunctionノードから、名前と説明を取得します。これらを連結したものをベクトル化の対象とします。
                query = """
                MATCH (n:APIFunction)
                WHERE n.name IS NOT NULL AND n.description IS NOT NULL
                RETURN elementId(n) AS node_id, n.name AS name, n.description AS description
                """
                logger.info("APIFunctionノードを取得しています...")
                result = session.run(query)
                records = list(result)
                logger.info(f"{len(records)}件のAPIFunctionノードを取得しました。")
                return records
    except Exception as e:
        logger.error(f"Neo4jからのデータ取得中にエラーが発生しました: {e}", exc_info=True)
        return []

def ingest_data_to_chroma(records):
    """取得したデータをChromaDBに格納します。"""
    if not records:
        logger.warning("格納するデータがありません。処理をスキップします。")
        return

    documents = []
    metadatas = []
    ids = []

    for record in records:
        # ドキュメントは、検索対象となるテキスト。名前と説明を組み合わせることで、検索精度向上を狙う。
        doc_content = f"API名: {record['name']}\n説明: {record['description']}"
        documents.append(doc_content)

        # メタデータには、後でグラフを再検索するために必要な情報を格納
        metadatas.append({
            "api_name": record["name"],
            "neo4j_node_id": record["node_id"]
        })

        # ChromaDB内でユニークなIDとして、Neo4jのノードIDを使用
        ids.append(record["node_id"])

    logger.info(f"{len(documents)}件のドキュメントをChromaDBに格納します...")
    logger.info(f"ChromaDB永続化ディレクトリ: {CHROMA_PERSIST_DIRECTORY}")

    try:
        # OpenAIの埋め込みモデルを初期化
        embedding_function = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

        # ChromaDBのクライアントを初期化（または既存のものを読み込み）
        vector_store = Chroma(
            collection_name=CHROMA_COLLECTION_NAME,
            embedding_function=embedding_function,
            persist_directory=CHROMA_PERSIST_DIRECTORY
        )

        # データを追加（既存のIDがあれば更新される）
        vector_store.add_texts(
            texts=documents,
            metadatas=metadatas,
            ids=ids
        )

        # 変更をディスクに永続化
        vector_store.persist()

        logger.info("ChromaDBへのデータ格納が正常に完了しました。")
        logger.info(f"コレクション '{CHROMA_COLLECTION_NAME}' には現在 {vector_store._collection.count()} 件のドキュメントがあります。")

    except Exception as e:
        logger.error(f"ChromaDBへのデータ格納中にエラーが発生しました: {e}", exc_info=True)

def main():
    """メインの実行関数"""
    logger.info("--- データ格納スクリプト開始 ---")

    if not check_env_vars():
        sys.exit(1)

    records = fetch_data_from_neo4j()
    ingest_data_to_chroma(records)

    logger.info("--- データ格納スクリプト終了 ---")

if __name__ == "__main__":
    main()
