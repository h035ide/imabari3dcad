"""
クエリ処理エンジン

ユーザークエリを受け取り、グラフとベクトル検索を統合してレスポンスを生成します。
"""

from typing import Dict, Any, List
from ..core.models import QueryRequest, QueryResponse
from ..core.logger import get_logger
from ..core.exceptions import QueryError
from .retriever import GraphRetriever, VectorRetriever
from .response_generator import ResponseGenerator

logger = get_logger(__name__)


class QueryProcessor:
    """クエリ処理エンジン"""

    def __init__(
        self,
        graph_retriever: GraphRetriever,
        vector_retriever: VectorRetriever,
        response_generator: ResponseGenerator,
    ):
        """
        初期化

        Args:
            graph_retriever: グラフ検索エンジン
            vector_retriever: ベクトル検索エンジン
            response_generator: レスポンス生成エンジン
        """
        self.graph_retriever = graph_retriever
        self.vector_retriever = vector_retriever
        self.response_generator = response_generator

    def process_query(self, request: QueryRequest) -> QueryResponse:
        """
        クエリを処理してレスポンスを生成する

        Args:
            request: クエリリクエスト

        Returns:
            クエリレスポンス

        Raises:
            QueryError: クエリ処理エラー時
        """
        try:
            logger.info(f"クエリ処理開始: {request.query}")

            # グラフ検索を実行
            graph_results = self.graph_retriever.search(
                query=request.query,
                max_results=request.max_results,
                filters=request.filters,
            )

            # ベクトル検索を実行
            vector_results = self.vector_retriever.search(
                query=request.query,
                max_results=request.max_results,
                filters=request.filters,
            )

            # 結果を統合してレスポンスを生成
            response = self.response_generator.generate_response(
                query=request.query,
                graph_results=graph_results,
                vector_results=vector_results,
            )

            logger.info(f"クエリ処理完了: {len(response.results)}件の結果")
            return response

        except Exception as e:
            raise QueryError(f"クエリ処理に失敗しました", str(e))

    def get_similar_methods(
        self, method_name: str, max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        指定されたメソッドに類似するメソッドを取得する

        Args:
            method_name: メソッド名
            max_results: 最大結果数

        Returns:
            類似メソッドのリスト
        """
        try:
            return self.graph_retriever.find_similar_methods(method_name, max_results)
        except Exception as e:
            logger.error(f"類似メソッド検索エラー: {e}")
            return []

    def get_method_usage_examples(self, method_name: str) -> List[Dict[str, Any]]:
        """
        指定されたメソッドの使用例を取得する

        Args:
            method_name: メソッド名

        Returns:
            使用例のリスト
        """
        try:
            return self.graph_retriever.find_method_usage_examples(method_name)
        except Exception as e:
            logger.error(f"使用例検索エラー: {e}")
            return []
