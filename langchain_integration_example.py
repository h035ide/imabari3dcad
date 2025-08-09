"""
LangChain Interface Integration Example

既存のimabari3dcadプロジェクトにLangChainインターフェースを統合する方法の例
"""

import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# 新しいLangChainインターフェースをインポート
from langchain_interface import create_interface, ConnectionConfig
from langchain_advanced_rag import create_advanced_rag, RAGConfig

# 既存のコンポーネント（利用可能な場合）
try:
    from neo4j_query_engine import Neo4jQueryEngine
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

logger = logging.getLogger(__name__)

class IntegratedRAGSystem:
    """
    既存のシステムと新しいLangChainインターフェースを統合したクラス
    """
    
    def __init__(self):
        # 環境変数の読み込み
        load_dotenv()
        
        # 設定の初期化
        self.config = self._create_config()
        
        # LangChainインターフェースの初期化
        self.langchain_interface = create_interface(self._config_to_dict())
        
        # 高度なRAGシステムの初期化
        self.advanced_rag = create_advanced_rag(self._config_to_dict())
        
        # 既存のNeo4jクエリエンジン（利用可能な場合）
        self.neo4j_query_engine = None
        if NEO4J_AVAILABLE:
            try:
                self.neo4j_query_engine = Neo4jQueryEngine(
                    neo4j_uri=self.config.neo4j_uri,
                    neo4j_user=self.config.neo4j_username,
                    neo4j_password=self.config.neo4j_password,
                    database_name=self.config.neo4j_database
                )
                logger.info("既存のNeo4jクエリエンジンを統合しました")
            except Exception as e:
                logger.warning(f"既存のNeo4jクエリエンジンの初期化に失敗: {e}")
        
        logger.info("統合RAGシステムを初期化しました")
    
    def _create_config(self) -> RAGConfig:
        """環境変数から設定を作成"""
        return RAGConfig(
            # Neo4j設定
            neo4j_uri=os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
            neo4j_username=os.getenv("NEO4J_USERNAME", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD", "password"),
            neo4j_database=os.getenv("NEO4J_DATABASE", "neo4j"),
            
            # Chroma設定
            chroma_persist_directory=os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"),
            chroma_collection_name=os.getenv("CHROMA_COLLECTION", "imabari3dcad"),
            
            # OpenAI設定
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            model_name=os.getenv("MODEL_NAME", "gpt-3.5-turbo"),
            
            # RAG設定
            enable_llamaindex_integration=True,
            enable_agent=True,
            chunk_size=1000,
            max_retrieval_results=10
        )
    
    def _config_to_dict(self) -> Dict[str, Any]:
        """設定をディクショナリに変換"""
        return {
            "neo4j_uri": self.config.neo4j_uri,
            "neo4j_username": self.config.neo4j_username,
            "neo4j_password": self.config.neo4j_password,
            "neo4j_database": self.config.neo4j_database,
            "chroma_persist_directory": self.config.chroma_persist_directory,
            "chroma_collection_name": self.config.chroma_collection_name,
            "openai_api_key": self.config.openai_api_key,
            "model_name": self.config.model_name
        }
    
    def unified_search(self, query: str, search_type: str = "comprehensive") -> Dict[str, Any]:
        """
        統合検索 - 複数のインターフェースを使用
        
        Args:
            query: 検索クエリ
            search_type: "basic", "advanced", "comprehensive", "legacy"
        """
        results = {
            "query": query,
            "search_type": search_type,
            "results": {}
        }
        
        try:
            if search_type == "basic":
                # 基本的なLangChainインターフェース
                results["results"]["langchain"] = self.langchain_interface.hybrid_search(query)
            
            elif search_type == "advanced":
                # 高度なRAGシステム
                results["results"]["advanced_rag"] = self.advanced_rag.comprehensive_search(query, "hybrid")
            
            elif search_type == "comprehensive":
                # すべてのシステムを使用
                results["results"]["langchain"] = self.langchain_interface.hybrid_search(query)
                results["results"]["advanced_rag"] = self.advanced_rag.comprehensive_search(query, "comprehensive")
                
                # 既存のNeo4jクエリエンジンも使用
                if self.neo4j_query_engine:
                    try:
                        results["results"]["legacy_neo4j"] = {
                            "complex_functions": self.neo4j_query_engine.find_functions_by_complexity(3.0),
                            "code_metrics": self.neo4j_query_engine.find_code_metrics()
                        }
                    except Exception as e:
                        results["results"]["legacy_neo4j"] = {"error": str(e)}
            
            elif search_type == "legacy":
                # 既存のシステムのみ使用
                if self.neo4j_query_engine:
                    results["results"]["legacy"] = {
                        "complex_functions": self.neo4j_query_engine.find_functions_by_complexity(3.0),
                        "dependencies": self.neo4j_query_engine.find_function_dependencies("main") if query == "main" else [],
                        "metrics": self.neo4j_query_engine.find_code_metrics()
                    }
                else:
                    results["results"]["legacy"] = {"error": "Legacy system not available"}
            
            return results
            
        except Exception as e:
            logger.error(f"Unified search error: {e}")
            results["error"] = str(e)
            return results
    
    def add_document_to_all_systems(self, content: str, metadata: Dict[str, Any] = None) -> Dict[str, bool]:
        """
        すべてのシステムにドキュメントを追加
        """
        results = {}
        
        try:
            # LangChainインターフェース
            self.langchain_interface.add_document(content, metadata)
            results["langchain"] = True
        except Exception as e:
            logger.error(f"LangChain document addition error: {e}")
            results["langchain"] = False
        
        try:
            # 高度なRAGシステム
            advanced_results = self.advanced_rag.add_knowledge(content, metadata, "document")
            results["advanced_rag"] = "error" not in advanced_results
        except Exception as e:
            logger.error(f"Advanced RAG document addition error: {e}")
            results["advanced_rag"] = False
        
        return results
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        すべてのシステムの健康状態をチェック
        """
        health = {
            "timestamp": str(os.times()),
            "systems": {}
        }
        
        # LangChainインターフェース
        try:
            health["systems"]["langchain"] = self.langchain_interface.get_connection_status()
        except Exception as e:
            health["systems"]["langchain"] = {"error": str(e)}
        
        # 高度なRAGシステム  
        try:
            health["systems"]["advanced_rag"] = self.advanced_rag.get_system_status()
        except Exception as e:
            health["systems"]["advanced_rag"] = {"error": str(e)}
        
        # 既存のNeo4jシステム
        if self.neo4j_query_engine:
            try:
                metrics = self.neo4j_query_engine.find_code_metrics()
                health["systems"]["legacy_neo4j"] = {"connected": True, "metrics": metrics}
            except Exception as e:
                health["systems"]["legacy_neo4j"] = {"connected": False, "error": str(e)}
        else:
            health["systems"]["legacy_neo4j"] = {"connected": False, "reason": "Not available"}
        
        return health
    
    def close_all_connections(self):
        """すべての接続を閉じる"""
        try:
            self.langchain_interface.close()
            self.advanced_rag.close()
            logger.info("All connections closed successfully")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")


def demonstration():
    """
    LangChainインターフェースの使用例を実演
    """
    print("=== LangChain Interface Integration Demonstration ===\n")
    
    # ロギング設定
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # 統合システムの初期化
    print("1. Initializing integrated RAG system...")
    system = IntegratedRAGSystem()
    
    # システム健康状態の確認
    print("\n2. Checking system health...")
    health = system.get_system_health()
    print(f"System Health Status:")
    for system_name, status in health["systems"].items():
        print(f"  - {system_name}: {'✓' if status.get('connected') or status.get('neo4j_connected') else '✗'}")
    
    # サンプルドキュメントの追加
    print("\n3. Adding sample documents...")
    sample_docs = [
        {
            "content": "imabari3dcadは高度な3D CADアプリケーションです。Neo4jグラフデータベースとChromaベクトルストアを使用して、強力なRAG（Retrieval-Augmented Generation）機能を提供します。",
            "metadata": {"category": "system_overview", "language": "ja", "type": "description"}
        },
        {
            "content": "LangChainインターフェースにより、グラフデータベースとベクトルストアの統合検索が可能になります。高い独立性を持ち、既存のシステムに簡単に統合できます。",
            "metadata": {"category": "features", "language": "ja", "type": "technical"}
        }
    ]
    
    for doc in sample_docs:
        results = system.add_document_to_all_systems(doc["content"], doc["metadata"])
        print(f"  Document added: {results}")
    
    # 各種検索の実演
    print("\n4. Demonstrating different search types...")
    
    search_queries = [
        ("3D CAD機能について", "basic"),
        ("LangChainの統合方法", "advanced"), 
        ("システム全体の機能", "comprehensive")
    ]
    
    for query, search_type in search_queries:
        print(f"\n--- {search_type.upper()} Search: '{query}' ---")
        try:
            results = system.unified_search(query, search_type)
            print(f"Search completed. Results keys: {list(results.get('results', {}).keys())}")
            
            # 結果の詳細表示（簡略化）
            for result_type, result_data in results.get("results", {}).items():
                if isinstance(result_data, dict) and "error" not in result_data:
                    print(f"  {result_type}: ✓ (data available)")
                else:
                    print(f"  {result_type}: ✗ (error or no data)")
        except Exception as e:
            print(f"  Error: {e}")
    
    # 使用方法のガイド
    print("\n5. Integration Guide:")
    print("""
    To integrate this LangChain interface in your code:
    
    # Basic usage:
    from langchain_interface import create_interface
    interface = create_interface()
    results = interface.hybrid_search("your query")
    
    # Advanced usage:
    from langchain_advanced_rag import create_advanced_rag
    rag = create_advanced_rag()
    results = rag.comprehensive_search("your query", "comprehensive")
    
    # Integrated usage:
    from langchain_integration_example import IntegratedRAGSystem
    system = IntegratedRAGSystem()
    results = system.unified_search("your query", "comprehensive")
    """)
    
    # クリーンアップ
    print("\n6. Cleaning up...")
    system.close_all_connections()
    print("✓ Demonstration completed successfully!")


if __name__ == "__main__":
    demonstration()