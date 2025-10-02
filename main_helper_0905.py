import os
from pathlib import Path
import logging
from typing import Optional, Any, Dict
from neo4j import GraphDatabase
from neo4j import Session
import chromadb
import numpy as np
from dotenv import load_dotenv
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
)
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.core.indices.property_graph import PropertyGraphIndex

# LangChain imports
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.schema import HumanMessage, SystemMessage
# from langchain.callbacks import LangChainTracer

# .envファイルを明示的にロード
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """設定クラス - 全ての設定を一元管理"""

    def __init__(self):
        self.project_root = Path(__file__).parent

        # Neo4j設定（環境変数から読み込み）
        self.neo4j_uri = self._normalize_neo4j_uri(os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687"))
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        self.neo4j_database = os.getenv("NEO4J_DATABASE", "docparser")

        # OpenAI設定（環境変数から読み込み）
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # LlamaIndex形式の生成を制御
        flag_raw = os.getenv("CREATE_LLAMAINDEX_FORMAT", "true")
        self.create_llamaindex_format = flag_raw.lower() in ("1", "true", "yes")

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
        # 基本設定（環境変数で上書き可能）
        self.llm_model = os.getenv("LLM_MODEL", "gpt-5-nano")
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
        # 基本設定（環境変数で上書き可能）
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.embedding_batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))

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
        with GraphDatabase.driver(config.neo4j_uri, auth=(config.neo4j_user, config.neo4j_password)) as driver:
            database = db_name or config.neo4j_database
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
        logger.error(f"Neo4jからのデータ取得中にエラーが発生しました: {e}", exc_info=True)
        return []


def ingest_data_to_chroma(
    records,
    collection_name: Optional[str] = None,
    persist_dir: Optional[str] = None,
    config: Optional[Config] = None,
):
    """取得したデータをChromaDBに格納します。upsert対応で重複IDを適切に処理します。"""
    if not records:
        logger.warning("格納するデータがありません。処理をスキップします。")
        return

    # デフォルト値を設定
    if collection_name is None:
        collection_name = config.chroma_collection_name if config else "api_documentation"
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
        metadatas.append({"api_name": record["name"], "neo4j_node_id": record["node_id"]})

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
        # OpenAI埋め込みモデルを使って埋め込みを生成（設定されたmodel/batch_sizeを反映）
        embed_model = OpenAIEmbedding(**config.llamaindex_embedding_config)
        embeddings = embed_model.get_text_embedding_batch(documents)
        # Chroma の型要件に合わせて明示的に List[List[float]] に正規化
        embeddings_for_chroma = [list(map(float, vec)) for vec in embeddings]
        embeddings_np = np.asarray(embeddings_for_chroma, dtype=np.float32)
        # chromadb クライアント直利用でupsert対応
        client = chromadb.PersistentClient(path=persist_dir)
        chroma_collection = client.get_or_create_collection(collection_name)

        # upsertでデータを追加/更新（ID重複を適切に処理）
        chroma_collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings_np,  # OpenAI埋め込みを明示的に渡す
        )

        logger.info("ChromaDBへのデータ格納が正常に完了しました。")

        # コレクション内のドキュメント数を取得（chromadb正式APIを使用）
        try:
            doc_count = chroma_collection.count()
            logger.info(f"コレクション '{collection_name}' には現在 {doc_count} 件のドキュメントがあります。")
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
        logger.error(f"ChromaDBの永続化ディレクトリが見つからないか空です: {persist_dir}")
        raise FileNotFoundError("ChromaDBのデータベースが見つかりません。先にデータ格納スクリプトを実行してください。")

    logger.info((f"既存のChromaDBコレクション '{collection}' からVectorQueryEngineを構築しています..."))

    # OpenAIのLLMと埋め込みモデルを初期化（グローバル設定を避ける）
    llm = OpenAI(**config.llamaindex_llm_config)
    embed_model = OpenAIEmbedding(**config.llamaindex_embedding_config)

    client = chromadb.PersistentClient(path=persist_dir)
    chroma_collection = client.get_or_create_collection(collection)

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # 既存のベクトルストアからインデックスを構築（embed_modelを明示的に指定）
    v_index = VectorStoreIndex.from_vector_store(
        vector_store,
        storage_context=storage_context,
        embed_model=embed_model,
    )

    logger.info("VectorQueryEngineの構築が完了しました。")
    return v_index.as_query_engine(llm=llm, similarity_top_k=similarity_top_k)


def _has_llamaindex_entities(session: Session) -> bool:
    """__Entity__ノードが存在するか確認"""
    result = session.run("MATCH (e:__Entity__) RETURN count(e) AS c")
    record = result.single()
    return bool(record and record.get("c", 0))


