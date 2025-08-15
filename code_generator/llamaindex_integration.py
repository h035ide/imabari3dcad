import os
import logging
import chromadb
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.core import PropertyGraphIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

logger = logging.getLogger(__name__)

def build_vector_engine(persist_dir: str, collection: str):
    """
    既存のChromaDB永続化データからLlamaIndexのVectorQueryEngineを構築します。
    """
    if not os.path.exists(persist_dir) or not os.listdir(persist_dir):
        logger.error(f"ChromaDBの永続化ディレクトリが見つからないか空です: {persist_dir}")
        raise FileNotFoundError(f"ChromaDBのデータベースが見つかりません。先にデータ格納スクリプトを実行してください。")

    logger.info(f"既存のChromaDBコレクション '{collection}' からVectorQueryEngineを構築しています...")

    # OpenAIの埋め込みモデルをLlamaIndexのSettingsに設定
    Settings.embed_model = OpenAIEmbedding()

    client = chromadb.PersistentClient(path=persist_dir)
    chroma_collection = client.get_or_create_collection(collection)

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # 既存のベクトルストアからインデックスを構築
    v_index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)

    logger.info("VectorQueryEngineの構築が完了しました。")
    return v_index.as_query_engine()

def build_graph_engine():
    """
    既存のNeo4jグラフからLlamaIndexのPropertyGraphQueryEngineを構築します。
    APOCプラグインがインストールされていることを前提としています。
    """
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    db_name = os.getenv("NEO4J_DATABASE")

    if not all([uri, user, password, db_name]):
        logger.error("Neo4j接続情報が環境変数に設定されていません。")
        raise ValueError("NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASEを.envファイルに設定してください。")

    logger.info(f"既存のNeo4jグラフ '{db_name}' からPropertyGraphQueryEngineを構築しています...")

    # OpenAIのLLMと埋め込みモデルをLlamaIndexのSettingsに設定
    Settings.llm = OpenAI(model="gpt-4o")
    Settings.embed_model = OpenAIEmbedding()

    try:
        # 標準的なNeo4jPropertyGraphStoreを使用（APOCプラグインが必要）
        graph_store = Neo4jPropertyGraphStore(
            username=user,
            password=password,
            url=uri,
            database=db_name,
        )
        
        # 既存のグラフ構造からインデックスをロード
        g_index = PropertyGraphIndex.from_existing(
            property_graph_store=graph_store,
        )

        logger.info("PropertyGraphQueryEngineの構築が完了しました。")
        return g_index.as_query_engine()
        
    except Exception as e:
        logger.error(f"Neo4jグラフエンジンの構築に失敗しました: {e}")
        logger.error("APOCプラグインが正しくインストールされているか確認してください。")
        raise e
