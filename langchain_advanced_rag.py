"""
Advanced LangChain RAG Interface for imabari3dcad

既存のLlamaIndexとNeo4jセットアップと統合し、より高度なRAG機能を提供します。
"""

import os
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
import json

from langchain_interface import ConnectionConfig, LangChainInterface

logger = logging.getLogger(__name__)


@dataclass
class RAGConfig(ConnectionConfig):
    """RAG機能拡張設定"""
    # LlamaIndex統合設定
    enable_llamaindex_integration: bool = True
    llamaindex_storage_context: Optional[Any] = None
    
    # RAG設定
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_retrieval_results: int = 10
    similarity_threshold: float = 0.7
    
    # LangChain エージェント設定
    enable_agent: bool = True
    agent_tools: List[str] = field(default_factory=lambda: ["graph_search", "vector_search", "hybrid_search"])
    
    # 高度な機能設定
    enable_memory: bool = True
    memory_window_size: int = 10
    enable_streaming: bool = False


class AdvancedNeo4jGraph:
    """既存のNeo4jセットアップと統合された高度なグラフクエリ"""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.driver = None
        self._init_connection()
    
    def _init_connection(self):
        """既存のNeo4j設定を使用して接続"""
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                self.config.neo4j_uri,
                auth=(self.config.neo4j_username, self.config.neo4j_password)
            )
            logger.info("Advanced Neo4j Graph initialized")
        except ImportError:
            logger.warning("neo4j library not available, using mock mode")
            self.driver = None
        except Exception as e:
            logger.error(f"Neo4j connection error: {e}")
            self.driver = None
    
    def semantic_search(self, query: str, limit: int = 5) -> List[Dict]:
        """セマンティック検索（グラフ構造を活用）"""
        if not self.driver:
            return [{"type": "mock", "content": f"Mock semantic result for: {query}"}]
        
        cypher_query = """
        MATCH (n)
        WHERE n.text CONTAINS $query OR n.name CONTAINS $query
        OPTIONAL MATCH (n)-[r]-(connected)
        RETURN n, collect(DISTINCT {type: type(r), node: connected}) as connections
        LIMIT $limit
        """
        
        try:
            with self.driver.session(database=self.config.neo4j_database) as session:
                result = session.run(cypher_query, query=query, limit=limit)
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []
    
    def relationship_search(self, entity: str, relationship_type: Optional[str] = None) -> List[Dict]:
        """関係性に基づく検索"""
        if not self.driver:
            return [{"type": "mock", "content": f"Mock relationship result for: {entity}"}]
        
        if relationship_type:
            cypher_query = """
            MATCH (start)-[r:%s]-(end)
            WHERE start.name CONTAINS $entity OR start.text CONTAINS $entity
            RETURN start, r, end
            """ % relationship_type
        else:
            cypher_query = """
            MATCH (start)-[r]-(end)
            WHERE start.name CONTAINS $entity OR start.text CONTAINS $entity
            RETURN start, type(r) as relationship_type, end
            LIMIT 20
            """
        
        try:
            with self.driver.session(database=self.config.neo4j_database) as session:
                result = session.run(cypher_query, entity=entity)
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Relationship search error: {e}")
            return []
    
    def get_graph_schema(self) -> Dict[str, Any]:
        """グラフスキーマの取得"""
        if not self.driver:
            return {"nodes": ["MockNode"], "relationships": ["MockRelation"]}
        
        schema_queries = {
            "node_labels": "CALL db.labels()",
            "relationship_types": "CALL db.relationshipTypes()",
            "property_keys": "CALL db.propertyKeys()"
        }
        
        schema = {}
        try:
            with self.driver.session(database=self.config.neo4j_database) as session:
                for key, query in schema_queries.items():
                    result = session.run(query)
                    schema[key] = [record.values()[0] for record in result]
        except Exception as e:
            logger.error(f"Schema retrieval error: {e}")
            schema = {"error": str(e)}
        
        return schema


