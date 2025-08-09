"""
LangChain Interface for imabari3dcad

このモジュールは、LangChainを使用したインターフェースを提供します。
Neo4jグラフインデックスとChromaベクトルストアをサポートし、
高い独立性を持ち、簡単に取り付けることができます。
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

# ベースクラスとして最小限の実装を提供
logger = logging.getLogger(__name__)

@dataclass
class ConnectionConfig:
    """接続設定用のデータクラス"""
    # Neo4j設定
    neo4j_uri: str = "neo4j://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"
    
    # Chroma設定
    chroma_persist_directory: str = "./chroma_db"
    chroma_collection_name: str = "imabari3dcad"
    
    # OpenAI設定
    openai_api_key: str = ""
    model_name: str = "gpt-3.5-turbo"
    embedding_model: str = "text-embedding-ada-002"
    
    @classmethod
    def from_env(cls) -> 'ConnectionConfig':
        """環境変数から設定を読み込み"""
        return cls(
            neo4j_uri=os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
            neo4j_username=os.getenv("NEO4J_USERNAME", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD", ""),
            neo4j_database=os.getenv("NEO4J_DATABASE", "neo4j"),
            chroma_persist_directory=os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"),
            chroma_collection_name=os.getenv("CHROMA_COLLECTION", "imabari3dcad"),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            model_name=os.getenv("MODEL_NAME", "gpt-3.5-turbo"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
        )


class BaseGraphIndex(ABC):
    """グラフインデックスのベースクラス"""
    
    @abstractmethod
    def query(self, query: str, **kwargs) -> str:
        """グラフに対してクエリを実行"""
        pass
    
    @abstractmethod
    def add_documents(self, documents: List[str]) -> None:
        """ドキュメントをグラフに追加"""
        pass


class BaseVectorStore(ABC):
    """ベクトルストアのベースクラス"""
    
    @abstractmethod
    def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """類似度検索を実行"""
        pass
    
    @abstractmethod
    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict]] = None) -> None:
        """テキストをベクトルストアに追加"""
        pass


class Neo4jGraphIndex(BaseGraphIndex):
    """Neo4jグラフインデックスの実装"""
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.driver = None
        self._init_connection()
    
    def _init_connection(self):
        """Neo4j接続を初期化"""
        try:
            # neo4jライブラリが利用可能な場合のみ接続
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                self.config.neo4j_uri,
                auth=(self.config.neo4j_username, self.config.neo4j_password)
            )
            logger.info("Neo4jに正常に接続しました")
        except ImportError:
            logger.warning("neo4jライブラリが見つかりません。モックモードで動作します")
            self.driver = None
        except Exception as e:
            logger.error(f"Neo4j接続エラー: {e}")
            self.driver = None
    
    def query(self, query: str, **kwargs) -> str:
        """Cypherクエリを実行"""
        if not self.driver:
            return f"Mock response for query: {query}"
        
        try:
            with self.driver.session(database=self.config.neo4j_database) as session:
                result = session.run(query, **kwargs)
                records = [record.data() for record in result]
                return str(records)
        except Exception as e:
            logger.error(f"クエリ実行エラー: {e}")
            return f"エラー: {str(e)}"
    
    def add_documents(self, documents: List[str]) -> None:
        """ドキュメントをグラフに追加"""
        if not self.driver:
            logger.warning("Neo4j接続がないため、ドキュメント追加をスキップします")
            return
        
        # 簡単な実装例
        try:
            with self.driver.session(database=self.config.neo4j_database) as session:
                for i, doc in enumerate(documents):
                    session.run(
                        "CREATE (d:Document {id: $id, content: $content})",
                        id=i, content=doc
                    )
            logger.info(f"{len(documents)}個のドキュメントを追加しました")
        except Exception as e:
            logger.error(f"ドキュメント追加エラー: {e}")
    
    def close(self):
        """接続を閉じる"""
        if self.driver:
            self.driver.close()


class ChromaVectorStore(BaseVectorStore):
    """Chromaベクトルストアの実装"""
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.client = None
        self.collection = None
        self._init_connection()
    
    def _init_connection(self):
        """Chroma接続を初期化"""
        try:
            import chromadb
            self.client = chromadb.PersistentClient(path=self.config.chroma_persist_directory)
            self.collection = self.client.get_or_create_collection(
                name=self.config.chroma_collection_name
            )
            logger.info("Chromaに正常に接続しました")
        except ImportError:
            logger.warning("chromadbライブラリが見つかりません。モックモードで動作します")
            self.client = None
            self.collection = None
        except Exception as e:
            logger.error(f"Chroma接続エラー: {e}")
            self.client = None
            self.collection = None
    
    def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """類似度検索を実行"""
        if not self.collection:
            return [{"content": f"Mock result for query: {query}", "score": 0.9}]
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=k
            )
            
            formatted_results = []
            for i, doc in enumerate(results.get('documents', [[]])[0]):
                metadata = results.get('metadatas', [[]])[0][i] if i < len(results.get('metadatas', [[]])[0]) else {}
                distance = results.get('distances', [[]])[0][i] if i < len(results.get('distances', [[]])[0]) else 0.0
                
                formatted_results.append({
                    "content": doc,
                    "metadata": metadata,
                    "score": 1.0 - distance  # 距離をスコアに変換
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"類似度検索エラー: {e}")
            return []
    
    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict]] = None) -> None:
        """テキストをベクトルストアに追加"""
        if not self.collection:
            logger.warning("Chroma接続がないため、テキスト追加をスキップします")
            return
        
        try:
            ids = [f"doc_{i}" for i in range(len(texts))]
            self.collection.add(
                documents=texts,
                metadatas=metadatas or [{}] * len(texts),
                ids=ids
            )
            logger.info(f"{len(texts)}個のテキストを追加しました")
        except Exception as e:
            logger.error(f"テキスト追加エラー: {e}")


class LangChainInterface:
    """
    LangChainインターフェースの統合クラス
    
    Neo4jグラフインデックスとChromaベクトルストアを統合し、
    高レベルなAPIを提供します。
    """
    
    def __init__(self, config: Optional[ConnectionConfig] = None):
        self.config = config or ConnectionConfig.from_env()
        self.graph_index = Neo4jGraphIndex(self.config)
        self.vector_store = ChromaVectorStore(self.config)
        logger.info("LangChainインターフェースを初期化しました")
    
    def hybrid_search(self, query: str, k: int = 5) -> Dict[str, Any]:
        """
        グラフとベクトルの両方を使用したハイブリッド検索
        """
        try:
            # ベクトル検索
            vector_results = self.vector_store.similarity_search(query, k=k)
            
            # グラフ検索（簡単なクエリ例）
            graph_query = f"MATCH (n) WHERE n.content CONTAINS '{query}' RETURN n LIMIT {k}"
            graph_results = self.graph_index.query(graph_query)
            
            return {
                "vector_results": vector_results,
                "graph_results": graph_results,
                "query": query
            }
        except Exception as e:
            logger.error(f"ハイブリッド検索エラー: {e}")
            return {"error": str(e)}
    
    def add_document(self, content: str, metadata: Optional[Dict] = None) -> None:
        """
        ドキュメントをグラフとベクトルストアの両方に追加
        """
        try:
            # ベクトルストアに追加
            self.vector_store.add_texts([content], [metadata] if metadata else None)
            
            # グラフインデックスに追加
            self.graph_index.add_documents([content])
            
            logger.info("ドキュメントを両方のストアに追加しました")
        except Exception as e:
            logger.error(f"ドキュメント追加エラー: {e}")
    
    def query_graph(self, cypher_query: str, **params) -> str:
        """
        グラフに対して直接Cypherクエリを実行
        """
        return self.graph_index.query(cypher_query, **params)
    
    def search_vectors(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        ベクトルストアで類似度検索を実行
        """
        return self.vector_store.similarity_search(query, k=k)
    
    def get_connection_status(self) -> Dict[str, bool]:
        """
        接続状態を確認
        """
        return {
            "neo4j_connected": self.graph_index.driver is not None,
            "chroma_connected": self.vector_store.collection is not None
        }
    
    def close(self):
        """
        すべての接続を閉じる
        """
        try:
            self.graph_index.close()
            logger.info("LangChainインターフェースを正常に終了しました")
        except Exception as e:
            logger.error(f"終了時エラー: {e}")