def _convert_existing_data_to_llamaindex(session: Session, config: Config) -> None:
    """既存データをLlamaIndex形式に変換"""
    from doc_parser.neo4j_importer import Neo4jImporter

    importer = Neo4jImporter(
        config.neo4j_uri,
        config.neo4j_user,
        config.neo4j_password,
        database=config.neo4j_database,
        create_llamaindex_format=True,
    )

    try:
        importer._create_llamaindex_structures(session)

        # 既存のLlamaIndex形式ノードを削除してから再生成（冪等性確保）
        session.run("MATCH (n:__Entity__) DETACH DELETE n")
        session.run("MATCH (n:__Node__) DETACH DELETE n")

        # ObjectDefinitionごとのプロパティ情報を先に取得
        object_properties_map = {}
        object_property_rows = session.run(
            """
            MATCH (od:ObjectDefinition)
            OPTIONAL MATCH (od)-[:HAS_PROPERTY]->(p:Parameter)
            WITH od, collect({
                name: p.name,
                description: p.description,
                type: p.type
            }) AS props
            RETURN od.name AS name,
                   od.description AS description,
                   od.category AS category,
                   od.notes AS notes,
                   props
            """
        ).data()
        for row in object_property_rows:
            obj_data = {
                "name": row.get("name"),
                "description": row.get("description") or "",
                "category": row.get("category") or "",
                "notes": row.get("notes") or "",
                "properties": [
                    {
                        "name": prop.get("name"),
                        "description": prop.get("description") or "",
                        "type": prop.get("type") or "",
                    }
                    for prop in row.get("props") or []
                    if prop.get("name")
                ],
            }
            object_properties_map[obj_data["name"]] = obj_data
            importer._create_llamaindex_object_definition(session, obj_data)

        # TypeノードをLlamaIndex形式へ
        type_records = session.run(
            """
            MATCH (t:Type)
            RETURN t.name AS name,
                   t.description AS description
            """
        ).data()
        for record in type_records:
            type_data = {
                "name": record.get("name"),
                "description": record.get("description") or "",
            }
            importer._create_llamaindex_type(session, type_data)

        # FunctionノードをLlamaIndex形式へ
        function_records = session.run(
            """
            MATCH (f:Function)
            RETURN f.name AS name,
                   f.description AS description,
                   f.category AS category,
                   f.implementation_status AS implementation_status,
                   f.notes AS notes
            """
        ).data()
        for record in function_records:
            func_data = {
                "name": record.get("name"),
                "description": record.get("description") or "",
                "category": record.get("category") or "",
                "implementation_status": record.get("implementation_status") or "",
                "notes": record.get("notes") or "",
            }
            combined_description = func_data["description"]
            importer._create_llamaindex_function(session, func_data, combined_description)

        # Parameter（Function用）をLlamaIndex形式へ
        function_param_records = session.run(
            """
            MATCH (f:Function)-[:HAS_PARAMETER]->(p:Parameter)
            RETURN f.name AS function_name,
                   p.name AS name,
                   p.description AS description,
                   p.is_required AS is_required,
                   p.type AS type,
                   p.position AS position
            """
        ).data()
        for record in function_param_records:
            param_data = {
                "name": record.get("name"),
                "description": record.get("description") or "",
                "is_required": record.get("is_required", False),
                "type": record.get("type") or "",
                "position": record.get("position", 0) or 0,
            }
            parent_function = record.get("function_name")
            importer._create_llamaindex_parameter(session, parent_function, param_data)

        # Parameter（ObjectDefinition用）をLlamaIndex形式へ
        object_property_records = session.run(
            """
            MATCH (od:ObjectDefinition)-[:HAS_PROPERTY]->(p:Parameter)
            RETURN od.name AS object_name,
                   p.name AS name,
                   p.description AS description,
                   p.type AS type
            """
        ).data()
        for record in object_property_records:
            prop_data = {
                "name": record.get("name"),
                "description": record.get("description") or "",
                "type": record.get("type") or "",
            }
            parent_object = record.get("object_name")
            importer._create_llamaindex_object_property(session, parent_object, prop_data)

        # Functionの戻り値を接続
        return_records = session.run(
            """
            MATCH (f:Function)-[:RETURNS]->(target)
            RETURN f.name AS function_name,
                   target.name AS target_name,
                   labels(target) AS labels
            """
        ).data()
        for record in return_records:
            function_name = record.get("function_name")
            target_name = record.get("target_name")
            labels = record.get("labels") or []
            is_object_definition = "ObjectDefinition" in labels
            importer._create_llamaindex_return_relationship(
                session,
                function_name,
                target_name,
                is_object_definition,
            )

        logger.info("既存データのLlamaIndex形式変換が完了しました。")
    finally:
        importer.close()


