import os
import sys
import logging
import argparse
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

def fetch_data_from_neo4j(label: str = "ApiFunction", db_name: str = None, allow_missing_description: bool = True):
    """
    Neo4jからベクトル化するデータを取得します。
    label: 取得対象のラベル（例: ApiFunction, Function）
    db_name: データベース名（未指定なら環境変数のNEO4J_DATABASEまたはneo4j）
    allow_missing_description: description欠如時も取得するか
    """
    logger.info(f"Neo4jデータベース ({NEO4J_URI}) に接続しています...")
    try:
        with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver:
            database = db_name or os.getenv("NEO4J_DATABASE", "neo4j")
            with driver.session(database=database) as session:
                if allow_missing_description:
                    query = f"""
                    MATCH (n:{label})
                    WHERE n.name IS NOT NULL
                    RETURN elementId(n) AS node_id, n.name AS name, n.description AS description
                    """
                else:
                    query = f"""
                    MATCH (n:{label})
                    WHERE n.name IS NOT NULL AND n.description IS NOT NULL
                    RETURN elementId(n) AS node_id, n.name AS name, n.description AS description
                    """
                logger.info(f"{label} ノードを取得しています（database={database}）...")
                result = session.run(query)
                records = list(result)
                logger.info(f"{len(records)}件の{label}ノードを取得しました。")
                return records
    except Exception as e:
        logger.error(f"Neo4jからのデータ取得中にエラーが発生しました: {e}", exc_info=True)
        return []

def ingest_data_to_chroma(records, collection_name: str = CHROMA_COLLECTION_NAME, persist_dir: str = CHROMA_PERSIST_DIRECTORY):
    """取得したデータをChromaDBに格納します。"""
    if not records:
        logger.warning("格納するデータがありません。処理をスキップします。")
        return

    documents = []
    metadatas = []
    ids = []

    for record in records:
        # ドキュメントは、検索対象となるテキスト。名前と説明を組み合わせることで、検索精度向上を狙う。
        description = record.get('description') or ""
        doc_content = f"API名: {record['name']}\n説明: {description}"
        documents.append(doc_content)

        # メタデータには、後でグラフを再検索するために必要な情報を格納
        metadatas.append({
            "api_name": record["name"],
            "neo4j_node_id": record["node_id"]
        })

        # ChromaDB内でユニークなIDとして、Neo4jのノードIDを使用
        ids.append(record["node_id"])

    logger.info(f"{len(documents)}件のドキュメントをChromaDBに格納します...")
    logger.info(f"ChromaDB永続化ディレクトリ: {persist_dir}")
    logger.info(f"コレクション名: {collection_name}")

    try:
        # OpenAIの埋め込みモデルを初期化
        embedding_function = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

        # ChromaDBのクライアントを初期化（または既存のものを読み込み）
        vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=embedding_function,
            persist_directory=persist_dir
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
        # コレクション内のドキュメント数を取得（公開APIを使用）
        try:
            collection = vector_store.get()
            doc_count = len(collection['documents']) if collection['documents'] else 0
            logger.info(f"コレクション '{collection_name}' には現在 {doc_count} 件のドキュメントがあります。")
        except Exception as e:
            logger.warning(f"ドキュメント数の取得に失敗しました: {e}")
            logger.info("ChromaDBへのデータ格納が完了しました。")

    except Exception as e:
        logger.error(f"ChromaDBへのデータ格納中にエラーが発生しました: {e}", exc_info=True)

def parse_args():
    p = argparse.ArgumentParser(description="Neo4j -> Chroma インジェスト")
    p.add_argument("--label", default=os.getenv("INGEST_LABEL", "ApiFunction"), help="取得対象のラベル")
    p.add_argument("--database", default=os.getenv("NEO4J_DATABASE", "neo4j"), help="Neo4jデータベース名")
    p.add_argument("--collection", default=os.getenv("CHROMA_COLLECTION_NAME", CHROMA_COLLECTION_NAME), help="Chromaコレクション名")
    p.add_argument("--persist-dir", default=CHROMA_PERSIST_DIRECTORY, help="Chroma永続化ディレクトリ")
    p.add_argument("--require-description", action="store_true", help="descriptionのあるノードのみ対象とする")
    return p.parse_args()


def main():
    """メインの実行関数"""
    logger.info("--- データ格納スクリプト開始 ---")

    if not check_env_vars():
        sys.exit(1)

    args = parse_args()
    records = fetch_data_from_neo4j(label=args.label, db_name=args.database, allow_missing_description=not args.require_description)
    ingest_data_to_chroma(records, collection_name=args.collection, persist_dir=args.persist_dir)

    logger.info("--- データ格納スクリプト終了 ---")

if __name__ == "__main__":
    main()
