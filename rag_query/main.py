"""
RAG Query メインエントリーポイント

データ取り込みとクエリ処理の統合エントリーポイントを提供します。
"""

import time
from pathlib import Path
from typing import Optional

from .core.logger import (
    get_logger,
    setup_progress_logger,
    set_global_log_file,
    add_file_handler_to_existing_loggers,
)
from .core.exceptions import RAGQueryError, ConfigurationError
from .core.models import QueryRequest
from .utils.validation import validate_config
from .config import (
    _load_yaml_config,
    OPENAI_API_KEY,
    NEO4J_URI,
    NEO4J_USER,
    NEO4J_PASSWORD,
    NEO4J_DATABASE,
)
from .ingestion.orchestrator import IngestionOrchestrator
from .storage.neo4j_manager import Neo4jManager
from .storage.chroma_manager import ChromaManager
from .storage.graph_builder import GraphBuilder
from .query.query_processor import QueryProcessor
from .query.retriever import GraphRetriever, VectorRetriever
from .query.response_generator import ResponseGenerator

# ロガーは初期化時に設定される（デフォルトではログファイルなし）
logger = None
progress_logger = None


class RAGQueryApp:
    """RAG Query アプリケーションクラス"""

    def __init__(self, config_path: Optional[Path] = None):
        """
        初期化

        Args:
            config_path: 設定ファイルパス（指定しない場合はデフォルト）
        """
        self.config = self._load_config(config_path)
        self._validate_config()

        # ロガーの初期化（ログファイルパスを設定）
        self._init_logging()

        # コンポーネントの初期化
        self._init_components()

    def run_ingestion(self) -> None:
        """データ取り込み処理を実行する"""
        try:
            progress_logger.info("🚀 === データ取り込み処理開始 ===")
            start_time = time.time()

            # レスポンス保存用ディレクトリを作成（response/response_YYYY-MM-DD_HHMMSS）
            from datetime import datetime
            run_stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            base_response_dir = Path(self.config.get("paths", {}).get("response_dir", "response"))
            response_dir = base_response_dir / f"response_{run_stamp}"
            response_dir.mkdir(parents=True, exist_ok=True)
            logger.info("レスポンス保存先: %s", response_dir)
            # オーケストレータとLLMへ保存先を伝播
            if hasattr(self.ingestion_orchestrator, "set_response_dir"):
                self.ingestion_orchestrator.set_response_dir(response_dir)

            # データ取り込み実行
            triples, node_props = self.ingestion_orchestrator.run_ingestion(self.config)

            # グラフドキュメント構築
            progress_logger.info("🔗 GraphDocument構築中...")
            graph_docs = self.graph_builder.build_graph_documents(triples, node_props)

            # Neo4jデータベース構築
            progress_logger.info("🗃️ Neo4jデータベース構築中...")
            node_count, rel_count = self.neo4j_manager.rebuild_database(graph_docs)

            # ChromaDBベクトルストア構築
            progress_logger.info("🔍 ChromaDBベクトルストア構築中...")
            self.chroma_manager.build_vectorstore(graph_docs)

            # 完了報告
            total_time = time.time() - start_time
            progress_logger.info("✅ === データ取り込み処理完了 ===")
            progress_logger.info("⏱️ 総処理時間: %.2f秒", total_time)
            progress_logger.info(
                "📊 Neo4j: ノード=%d件, リレーション=%d件", node_count, rel_count
            )

        except Exception as e:
            logger.error("データ取り込み処理エラー: %s", e)
            raise RAGQueryError("データ取り込み処理に失敗しました", str(e))

    def query(self, query_text: str, max_results: int = 10) -> dict:
        """
        クエリを実行する

        Args:
            query_text: クエリテキスト
            max_results: 最大結果数

        Returns:
            クエリ結果辞書
        """
        try:
            request = QueryRequest(query=query_text, max_results=max_results)
            response = self.query_processor.process_query(request)

            return {
                "query": query_text,
                "results": response.results,
                "total_count": response.total_count,
                "processing_time": response.processing_time,
                "metadata": response.metadata,
            }

        except Exception as e:
            logger.error("クエリ実行エラー: %s", e)
            raise RAGQueryError("クエリ実行に失敗しました", str(e))

    def get_database_stats(self) -> dict:
        """
        データベースの統計情報を取得する

        Returns:
            統計情報辞書
        """
        try:
            neo4j_stats = self.neo4j_manager.get_database_stats()

            return {"neo4j": neo4j_stats, "timestamp": time.time()}

        except Exception as e:
            logger.error("統計情報取得エラー: %s", e)
            return {"error": str(e)}

    def _load_config(self, config_path: Optional[Path]) -> dict:
        """設定を読み込む"""
        try:
            if config_path and config_path.exists():
                import yaml

                with open(config_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            else:
                return _load_yaml_config()
        except Exception as e:
            raise ConfigurationError("設定ファイル読み込みエラー", str(e))

    def _validate_config(self) -> None:
        """設定を検証する"""
        try:
            validate_config(self.config)

            # 必要な環境変数をチェック
            if not OPENAI_API_KEY:
                raise ConfigurationError("OPENAI_API_KEYが設定されていません")

            if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
                raise ConfigurationError("Neo4j接続情報が不完全です")

        except Exception as e:
            raise ConfigurationError("設定検証エラー", str(e))

    def _init_logging(self) -> None:
        """ロガーの初期化（ログファイルパスを設定）"""
        global logger, progress_logger

        # ログファイルパスを取得
        paths_config = self.config.get("paths", {})
        logging_config = self.config.get("logging", {})
        log_dir = Path(paths_config.get("log_dir", "log"))
        log_file_name = logging_config.get("log_file", "rag_query.log")
        log_file_path = log_dir / log_file_name

        # グローバルログファイルを設定（すべてのモジュールで共有）
        set_global_log_file(log_file_path)

        # 既存のすべてのロガーにファイルハンドラーを追加
        add_file_handler_to_existing_loggers(log_file_path)

        # ロガーを初期化
        logger = get_logger(__name__)
        progress_logger = setup_progress_logger(__name__)

    def _init_components(self) -> None:
        """コンポーネントを初期化する"""
        try:
            # データ取り込み関連
            self.ingestion_orchestrator = IngestionOrchestrator(
                openai_api_key=OPENAI_API_KEY,
                model_name=self.config.get("llm", {}).get("model_name", "gpt-4"),
                temperature=self.config.get("llm", {}).get("temperature", 0),
            )

            # ストレージ関連
            self.neo4j_manager = Neo4jManager(
                uri=NEO4J_URI,
                username=NEO4J_USER,
                password=NEO4J_PASSWORD,
                database=NEO4J_DATABASE,
            )

            chroma_persist_dir = Path(
                self.config.get("paths", {}).get("chroma_persist_dir", "data/chroma_db")
            )
            self.chroma_manager = ChromaManager(
                openai_api_key=OPENAI_API_KEY, persist_directory=chroma_persist_dir
            )

            self.graph_builder = GraphBuilder()

            # クエリ処理関連
            graph_retriever = GraphRetriever(self.neo4j_manager)
            vector_retriever = VectorRetriever(self.chroma_manager)
            response_generator = ResponseGenerator()

            self.query_processor = QueryProcessor(
                graph_retriever=graph_retriever,
                vector_retriever=vector_retriever,
                response_generator=response_generator,
            )

        except Exception as e:
            raise ConfigurationError("コンポーネント初期化エラー", str(e))


def main_ingestion() -> None:
    """データ取り込み処理のメインエントリーポイント"""
    try:
        app = RAGQueryApp()
        app.run_ingestion()
    except Exception as e:
        logger.error("アプリケーションエラー: %s", e)
        raise


def main_query(query_text: str) -> dict:
    """クエリ処理のメインエントリーポイント"""
    try:
        app = RAGQueryApp()
        return app.query(query_text)
    except Exception as e:
        logger.error("クエリ処理エラー: %s", e)
        return {"error": str(e)}


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "ingest":
            main_ingestion()
        elif command == "query" and len(sys.argv) > 2:
            query_text = " ".join(sys.argv[2:])
            result = main_query(query_text)
            print(result)
        else:
            print("使用方法:")
            print("  python -m rag_query.main ingest          # データ取り込み実行")
            print("  python -m rag_query.main query <text>    # クエリ実行")
    else:
        # デフォルトはデータ取り込み
        main_ingestion()
