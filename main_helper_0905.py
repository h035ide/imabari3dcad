import os
from pathlib import Path
import logging
from typing import Optional
from neo4j import GraphDatabase
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import chromadb

# LlamaIndex imports
from llama_index.core import (
    Settings,
    VectorStoreIndex,
    StorageContext,
)
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.core.indices.property_graph import PropertyGraphIndex

logger = logging.getLogger(__name__)


class Config:
    """設定クラス - 全ての設定を一元管理"""

    def __init__(self):
        self.project_root = Path(__file__).parent

        # Neo4j設定（環境変数から読み込み）
        self.neo4j_uri = self._normalize_neo4j_uri(
            os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
        )
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        self.neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")

        # OpenAI設定（環境変数から読み込み）
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # APIドキュメント設定（プロジェクトルート基準の絶対パス。環境変数で上書き可）
        default_api_dir = self.project_root / "data" / "src"
        self.api_document_dir = Path(os.getenv("API_DOCUMENT_DIR", str(default_api_dir)))

        # ファイルパス設定
        self.parsed_api_result_def_file = "doc_parser/parsed_api_result_def.json"
        self.parsed_api_result_file = "doc_parser/parsed_api_result.json"

        # Chroma設定
        self.chroma_persist_directory = "chroma_db_store"
        self.chroma_collection_name = "api_documentation"

        # LlM設定
        self.setup_llm_config()
        self.setup_embedding_config()

    def _normalize_neo4j_uri(self, uri: str) -> str:
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

    def setup_llm_config(self):
        """LLM設定"""
        # 基本設定
        self.llm_model = "gpt-5-mini"
        self.response_format = "text"  # "json_object"
        # only for standard models
        self.llm_temperature = 0  # or None
        # only for inference models
        self.llm_verbosity = "high"  # "none" or "low" or "medium" or "high"
        # "none" or "minimal" or "low" or "medium" or "high"
        self.llm_reasoning_effort = "high"

        # モデル判定
        self.is_inference_model = self._is_inference_model()

        # 設定辞書を構築
        self._build_llm_configs()

    def _is_inference_model(self):
        """推論モデルかどうかを判定"""
        inference_models = ["o4-mini", "o4", "gpt-5", "gpt-5-mini", "gpt-5-nano"]
        return any(model in self.llm_model.lower() for model in inference_models)

    def _build_llm_configs(self):
        """LLM設定辞書を構築"""
        # 基本設定
        base_config = {"api_key": self.openai_api_key}

        # LangChain用設定
        self.langchain_llm_config = {"model_name": self.llm_model, **base_config}

        # LlamaIndex用設定
        self.llamaindex_llm_config = {"model": self.llm_model, **base_config}

        # モデル別パラメータを追加
        if self.is_inference_model:
            self._add_inference_model_params()
        else:
            self._add_standard_model_params()

    def _add_inference_model_params(self):
        """推論モデル専用パラメータを追加"""
        # 推論モデルではtemperatureは使用しない
        self.llm_temperature = None

        inference_params = {
            "reasoning_effort": self.llm_reasoning_effort,
            "output_version": "responses/v1",
            "verbosity": self.llm_verbosity,
            "response_format": self.response_format,
        }

        for key, value in inference_params.items():
            self.langchain_llm_config[key] = value
            self.llamaindex_llm_config[key] = value

    def _add_standard_model_params(self):
        """通常モデルのパラメータを追加"""
        # 通常モデルでは推論モデルパラメータは使用しない
        self.llm_verbosity = None
        self.llm_reasoning_effort = None

        # temperatureを追加
        if self.llm_temperature is not None:
            self.langchain_llm_config["temperature"] = self.llm_temperature
            self.llamaindex_llm_config["temperature"] = self.llm_temperature

    def setup_embedding_config(self):
        """埋め込みモデル設定"""
        # 基本設定
        self.embedding_model = "text-embedding-3-small"
        self.embedding_batch_size = 100

        # LangChain用設定
        self.langchain_embedding_config = {
            "model": self.embedding_model,
            "api_key": self.openai_api_key,
        }

        # LlamaIndex用設定
        self.llamaindex_embedding_config = {
            "model": self.embedding_model,
            "batch_size": self.embedding_batch_size,
            "api_key": self.openai_api_key,
        }

    def print_llm_config(self):
        """LLM設定を表示"""
        print("🤖 LLM設定:")
        print(f"  モデル: {self.llm_model}")
        print(f"  推論モデル: {'✅' if self.is_inference_model else '❌'}")
        print(f"  Temperature: {self.llm_temperature}")
        print(f"  Response Format: {self.response_format}")

        if self.is_inference_model:
            print(f"  Verbosity: {self.llm_verbosity}")
            print(f"  Reasoning Effort: {self.llm_reasoning_effort}")

        print("\n📋 LangChain設定:")
        for key, value in self.langchain_llm_config.items():
            print(f"  {key}: {value}")
        print("\n📋 LlamaIndex設定:")
        for key, value in self.llamaindex_llm_config.items():
            print(f"  {key}: {value}")


