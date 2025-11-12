"""
Neo4jデータベース管理モジュール

Neo4jグラフデータベースへの接続、データ投入、クエリ実行を管理します。
"""

from typing import List, Tuple, Dict, Any
from langchain_neo4j import Neo4jGraph
from langchain_community.graphs.graph_document import GraphDocument
from neo4j.exceptions import ServiceUnavailable

from ..core.logger import get_logger
from ..core.exceptions import StorageError

logger = get_logger(__name__)


class Neo4jManager:
    """Neo4jデータベース管理クラス"""

    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        """
        初期化

        Args:
            uri: Neo4jデータベースURI
            username: ユーザー名
            password: パスワード
            database: データベース名
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self._graph = None

    @property
    def graph(self) -> Neo4jGraph:
        """Neo4jGraphインスタンスを取得（遅延初期化）"""
        if self._graph is None:
            try:
                self._graph = Neo4jGraph(
                    url=self.uri,
                    username=self.username,
                    password=self.password,
                    database=self.database,
                )
                logger.info(f"Neo4jに接続しました: {self.uri}")
            except ServiceUnavailable as e:
                raise StorageError(f"Neo4jへの接続に失敗しました: {self.uri}", str(e))
            except Exception as e:
                raise StorageError(f"Neo4j接続エラー", str(e))

        return self._graph

    def clear_database(self) -> None:
        """
        データベースの全データを削除する

        Raises:
            StorageError: 削除処理エラー時
        """
        try:
            logger.info("Neo4jデータベースをクリア中...")
            delete_query = "MATCH (n) DETACH DELETE n"
            self.graph.query(delete_query)
            logger.info("Neo4jデータベースのクリア完了")
        except Exception as e:
            raise StorageError(f"Neo4jデータベースのクリアに失敗しました", str(e))

    def load_graph_documents(self, graph_docs: List[GraphDocument]) -> Tuple[int, int]:
        """
        GraphDocumentをNeo4jに投入する

        Args:
            graph_docs: GraphDocumentのリスト

        Returns:
            (ノード数, リレーションシップ数)

        Raises:
            StorageError: データ投入エラー時
        """
        try:
            logger.info("Neo4jにグラフデータを投入中...")

            # データを投入
            self.graph.add_graph_documents(graph_docs)

            # 投入後の統計を取得
            node_count = self._get_node_count()
            rel_count = self._get_relationship_count()

            logger.info(
                f"Neo4jデータ投入完了: ノード={node_count}件, リレーション={rel_count}件"
            )
            return node_count, rel_count

        except Exception as e:
            raise StorageError(f"Neo4jデータ投入に失敗しました", str(e))

    def rebuild_database(self, graph_docs: List[GraphDocument]) -> Tuple[int, int]:
        """
        データベースを再構築する（クリア + データ投入）

        Args:
            graph_docs: GraphDocumentのリスト

        Returns:
            (ノード数, リレーションシップ数)

        Raises:
            StorageError: 再構築エラー時
        """
        try:
            # 既存データをクリア
            self.clear_database()

            # 新しいデータを投入
            return self.load_graph_documents(graph_docs)

        except Exception as e:
            raise StorageError(f"Neo4jデータベースの再構築に失敗しました", str(e))

    def execute_query(
        self, query: str, params: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Cypherクエリを実行する

        Args:
            query: Cypherクエリ
            params: クエリパラメータ

        Returns:
            クエリ結果

        Raises:
            StorageError: クエリ実行エラー時
        """
        try:
            if params is None:
                params = {}

            result = self.graph.query(query, params)
            return result

        except Exception as e:
            raise StorageError(f"Neo4jクエリ実行エラー", str(e))

    def get_database_stats(self) -> Dict[str, int]:
        """
        データベースの統計情報を取得する

        Returns:
            統計情報辞書

        Raises:
            StorageError: 統計取得エラー時
        """
        try:
            node_count = self._get_node_count()
            rel_count = self._get_relationship_count()

            return {"node_count": node_count, "relationship_count": rel_count}

        except Exception as e:
            raise StorageError(f"Neo4j統計情報取得エラー", str(e))

    def _get_node_count(self) -> int:
        """ノード数を取得する"""
        result = self.graph.query("MATCH (n) RETURN count(n) AS c")
        return int(result[0]["c"]) if result else 0

    def _get_relationship_count(self) -> int:
        """リレーションシップ数を取得する"""
        result = self.graph.query("MATCH ()-[r]->() RETURN count(r) AS c")
        return int(result[0]["c"]) if result else 0

    def close(self) -> None:
        """接続を閉じる"""
        if self._graph:
            # Neo4jGraphには明示的なclose()メソッドがないため、
            # インスタンスをクリアするのみ
            self._graph = None
            logger.info("Neo4j接続を閉じました")
