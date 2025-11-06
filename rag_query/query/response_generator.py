"""
レスポンス生成モジュール

検索結果を統合してユーザーに返すレスポンスを生成します。
"""

import time
from typing import List, Dict, Any
from ..core.models import QueryResponse
from ..core.logger import get_logger

logger = get_logger(__name__)


class ResponseGenerator:
    """レスポンス生成クラス"""

    def __init__(self):
        """初期化"""
        pass

    def generate_response(
        self,
        query: str,
        graph_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
    ) -> QueryResponse:
        """
        検索結果を統合してレスポンスを生成する

        Args:
            query: 元のクエリ
            graph_results: グラフ検索結果
            vector_results: ベクトル検索結果

        Returns:
            統合されたクエリレスポンス
        """
        start_time = time.time()

        try:
            # 結果を統合
            integrated_results = self._integrate_results(graph_results, vector_results)

            # 結果をランク付け
            ranked_results = self._rank_results(integrated_results, query)

            # レスポンスを生成
            processing_time = time.time() - start_time

            response = QueryResponse(
                results=ranked_results,
                total_count=len(ranked_results),
                processing_time=processing_time,
                metadata={
                    "graph_result_count": len(graph_results),
                    "vector_result_count": len(vector_results),
                    "query": query,
                },
            )

            logger.info(f"レスポンス生成完了: {len(ranked_results)}件")
            return response

        except Exception as e:
            logger.error(f"レスポンス生成エラー: {e}")
            # エラー時は空のレスポンスを返す
            return QueryResponse(
                results=[],
                total_count=0,
                processing_time=time.time() - start_time,
                metadata={"error": str(e)},
            )

    def _integrate_results(
        self, graph_results: List[Dict[str, Any]], vector_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        グラフ検索結果とベクトル検索結果を統合する

        Args:
            graph_results: グラフ検索結果
            vector_results: ベクトル検索結果

        Returns:
            統合された結果のリスト
        """
        integrated = []

        # グラフ検索結果を追加
        for result in graph_results:
            integrated_result = {
                "source": "graph",
                "type": result.get("type", "unknown"),
                "id": result.get("id", ""),
                "properties": result.get("properties", {}),
                "relevance_score": 0.8,  # グラフ検索の基本スコア
            }
            integrated.append(integrated_result)

        # ベクトル検索結果を追加
        for result in vector_results:
            integrated_result = {
                "source": "vector",
                "type": result.get("metadata", {}).get("node_type", "unknown"),
                "id": result.get("metadata", {}).get("node_id", ""),
                "content": result.get("content", ""),
                "metadata": result.get("metadata", {}),
                "relevance_score": 1.0
                - result.get("similarity_score", 0.5),  # スコアを逆転
            }
            integrated.append(integrated_result)

        return integrated

    def _rank_results(
        self, results: List[Dict[str, Any]], query: str
    ) -> List[Dict[str, Any]]:
        """
        結果をランク付けする

        Args:
            results: 統合された結果のリスト
            query: 元のクエリ

        Returns:
            ランク付けされた結果のリスト
        """

        # 簡単なランキング（将来的にはより高度なアルゴリズムに発展）
        def calculate_score(result):
            base_score = result.get("relevance_score", 0.0)

            # ソースによる重み付け
            if result.get("source") == "graph":
                base_score *= 1.1  # グラフ検索を少し優遇

            # タイプによる重み付け
            if result.get("type") == "Method":
                base_score *= 1.2  # メソッドを優遇
            elif result.get("type") == "ScriptExample":
                base_score *= 1.1  # スクリプト例を優遇

            return base_score

        # スコアでソート（降順）
        ranked_results = sorted(results, key=calculate_score, reverse=True)

        return ranked_results