def fetch_data_from_neo4j(
    label: str = "ApiFunction",
    db_name: Optional[str] = None,
    allow_missing_description: bool = True,
    config: Optional[Config] = None,
):
    """
    Neo4jからベクトル化するデータを取得します。
    label: 取得対象のラベル（例: ApiFunction, Function）
    db_name: データベース名（未指定なら環境変数のNEO4J_DATABASEまたはcodeparsar）
    allow_missing_description: description欠如時も取得するか
    """
    if config is None:
        logger.error("Configが指定されていません。")
        return []

    logger.info(f"Neo4jデータベース ({config.neo4j_uri}) に接続しています...")
    try:
        with GraphDatabase.driver(
            config.neo4j_uri, auth=(config.neo4j_user, config.neo4j_password)
        ) as driver:
            database = db_name or os.getenv("NEO4J_DATABASE", "codeparsar")
            with driver.session(database=database) as session:
                if allow_missing_description:
                    query = f"""
                    MATCH (n:{label})
                    WHERE n.name IS NOT NULL
                    RETURN elementId(n) AS node_id, n.name AS name,
                           n.description AS description
                    """
                else:
                    query = f"""
                    MATCH (n:{label})
                    WHERE n.name IS NOT NULL AND n.description IS NOT NULL
                    RETURN elementId(n) AS node_id, n.name AS name,
                           n.description AS description
                    """
                logger.info(f"{label} ノードを取得しています（database={database}）...")
                result = session.run(query)  # type: ignore
                records = list(result)
                logger.info(f"{len(records)}件の{label}ノードを取得しました。")
                return records
    except Exception as e:
        logger.error(
            f"Neo4jからのデータ取得中にエラーが発生しました: {e}", exc_info=True
        )
        return []


def ingest_data_to_chroma(
    records,
    collection_name: Optional[str] = None,
    persist_dir: Optional[str] = None,
    config: Optional[Config] = None,
):
    """取得したデータをChromaDBに格納します。"""
    if not records:
        logger.warning("格納するデータがありません。処理をスキップします。")
        return

    # デフォルト値を設定
    if collection_name is None:
        collection_name = (
            config.chroma_collection_name if config else "api_documentation"
        )
    if persist_dir is None:
        persist_dir = config.chroma_persist_directory if config else "chroma_db_store"
    if config is None:
        logger.error("Configが指定されていません。")
        return

    documents = []
    metadatas = []
    ids = []

    for record in records:
        # ドキュメントは、検索対象となるテキスト。
        # 名前と説明を組み合わせることで、検索精度向上を狙う。
        description = record.get("description") or ""
        doc_content = f"API名: {record['name']}\n説明: {description}"
        documents.append(doc_content)

        # メタデータには、後でグラフを再検索するために必要な情報を格納
        metadatas.append(
            {"api_name": record["name"], "neo4j_node_id": record["node_id"]}
        )

        # ChromaDB内でユニークなIDとして、Neo4jのノードIDを使用
        ids.append(record["node_id"])

    logger.info(f"{len(documents)}件のドキュメントをChromaDBに格納します...")
    logger.info(f"ChromaDB永続化ディレクトリ: {persist_dir}")
    logger.info(f"コレクション名: {collection_name}")

    try:
        # OpenAIの埋め込みモデルを初期化
        api_key = config.openai_api_key
        if api_key is None:
            logger.error("OpenAI APIキーが設定されていません。")
            return
        # LangChain側の埋め込みも config のモデルに統一
        embedding_function = OpenAIEmbeddings(
            **config.langchain_embedding_config
        )  # type: ignore

        # ChromaDBのクライアントを初期化（または既存のものを読み込み）
        vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=embedding_function,
            persist_directory=persist_dir,
        )

        # データを追加（既存のIDがあれば更新される）
        vector_store.add_texts(texts=documents, metadatas=metadatas, ids=ids)

        # Chroma 0.4.x以降では自動永続化のためpersist()は不要
        # vector_store.persist()  # 削除

        logger.info("ChromaDBへのデータ格納が正常に完了しました。")
        # コレクション内のドキュメント数を取得（公開APIを使用）
        try:
            collection = vector_store.get()
            doc_count = len(collection["documents"]) if collection["documents"] else 0
            logger.info(
                f"コレクション '{collection_name}' には現在 "
                f"{doc_count} 件のドキュメントがあります。"
            )
        except Exception as e:
            logger.warning(f"ドキュメント数の取得に失敗しました: {e}")
            logger.info("ChromaDBへのデータ格納が完了しました。")

    except Exception as e:
        logger.error(
            f"ChromaDBへのデータ格納中にエラーが発生しました: {e}",
            exc_info=True,
        )