def _ensure_llamaindex_data(config: Config) -> None:
    """LlamaIndex形式データが存在しない場合に変換を実行"""
    if not config.create_llamaindex_format:
        logger.info("CREATE_LLAMAINDEX_FORMAT=false のため変換をスキップします。")
        return

    try:
        with GraphDatabase.driver(
            config.neo4j_uri,
            auth=(config.neo4j_user, config.neo4j_password),
        ) as driver:
            with driver.session(database=config.neo4j_database) as session:
                if _has_llamaindex_entities(session):
                    logger.info("既にLlamaIndex形式のエンティティが存在します。変換は不要です。")
                    return

                logger.info("LlamaIndex形式のデータが見つからないため自動変換を実行します。")
                _convert_existing_data_to_llamaindex(session, config)
    except Exception as exc:
        logger.warning(f"LlamaIndex形式への変換に失敗しました: {exc}", exc_info=True)


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
        raise ValueError(("config に neo4j_uri, neo4j_user, neo4j_password, neo4j_database が設定されていません。"))

    logger.info((f"既存のNeo4jグラフ '{db_name}' からPropertyGraphQueryEngineを構築しています..."))

    # 事前にLlamaIndex形式データを整備
    _ensure_llamaindex_data(config)

    # OpenAIのLLMと埋め込みモデルを初期化（グローバル設定を避ける）
    llm = OpenAI(**config.llamaindex_llm_config)
    embed_model = OpenAIEmbedding(**config.llamaindex_embedding_config)

    try:
        # 標準的なNeo4jPropertyGraphStoreを使用（APOCプラグインが必要）
        # ここでは環境変数の存在を既に検証済みだが、型シグネチャが str を要求するためキャスト
        assert user is not None and password is not None and uri is not None and db_name is not None
        graph_store = Neo4jPropertyGraphStore(
            username=str(user),
            password=str(password),
            url=str(uri),
            database=str(db_name),
        )

        # 既存のグラフ構造からインデックスをロード（llmとembed_modelを明示的に指定）
        # 注意: from_existingはLlamaIndexが作成した特殊なラベル（__Entity__, __Node__等）を期待する
        # 通常のNeo4jデータ（Function, Parameter等）には対応していない
        try:
            g_index = PropertyGraphIndex.from_existing(
                property_graph_store=graph_store,
                llm=llm,
                embed_model=embed_model,
            )
        except Exception as e:
            logger.warning(f"PropertyGraphIndex.from_existing failed: {e}")
            logger.info("Creating new PropertyGraphIndex for existing Neo4j data...")
            # 既存データから新しいインデックスを作成
            g_index = PropertyGraphIndex.from_vector_store(
                vector_store=None,  # ベクトルストアは使用しない
                property_graph_store=graph_store,
                llm=llm,
                embed_model=embed_model,
            )

        logger.info("PropertyGraphQueryEngineの構築が完了しました。")
        # スキーマ情報を明示的に提供してクエリエンジンを構築
        query_engine = g_index.as_query_engine(llm=llm)

        # デバッグ用: グラフストアから直接サンプルデータを取得
        try:
            with graph_store._driver.session(database=str(db_name)) as session:
                result = session.run(
                    "MATCH (n:Function) RETURN n.name AS name, n.description AS description, "
                    "n.parameters AS parameters, n.return_value AS return_value LIMIT 5"
                )
                sample_data = list(result)
                logger.info(f"サンプルFunctionノード（詳細）: {sample_data}")

                # スキーマ情報も取得
                schema_result = session.run(
                    "CALL db.schema.nodeTypeProperties() YIELD nodeType, propertyName, propertyTypes "
                    "RETURN nodeType, collect(propertyName) as properties"
                )
                schema_data = list(schema_result)
                logger.info(f"グラフスキーマ: {schema_data}")
        except Exception as e:
            logger.warning(f"サンプルデータ取得に失敗: {e}")

        return query_engine

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


