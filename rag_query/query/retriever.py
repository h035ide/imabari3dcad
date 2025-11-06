"""
データ検索モジュール

グラフデータベースとベクトルデータベースからの情報検索を行います。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..core.logger import get_logger
from ..core.exceptions import QueryError
from ..storage.neo4j_manager import Neo4jManager
from ..storage.chroma_manager import ChromaManager

logger = get_logger(__name__)


class BaseRetriever(ABC):
    """検索エンジンの基底クラス"""
    
    @abstractmethod
    def search(self, query: str, max_results: int = 10, 
               filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """検索を実行する"""
        pass


class GraphRetriever(BaseRetriever):
    """グラフデータベース検索エンジン"""
    
    def __init__(self, neo4j_manager: Neo4jManager):
        """
        初期化
        
        Args:
            neo4j_manager: Neo4jマネージャー
        """
        self.neo4j_manager = neo4j_manager
    
    def search(self, query: str, max_results: int = 10, 
               filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        グラフデータベースから検索する
        
        Args:
            query: 検索クエリ
            max_results: 最大結果数
            filters: 検索フィルタ
            
        Returns:
            検索結果のリスト
        """
        try:
            # 簡単なテキスト検索クエリを構築（将来的にはより高度な検索に発展）
            cypher_query = """
            MATCH (n)
            WHERE toLower(n.name) CONTAINS toLower($query)
               OR any(prop IN keys(n) WHERE toLower(toString(n[prop])) CONTAINS toLower($query))
            RETURN n.id as id, labels(n)[0] as type, n as properties
            LIMIT $limit
            """
            
            params = {
                "query": query,
                "limit": max_results
            }
            
            results = self.neo4j_manager.execute_query(cypher_query, params)
            
            logger.info(f"グラフ検索完了: {len(results)}件")
            return results
            
        except Exception as e:
            raise QueryError(f"グラフ検索エラー", str(e))
    
    def find_similar_methods(self, method_name: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        類似するメソッドを検索する
        
        Args:
            method_name: メソッド名
            max_results: 最大結果数
            
        Returns:
            類似メソッドのリスト
        """
        try:
            cypher_query = """
            MATCH (m:Method)
            WHERE m.name <> $method_name
              AND (toLower(m.name) CONTAINS toLower($method_name)
                   OR toLower(m.description) CONTAINS toLower($method_name))
            RETURN m.name as method_name, m.description as description
            LIMIT $limit
            """
            
            params = {
                "method_name": method_name,
                "limit": max_results
            }
            
            results = self.neo4j_manager.execute_query(cypher_query, params)
            
            logger.info(f"類似メソッド検索完了: {len(results)}件")
            return results
            
        except Exception as e:
            logger.error(f"類似メソッド検索エラー: {e}")
            return []
    
    def find_method_usage_examples(self, method_name: str) -> List[Dict[str, Any]]:
        """
        メソッドの使用例を検索する
        
        Args:
            method_name: メソッド名
            
        Returns:
            使用例のリスト
        """
        try:
            cypher_query = """
            MATCH (m:Method {name: $method_name})<-[:CALLS]-(call:MethodCall)
            MATCH (call)<-[:CONTAINS]-(script:ScriptExample)
            RETURN script.name as script_name, script.code as code, call.code as call_code
            """
            
            params = {"method_name": method_name}
            results = self.neo4j_manager.execute_query(cypher_query, params)
            
            logger.info(f"使用例検索完了: {len(results)}件")
            return results
            
        except Exception as e:
            logger.error(f"使用例検索エラー: {e}")
            return []


class VectorRetriever(BaseRetriever):
    """ベクトルデータベース検索エンジン"""
    
    def __init__(self, chroma_manager: ChromaManager):
        """
        初期化
        
        Args:
            chroma_manager: ChromaDBマネージャー
        """
        self.chroma_manager = chroma_manager
        self._vectorstore = None
    
    @property
    def vectorstore(self):
        """ベクトルストアを取得（遅延初期化）"""
        if self._vectorstore is None:
            self._vectorstore = self.chroma_manager.load_vectorstore()
        return self._vectorstore
    
    def search(self, query: str, max_results: int = 10, 
               filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        ベクトルデータベースから検索する
        
        Args:
            query: 検索クエリ
            max_results: 最大結果数
            filters: 検索フィルタ
            
        Returns:
            検索結果のリスト
        """
        try:
            # 類似度検索を実行
            docs_with_scores = self.vectorstore.similarity_search_with_score(
                query=query,
                k=max_results
            )
            
            results = []
            for doc, score in docs_with_scores:
                result = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": score
                }
                results.append(result)
            
            logger.info(f"ベクトル検索完了: {len(results)}件")
            return results
            
        except Exception as e:
            raise QueryError(f"ベクトル検索エラー", str(e))
    
    def find_similar_content(self, content: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        指定されたコンテンツに類似するコンテンツを検索する
        
        Args:
            content: 検索対象コンテンツ
            max_results: 最大結果数
            
        Returns:
            類似コンテンツのリスト
        """
        try:
            return self.search(content, max_results)
        except Exception as e:
            logger.error(f"類似コンテンツ検索エラー: {e}")
            return []