# 便利な関数
def create_interface(config_dict: Optional[Dict[str, Any]] = None) -> LangChainInterface:
    """
    設定辞書からLangChainインターフェースを作成
    
    Args:
        config_dict: 設定を含む辞書（None の場合は環境変数を使用）
    
    Returns:
        LangChainInterface: 初期化されたインターフェース
    """
    if config_dict:
        config = ConnectionConfig(**config_dict)
    else:
        config = ConnectionConfig.from_env()
    
    return LangChainInterface(config)


def quick_search(query: str, config: Optional[ConnectionConfig] = None) -> Dict[str, Any]:
    """
    クイック検索用の便利関数
    """
    interface = LangChainInterface(config)
    try:
        return interface.hybrid_search(query)
    finally:
        interface.close()


if __name__ == "__main__":
    # 使用例
    logging.basicConfig(level=logging.INFO)
    
    # インターフェースの作成
    interface = create_interface()
    
    # 接続状態の確認
    status = interface.get_connection_status()
    print(f"接続状態: {status}")
    
    # サンプルドキュメントの追加
    interface.add_document(
        "これはテストドキュメントです。3D CADアプリケーションに関する情報が含まれています。",
        {"type": "test", "category": "cad"}
    )
    
    # ハイブリッド検索のテスト
    results = interface.hybrid_search("3D CAD")
    print(f"検索結果: {results}")
    
    # 終了
    interface.close()