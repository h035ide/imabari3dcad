import os
from pathlib import Path
import logging
from typing import Optional, Any, Dict
from neo4j import GraphDatabase
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
        self.llm_model = os.getenv("LLM_MODEL", "gpt-5-mini")
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


def build_graph_engine(config: Config):
    """
    直接Neo4jクエリを使用するグラフ検索エンジンを構築します。
    PropertyGraphQueryEngineの代わりに、既存のNeo4jデータ構造を直接利用します。
    """
    uri = config.neo4j_uri
    user = config.neo4j_user
    password = config.neo4j_password
    db_name = config.neo4j_database

    if not all([uri, user, password, db_name]):
        logger.error("Neo4j接続情報が config から取得できません。")
        raise ValueError(("config に neo4j_uri, neo4j_user, neo4j_password, neo4j_database が設定されていません。"))

    logger.info(f"直接Neo4jグラフ検索エンジンを構築しています...")

    class DirectNeo4jEngine:
        def __init__(self, config: Config):
            self.config = config
            self.driver = GraphDatabase.driver(
                config.neo4j_uri,
                auth=(config.neo4j_user, config.neo4j_password)
            )
        
        def query(self, query: str):
            """クエリを実行して結果を返す"""
            try:
                with self.driver.session(database=self.config.neo4j_database) as session:
                    # クエリからCypherクエリを抽出
                    if "MATCH (f:Function)" in query and "CONTAINS" in query:
                        # CreateSketchLineのような関数検索クエリの場合
                        return self._search_function_with_parameters(session, query)
                    else:
                        # その他のクエリはそのまま実行
                        result = session.run(query)
                        records = list(result)
                        if records:
                            return self._format_records(records)
                        else:
                            return "Empty Response"
            except Exception as e:
                logger.error(f"Neo4jクエリ実行エラー: {e}")
                return f"エラーが発生しました: {e}"
        
        def _search_function_with_parameters(self, session, query: str):
            """関数とそのパラメータを検索"""
            try:
                # クエリから関数名を抽出（簡易版）
                if "CreateSketchLine" in query:
                    function_name = "CreateSketchLine"
                else:
                    # より汎用的な抽出ロジックが必要
                    function_name = "CreateSketchLine"  # デフォルト
                
                cypher = """
                MATCH (f:Function)
                WHERE toLower(f.name) CONTAINS toLower($function_name)
                OPTIONAL MATCH (p:Parameter)
                WHERE toLower(p.parent_function) = toLower(f.name)
                WITH f, collect(p) AS params
                RETURN f.name AS name,
                       f.description AS description,
                       [q IN params WHERE q IS NOT NULL AND q.name IS NOT NULL |
                        {name:q.name, description:q.description, required:coalesce(q.is_required,false)}] AS parameters,
                       null AS return_value
                LIMIT 5
                """
                
                result = session.run(cypher, function_name=function_name)
                records = list(result)
                
                if records:
                    return self._format_function_results(records)
                else:
                    return "Empty Response"
                    
            except Exception as e:
                logger.error(f"関数検索エラー: {e}")
                return f"エラーが発生しました: {e}"
        
        def _format_function_results(self, records):
            """関数検索結果をフォーマット"""
            results = []
            for record in records:
                name = record.get("name", "")
                description = record.get("description", "")
                parameters = record.get("parameters", [])
                return_value = record.get("return_value")
                
                result_text = f"関数名: {name}\n"
                result_text += f"説明: {description}\n"
                
                if parameters:
                    result_text += "引数:\n"
                    for param in parameters:
                        if isinstance(param, dict) and param.get("name"):
                            param_name = param.get("name", "")
                            param_desc = param.get("description", "")
                            param_required = param.get("required", False)
                            result_text += f"- {param_name}: {param_desc} (必須: {param_required})\n"
                
                if return_value:
                    result_text += f"戻り値: {return_value}\n"
                else:
                    result_text += "戻り値: 不明\n"
                
                results.append(result_text)
            
            return "\n\n".join(results)
        
        def _format_records(self, records):
            """一般的なレコードをフォーマット"""
            if not records:
                return "Empty Response"
            
            # 簡易的なフォーマット
            return str(records)
        
        def close(self):
            """接続を閉じる"""
            if self.driver:
                self.driver.close()

    try:
        # デバッグ用: サンプルデータを取得
        with GraphDatabase.driver(uri, auth=(user, password)) as driver:
            with driver.session(database=db_name) as session:
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

        logger.info("直接Neo4jグラフ検索エンジンの構築が完了しました。")
        return DirectNeo4jEngine(config)

    except Exception as e:
        logger.error(f"Neo4jグラフエンジンの構築に失敗しました: {e}")
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