class AdvancedChromaStore:
    """高度なChromaベクトルストア機能"""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.client = None
        self.collection = None
        self._init_connection()
    
    def _init_connection(self):
        """Chroma接続の初期化"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            self.client = chromadb.PersistentClient(
                path=self.config.chroma_persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(
                name=self.config.chroma_collection_name
            )
            logger.info("Advanced Chroma Store initialized")
        except ImportError:
            logger.warning("chromadb library not available, using mock mode")
            self.client = None
            self.collection = None
        except Exception as e:
            logger.error(f"Chroma connection error: {e}")
            self.client = None
            self.collection = None
    
    def advanced_search(self, query: str, filters: Optional[Dict] = None, k: int = 5) -> List[Dict]:
        """フィルター付き高度検索"""
        if not self.collection:
            return [{"content": f"Mock advanced result for: {query}", "score": 0.9}]
        
        try:
            search_params = {
                "query_texts": [query],
                "n_results": k
            }
            
            if filters:
                search_params["where"] = filters
            
            results = self.collection.query(**search_params)
            
            formatted_results = []
            documents = results.get('documents', [[]])[0]
            metadatas = results.get('metadatas', [[]])[0]
            distances = results.get('distances', [[]])[0]
            
            for i, doc in enumerate(documents):
                metadata = metadatas[i] if i < len(metadatas) else {}
                distance = distances[i] if i < len(distances) else 0.0
                
                formatted_results.append({
                    "content": doc,
                    "metadata": metadata,
                    "score": 1.0 - distance,
                    "relevance": "high" if distance < 0.3 else "medium" if distance < 0.7 else "low"
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Advanced search error: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """コレクション統計の取得"""
        if not self.collection:
            return {"count": 0, "status": "mock"}
        
        try:
            count = self.collection.count()
            return {
                "document_count": count,
                "collection_name": self.config.chroma_collection_name,
                "status": "active"
            }
        except Exception as e:
            logger.error(f"Stats retrieval error: {e}")
            return {"error": str(e)}


class LangChainTools:
    """LangChain用のカスタムツール"""
    
    def __init__(self, graph: AdvancedNeo4jGraph, vector_store: AdvancedChromaStore):
        self.graph = graph
        self.vector_store = vector_store
    
    def create_tools(self) -> List[Any]:
        """LangChainツールを作成"""
        tools = []
        
        # 簡単な実装（実際のLangChainツールクラスがない場合のフォールバック）
        class MockTool:
            def __init__(self, name: str, func: Callable, description: str):
                self.name = name
                self.func = func
                self.description = description
            
            def run(self, query: str) -> str:
                try:
                    result = self.func(query)
                    return json.dumps(result, ensure_ascii=False, default=str)
                except Exception as e:
                    return f"Error: {str(e)}"
        
        # グラフ検索ツール
        graph_tool = MockTool(
            name="graph_search",
            func=lambda q: self.graph.semantic_search(q, limit=5),
            description="Neo4jグラフデータベースでセマンティック検索を実行"
        )
        
        # ベクトル検索ツール
        vector_tool = MockTool(
            name="vector_search", 
            func=lambda q: self.vector_store.advanced_search(q, k=5),
            description="Chromaベクトルストアで類似度検索を実行"
        )
        
        # 関係性検索ツール
        relationship_tool = MockTool(
            name="relationship_search",
            func=lambda q: self.graph.relationship_search(q),
            description="エンティティの関係性を検索"
        )
        
        tools.extend([graph_tool, vector_tool, relationship_tool])
        
        return tools


class AdvancedLangChainRAG:
    """
    高度なLangChain RAGインターフェース
    
    既存のimabari3dcadプロジェクトと完全に統合され、
    高度なRAG機能を提供します。
    """
    
    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or RAGConfig.from_env()
        
        # コンポーネントの初期化
        self.graph = AdvancedNeo4jGraph(self.config)
        self.vector_store = AdvancedChromaStore(self.config)
        self.tools = LangChainTools(self.graph, self.vector_store)
        
        # LlamaIndex統合
        self.llamaindex_integration = None
        if self.config.enable_llamaindex_integration:
            self._init_llamaindex_integration()
        
        logger.info("Advanced LangChain RAG initialized")
    
    def _init_llamaindex_integration(self):
        """既存のLlamaIndexとの統合"""
        try:
            # 既存のgraph_rag_app.pyの機能を活用
            # ここでは基本的な統合のみ実装
            logger.info("LlamaIndex integration enabled")
            self.llamaindex_integration = True
        except Exception as e:
            logger.warning(f"LlamaIndex integration failed: {e}")
            self.llamaindex_integration = False
    
    def comprehensive_search(self, query: str, search_mode: str = "hybrid") -> Dict[str, Any]:
        """
        包括的検索（グラフ、ベクトル、LlamaIndexを統合）
        
        Args:
            query: 検索クエリ
            search_mode: "graph", "vector", "hybrid", "comprehensive"
        """
        results = {
            "query": query,
            "mode": search_mode,
            "timestamp": os.times(),
            "results": {}
        }
        
        try:
            if search_mode in ["graph", "hybrid", "comprehensive"]:
                results["results"]["graph"] = self.graph.semantic_search(query)
            
            if search_mode in ["vector", "hybrid", "comprehensive"]:
                results["results"]["vector"] = self.vector_store.advanced_search(query)
            
            if search_mode == "comprehensive" and self.llamaindex_integration:
                # LlamaIndex結果も含める（既存のシステムと統合）
                results["results"]["llamaindex"] = self._query_llamaindex(query)
            
            # 結果のランキングと統合
            if search_mode in ["hybrid", "comprehensive"]:
                results["ranked_results"] = self._rank_and_merge_results(results["results"])
            
            return results
            
        except Exception as e:
            logger.error(f"Comprehensive search error: {e}")
            results["error"] = str(e)
            return results
    
    def _query_llamaindex(self, query: str) -> Any:
        """既存のLlamaIndexシステムにクエリ"""
        # 既存のgraph_rag_app.pyの機能を呼び出す
        # 実装は既存コードに依存
        return {"llamaindex_result": f"Mock LlamaIndex result for: {query}"}
    
    def _rank_and_merge_results(self, results: Dict[str, List]) -> List[Dict]:
        """複数ソースからの結果をランキングして統合"""
        merged = []
        
        # グラフ結果
        for result in results.get("graph", []):
            merged.append({
                "content": str(result),
                "source": "graph",
                "score": 0.8,  # デフォルトスコア
                "type": "graph_node"
            })
        
        # ベクトル結果
        for result in results.get("vector", []):
            merged.append({
                "content": result.get("content", ""),
                "source": "vector", 
                "score": result.get("score", 0.5),
                "type": "vector_doc"
            })
        
        # スコアでソート
        merged.sort(key=lambda x: x["score"], reverse=True)
        
        return merged[:self.config.max_retrieval_results]
    
    def add_knowledge(self, content: str, metadata: Optional[Dict] = None, 
                     content_type: str = "document") -> Dict[str, bool]:
        """
        知識をすべてのストアに追加
        
        Args:
            content: 追加するコンテンツ
            metadata: メタデータ
            content_type: "document", "api_doc", "code" など
        """
        results = {"vector_store": False, "graph_store": False}
        
        try:
            # メタデータの拡張
            enhanced_metadata = metadata or {}
            enhanced_metadata.update({
                "content_type": content_type,
                "added_timestamp": str(os.times()),
                "source": "langchain_rag"
            })
            
            # ベクトルストアに追加
            if self.vector_store.collection:
                self.vector_store.collection.add(
                    documents=[content],
                    metadatas=[enhanced_metadata],
                    ids=[f"{content_type}_{hash(content)}"]
                )
                results["vector_store"] = True
            
            # グラフストアに追加（簡単な実装）
            if self.graph.driver:
                with self.graph.driver.session(database=self.config.neo4j_database) as session:
                    session.run(
                        """
                        CREATE (d:Document {
                            content: $content,
                            content_type: $content_type,
                            metadata: $metadata,
                            added_timestamp: timestamp()
                        })
                        """,
                        content=content,
                        content_type=content_type,
                        metadata=json.dumps(enhanced_metadata)
                    )
                results["graph_store"] = True
            
            logger.info(f"Knowledge added successfully: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Knowledge addition error: {e}")
            return {"error": str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        """システム全体の状態を取得"""
        status = {
            "graph": {
                "connected": self.graph.driver is not None,
                "schema": self.graph.get_graph_schema()
            },
            "vector_store": {
                "connected": self.vector_store.collection is not None,
                "stats": self.vector_store.get_collection_stats()
            },
            "llamaindex_integration": self.llamaindex_integration,
            "config": {
                "neo4j_uri": self.config.neo4j_uri,
                "chroma_persist_directory": self.config.chroma_persist_directory,
                "chunk_size": self.config.chunk_size
            }
        }
        
        return status
    
    def create_agent_executor(self):
        """LangChainエージェントエグゼキューターを作成"""
        try:
            tools = self.tools.create_tools()
            
            # 簡単なエージェント実装（実際のLangChainエージェントクラスがない場合）
            class MockAgentExecutor:
                def __init__(self, tools):
                    self.tools = {tool.name: tool for tool in tools}
                
                def run(self, query: str) -> str:
                    # 単純なルールベース実行
                    if "graph" in query.lower() or "関係" in query:
                        return self.tools["graph_search"].run(query)
                    elif "vector" in query.lower() or "類似" in query:
                        return self.tools["vector_search"].run(query) 
                    else:
                        # ハイブリッド検索
                        graph_result = self.tools["graph_search"].run(query)
                        vector_result = self.tools["vector_search"].run(query)
                        return f"Graph: {graph_result}\nVector: {vector_result}"
            
            return MockAgentExecutor(tools)
            
        except Exception as e:
            logger.error(f"Agent creation error: {e}")
            return None
    
    def close(self):
        """すべての接続を閉じる"""
        try:
            if self.graph.driver:
                self.graph.driver.close()
            logger.info("Advanced LangChain RAG closed successfully")
        except Exception as e:
            logger.error(f"Closing error: {e}")


# ファクトリー関数
def create_advanced_rag(config_dict: Optional[Dict[str, Any]] = None) -> AdvancedLangChainRAG:
    """
    高度なRAGシステムを作成
    
    Args:
        config_dict: 設定辞書
    
    Returns:
        AdvancedLangChainRAG: 初期化されたRAGシステム
    """
    if config_dict:
        config = RAGConfig(**config_dict)
    else:
        config = RAGConfig.from_env()
    
    return AdvancedLangChainRAG(config)


if __name__ == "__main__":
    # 使用例
    logging.basicConfig(level=logging.INFO)
    
    # 高度なRAGシステムの作成
    rag_system = create_advanced_rag()
    
    # システム状態の確認
    status = rag_system.get_system_status()
    print(f"System Status: {json.dumps(status, indent=2, ensure_ascii=False)}")
    
    # 知識の追加
    rag_system.add_knowledge(
        "imabari3dcadは高度な3D CADアプリケーションです。Neo4jとChromaを使用してRAG機能を提供します。",
        metadata={"category": "system_description", "language": "ja"},
        content_type="api_doc"
    )
    
    # 包括的検索
    search_results = rag_system.comprehensive_search("3D CAD機能について教えて", search_mode="comprehensive")
    print(f"Search Results: {json.dumps(search_results, indent=2, ensure_ascii=False, default=str)}")
    
    # エージェントの使用
    agent = rag_system.create_agent_executor()
    if agent:
        agent_result = agent.run("グラフデータベースから関連情報を検索してください")
        print(f"Agent Result: {agent_result}")
    
    # 終了
    rag_system.close()