def build_langchain_wrapped_engines(config: Config):
    """LangChainでラップしたエンジンを構築（LangSmithでウォッチ可能）"""

    # LangChainのLLMとEmbeddings（サポートされる引数のみを指定）
    llm_kwargs: Dict[str, Any] = {"model": config.llm_model}
    if config.openai_api_key:
        llm_kwargs["api_key"] = config.openai_api_key
    llm = ChatOpenAI(**llm_kwargs)  # type: ignore[arg-type]
    embeddings = OpenAIEmbeddings(**config.langchain_embedding_config)  # type: ignore[arg-type]

    # ベクトル検索のラッパー
    def vector_search_wrapper(query: str):
        """ベクトル検索をLangChainでラップ"""
        try:
            vector_engine = build_vector_engine(
                persist_dir=config.chroma_persist_directory,
                collection=config.chroma_collection_name,
                config=config
            )
            return vector_engine.query(query)
        except Exception as e:
            logger.error(f"ベクトル検索エラー: {e}")
            return f"ベクトル検索でエラーが発生しました: {e}"

    # グラフ検索のラッパー
    def graph_search_wrapper(
        query: str,
        *,
        on_result: Optional[Any] = None,
        on_empty: Optional[Any] = None,
        on_error: Optional[Any] = None,
        diagnose: bool = False,
        keyword: Optional[str] = None,
    ):
        """グラフ検索をLangChainでラップ

        on_result(response: Any) -> None: 成功時に呼ばれるコールバック
        on_empty(info: dict) -> None: 結果が空/実質空のときに呼ばれるコールバック
        on_error(error: Exception) -> None: 例外時に呼ばれるコールバック
        """
        try:
            graph_engine = build_graph_engine(config)
            response = graph_engine.query(query)

            # 空判定: None, 空文字, "Empty Response" 等
            as_str = str(response).strip() if response is not None else ""
            # デバッグ用: レスポンスの詳細をログ出力
            logger.debug(f"グラフ検索レスポンス: {repr(response)}")
            logger.debug(f"グラフ検索レスポンス (文字列): {repr(as_str)}")
            is_empty = (not as_str) or (as_str in ("", "Empty Response"))

            if is_empty:
                diag: Optional[dict] = None
                if diagnose:
                    diag = {}
                    try:
                        with GraphDatabase.driver(
                            config.neo4j_uri,
                            auth=(config.neo4j_user, config.neo4j_password),
                        ) as driver:
                            with driver.session(database=config.neo4j_database) as session:
                                # 全体件数
                                total_funcs = session.run("MATCH (f:Function) RETURN count(f) AS c").single()
                                diag["function_count"] = (total_funcs and total_funcs.get("c")) or 0
                                # キーワード一致件数
                                kw = keyword or ""
                                match_funcs = session.run(
                                    (
                                        "MATCH (f:Function) "
                                        "WHERE toLower(f.name) CONTAINS toLower($kw) "
                                        "RETURN count(f) AS c"
                                    ),
                                    kw=kw,
                                ).single()
                                diag["match_count_by_keyword"] = (match_funcs and match_funcs.get("c")) or 0
                                # サンプル名
                                sample = session.run(
                                    "MATCH (f:Function) RETURN f.name AS name LIMIT 5"
                                )
                                diag["sample_function_names"] = [r.get("name") for r in sample if r.get("name")]
                                # Parameter の存在
                                total_params = session.run("MATCH (p:Parameter) RETURN count(p) AS c").single()
                                diag["parameter_count"] = (total_params and total_params.get("c")) or 0
                    except Exception:
                        # 診断に失敗しても無視
                        pass
                if callable(on_empty):
                    try:
                        on_empty({
                            "query": query,
                            "raw_response": response,
                            "normalized": as_str,
                            "diagnosis": diag,
                            "keyword": keyword,
                        })
                    except Exception:
                        # コールバック失敗は主処理に影響させない
                        pass
            else:
                if callable(on_result):
                    try:
                        on_result(response)
                    except Exception:
                        pass

            return response
        except Exception as e:
            logger.error(f"グラフ検索エラー: {e}")
            if callable(on_error):
                try:
                    on_error(e)
                except Exception:
                    pass
            return f"グラフ検索でエラーが発生しました: {e}"

    # 統合回答生成のラッパー
    def generate_integrated_response(vector_result: str, graph_result: str, question: str):
        """統合回答をLangChainで生成"""
        try:
            messages = [
                SystemMessage(content="""あなたはAPIドキュメントの専門家です。
以下の検索結果を統合して、ユーザーの質問に包括的に回答してください。

回答のガイドライン:
- 両方の検索結果の情報を統合
- 具体的なAPI関数名とその使用方法を明記
- パラメータの詳細と戻り値について説明
- 実用的なコード例があれば提供
- 不明な点は正直に「不明」と回答
- 日本語で回答"""),
                HumanMessage(content=f"""
【ベクトル検索結果】
{vector_result}

【グラフ検索結果】
{graph_result}

【ユーザーの質問】
{question}

上記の情報を統合して回答してください。""")
            ]
            response = llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"統合回答生成エラー: {e}")
            return f"統合回答生成でエラーが発生しました: {e}"

    return {
        'vector_search': vector_search_wrapper,
        'graph_search': graph_search_wrapper,
        'generate_response': generate_integrated_response,
        'llm': llm,
        'embeddings': embeddings
    }
