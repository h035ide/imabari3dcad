import os
import sys
import logging
from typing import Type, Dict, Any, List

# --- [Path Setup] ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- [End Path Setup] ---

from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain.tools import BaseTool
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# .envファイルを読み込む
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 定数定義 ---
CHROMA_PERSIST_DIRECTORY = os.path.join(project_root, "chroma_db_store")
CHROMA_COLLECTION_NAME = "api_functions"

class GraphSearchInput(BaseModel):
    """グラフ検索ツールの入力スキーマ。"""
    query: str = Field(description="ナレッジグラフから情報を検索するための自然言語クエリ。")

class GraphSearchTool(BaseTool):
    """
    APIの機能やコード例を検索するためのハイブリッド検索ツール。
    まずベクトル検索で関連性の高いAPI候補を見つけ、次にグラフデータベースで詳細情報を取得します。
    """
    name: str = "hybrid_graph_knowledge_search"
    description: str = (
        "APIの機能、関数、クラス、またはコード例に関する情報を検索する場合に必ず使用します。"
        "「球を作成する関数」や「特定のパラメータを持つAPI」など、"
        "探している機能やコードを自然言語で具体的に記述したクエリを入力してください。"
    )
    args_schema: Type[BaseModel] = GraphSearchInput

    _neo4j_driver: GraphDatabase.driver = None
    _vector_store: Chroma = None
    _is_configured: bool = False

    def __init__(self, **data):
        super().__init__(**data)

        api_key = os.getenv("OPENAI_API_KEY")
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")

        if not all([api_key, uri, user, password]):
            logger.warning("必要な環境変数が見つからないため、GraphSearchToolは非アクティブモードで初期化されました。")
            self._is_configured = False
        else:
            # Neo4jドライバを初期化
            self._neo4j_driver = GraphDatabase.driver(uri, auth=(user, password))
            self._db_name = os.getenv("NEO4J_DATABASE", "neo4j")

            # ChromaDBクライアントと埋め込み関数を初期化
            embedding_function = OpenAIEmbeddings(api_key=api_key)
            self._vector_store = Chroma(
                collection_name=CHROMA_COLLECTION_NAME,
                embedding_function=embedding_function,
                persist_directory=CHROMA_PERSIST_DIRECTORY
            )
            self._is_configured = True
            logger.info("GraphSearchToolは正常に設定され、アクティブです。")

    def _run(self, query: str) -> str:
        """ツールの同期実行ロジック（ハイブリッド検索）。"""
        if not self._is_configured:
            return "ツールが設定されていません。APIキーとDB接続情報を確認してください。"

        if not os.path.exists(CHROMA_PERSIST_DIRECTORY):
            return (f"ChromaDBのデータベースが見つかりません。先にデータ格納スクリプトを実行してください。\n"
                    f"コマンド: `python -m code_generator.db.ingest_to_chroma`")

        logger.info(f"ハイブリッド検索を開始。クエリ: '{query}'")
        try:
            # 1. ベクトル検索で関連性の高いノード候補を取得
            logger.info(f"ステップ1/2: ChromaDBでベクトル検索を実行中...")
            # `include=['metadatas']` を指定してメタデータのみ取得
            results = self._vector_store.similarity_search(query, k=5, include=['metadatas'])

            if not results:
                return "ベクトル検索で関連するAPIが見つかりませんでした。"

            logger.info(f"{len(results)}件の候補をベクトル検索で発見しました。")

            # 2. グラフ探索で詳細情報を取得
            logger.info(f"ステップ2/2: Neo4jで詳細情報を取得中...")
            node_ids = [doc.metadata.get("neo4j_node_id") for doc in results if doc.metadata.get("neo4j_node_id")]

            if not node_ids:
                 return "ベクトル検索の結果から有効なノードIDを取得できませんでした。"

            cypher_query = """
            MATCH (api:APIFunction)
            WHERE elementId(api) IN $node_ids
            OPTIONAL MATCH (f:Function)-[:IMPLEMENTS_API]->(api)
            OPTIONAL MATCH (api)-[:HAS_PARAMETER]->(p:Parameter)
            RETURN api.name AS apiName, api.description AS apiDescription,
                   f.name AS functionName, f.code AS functionCode, f.signature AS functionSignature,
                   collect(p.name) AS parameters
            """

            with self._neo4j_driver.session(database=self._db_name) as session:
                result = session.run(cypher_query, node_ids=node_ids)
                records = [record.data() for record in result]

            if not records:
                return "グラフデータベースで詳細情報の取得に失敗しました。"

            return self._format_results(records)

        except Exception as e:
            logger.error(f"ハイブリッド検索の実行中にエラーが発生しました: {e}", exc_info=True)
            return f"ツールの実行中にエラーが発生しました: {e}"

    def _format_results(self, records: List[Dict[str, Any]]) -> str:
        """データベースの検索結果をエージェントが理解しやすい文字列に整形します。"""
        if not records: return "結果なし"
        formatted_string = "ナレッジグラフから以下の情報が見つかりました:\n\n"
        for i, record in enumerate(records):
            formatted_string += f"--- 関連API候補 {i+1} ---\n"
            for key, value in record.items():
                if value is not None:
                    if isinstance(value, list):
                        formatted_value = ", ".join(map(str, value)) if value else "なし"
                    else:
                        formatted_value = str(value)
                    formatted_string += f"- {key}: {formatted_value}\n"
            formatted_string += "\n"
        return formatted_string

    def close(self):
        """ドライバ接続を閉じます。"""
        if self._neo4j_driver:
            self._neo4j_driver.close()

# `if __name__ == '__main__':` ブロックは、テストファイルに移行したため削除。
# このファイルはツール定義に専念する。