def build_vector_engine(
    persist_dir: str,
    collection: str,
    config: Config,
    similarity_top_k: int = 15,
):
    """
    既存のChromaDB永続化データからLlamaIndexのVectorQueryEngineを構築します。
    """
    if not os.path.exists(persist_dir) or not os.listdir(persist_dir):
        logger.error(
            f"ChromaDBの永続化ディレクトリが見つからないか空です: {persist_dir}"
        )
        raise FileNotFoundError(
            "ChromaDBのデータベースが見つかりません。先にデータ格納スクリプトを実行してください。"
        )

    logger.info(
        (
            f"既存のChromaDBコレクション '{collection}' から"
            "VectorQueryEngineを構築しています..."
        )
    )

    # OpenAIの埋め込みモデルをLlamaIndexのSettingsに設定
    Settings.embed_model = OpenAIEmbedding(**config.llamaindex_embedding_config)

    client = chromadb.PersistentClient(path=persist_dir)
    chroma_collection = client.get_or_create_collection(collection)

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # 既存のベクトルストアからインデックスを構築
    v_index = VectorStoreIndex.from_vector_store(
        vector_store,
        storage_context=storage_context,
    )

    logger.info("VectorQueryEngineの構築が完了しました。")
    return v_index.as_query_engine(similarity_top_k=similarity_top_k)


def build_graph_engine(config: Config):
    """
    既存のNeo4jグラフからLlamaIndexのPropertyGraphQueryEngineを構築します。
    APOCプラグインがインストールされていることを前提としています。
    """
    uri = config.neo4j_uri
    user = config.neo4j_user
    password = config.neo4j_password
    db_name = config.neo4j_database

    if not all([uri, user, password, db_name]):
        logger.error("Neo4j接続情報が config から取得できません。")
        raise ValueError(
            (
                "config に neo4j_uri, neo4j_user, neo4j_password, "
                "neo4j_database が設定されていません。"
            )
        )

    logger.info(
        (
            f"既存のNeo4jグラフ '{db_name}' から"
            "PropertyGraphQueryEngineを構築しています..."
        )
    )

    # OpenAIのLLMと埋め込みモデルをLlamaIndexのSettingsに設定（configから）
    Settings.llm = OpenAI(**config.llamaindex_llm_config)
    Settings.embed_model = OpenAIEmbedding(**config.llamaindex_embedding_config)

    try:
        # 標準的なNeo4jPropertyGraphStoreを使用（APOCプラグインが必要）
        # ここでは環境変数の存在を既に検証済みだが、型シグネチャが str を要求するためキャスト
        assert (
            user is not None
            and password is not None
            and uri is not None
            and db_name is not None
        )
        graph_store = Neo4jPropertyGraphStore(
            username=str(user),
            password=str(password),
            url=str(uri),
            database=str(db_name),
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
        logger.error(
            (
                f"Neo4jグラフエンジンの構築中に例外が発生しました "
                f"[{type(e).__name__}]: {e}\n"
                "失敗したステップ: Neo4jPropertyGraphStoreの初期化または"
                "PropertyGraphIndexのロード。\n"
                "APOCプラグインが正しくインストールされているか確認してください。"
            )
        )
        raise
