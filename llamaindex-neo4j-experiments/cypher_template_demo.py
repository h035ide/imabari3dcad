# pip install llama-index-core llama-index-graph-stores-neo4j nest-asyncio
import nest_asyncio
from llama_index.core import Document
from llama_index.core.indices.property_graph import PropertyGraphIndex
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from dotenv import load_dotenv
import os
import logging

# Windows環境での非同期処理の安定化
nest_asyncio.apply()

# 環境変数を読み込み
load_dotenv()


def normalize_neo4j_uri(uri: str) -> str:
    """ローカル単一ノード接続でのルーティングエラー回避のためURIを正規化。
    - neo4j://localhost(127.0.0.1) → bolt://localhost(127.0.0.1)
    - ポート未指定時は :7687 を付与
    """
    try:
        u = uri.strip()
        if u.startswith("neo4j://") and ("localhost" in u or "127.0.0.1" in u):
            u = "bolt://" + u[len("neo4j://"):]
        if u.startswith("bolt://"):
            host_port = u[len("bolt://"):]
            # ポートが無ければ7687を付与
            if ":" not in host_port:
                u = u + ":7687"
        return u
    except Exception:
        # 失敗しても元の値を返す
        return uri


# Neo4j設定（環境変数から読み込み）
neo4j_uri = normalize_neo4j_uri(os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687"))
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "password")


# ロギング設定: LOG_LEVEL 環境変数で調整（未設定は DEBUG）
_log_level_name = os.getenv("LOG_LEVEL", "DEBUG").upper()
_log_level = getattr(logging, _log_level_name, logging.DEBUG)

# ログファイルの設定
_log_file = os.getenv("LOG_FILE", "cypher_template_demo.log")

# ログフォーマット
_log_format = "%(asctime)s %(levelname)s %(name)s: %(message)s"

# ログ設定（コンソールとファイル両方に出力）
logging.basicConfig(
    level=_log_level,
    format=_log_format,
    handlers=[
        logging.FileHandler(_log_file, encoding='utf-8'),  # ファイル出力
        logging.StreamHandler()  # コンソール出力
    ]
)

# Neo4j 接続（環境変数から読み込み）
graph_store = Neo4jPropertyGraphStore(
    url=neo4j_uri,
    username=neo4j_user,
    password=neo4j_password,
    database="demo",  # デフォルトデータベースを使用
)

# ドキュメントを投入（PG Index が内部でノード・リレーション化）
docs = [Document(text="Taro works at ACME. ACME is based in Tokyo.")]
index = PropertyGraphIndex.from_documents(docs, property_graph_store=graph_store)

# 最小クエリエンジン（自然文→内部で Text→Cypher / ベクタ等）
engine = index.as_query_engine()
print(engine.query("Where does ACME locate?"))
