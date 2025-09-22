"""Hybrid retriever combining multiple search strategies."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .base import BaseRetriever, QueryContext, SearchResult
from .sparse_retriever import SparseVectorRetriever, BM25Retriever
from .fulltext_retriever import WhooshRetriever, ElasticsearchRetriever
from .graph_retriever import Neo4jGraphRetriever, GraphPathRetriever
from .fusion import ReciprocalRankFusion, WeightedSumFusion, BordaCountFusion, AdaptiveFusion


class HybridRetriever(BaseRetriever):
    """Multi-modal hybrid retriever combining dense, sparse, fulltext, and graph search."""
    
    def __init__(self, config: HybridRetrieverConfig):
        self.config = config
        self.retrievers: Dict[str, BaseRetriever] = {}
        self.fusion_engine = self._create_fusion_engine()
        self._initialize_retrievers()
        
    def _create_fusion_engine(self):
        """Create result fusion engine based on configuration."""
        fusion_method = self.config.fusion_method
        
        if fusion_method == "rrf":
            return ReciprocalRankFusion(k=self.config.rrf_k)
        elif fusion_method == "weighted":
            return WeightedSumFusion(self.config.source_weights)
        elif fusion_method == "borda":
            return BordaCountFusion()
        elif fusion_method == "adaptive":
            return AdaptiveFusion()
        else:
            return ReciprocalRankFusion()  # Default
    
    def _initialize_retrievers(self):
        """Initialize all configured retrievers."""
        
        # Dense vector retriever (Chroma)
        if self.config.enable_dense and self.config.chroma_config:
            try:
                self.retrievers["dense"] = ChromaDenseRetriever(
                    collection_name=self.config.chroma_config.collection_name,
                    persist_directory=self.config.chroma_config.persist_directory,
                    embedding_model=self.config.chroma_config.embedding_model
                )
            except Exception as exc:
                import logging
                logging.warning("Failed to initialize dense retriever: %s", exc)
        
        # Sparse vector retrievers
        if self.config.enable_sparse:
            if self.config.tfidf_config:
                try:
                    self.retrievers["sparse_tfidf"] = SparseVectorRetriever(
                        vectorizer_path=self.config.tfidf_config.vectorizer_path,
                        documents_path=self.config.tfidf_config.documents_path,
                        index_name=self.config.tfidf_config.index_name
                    )
                except Exception as exc:
                    import logging
                    logging.warning("Failed to initialize TF-IDF retriever: %s", exc)
            
            if self.config.bm25_config:
                try:
                    self.retrievers["sparse_bm25"] = BM25Retriever(
                        documents_path=self.config.bm25_config.documents_path,
                        k1=self.config.bm25_config.k1,
                        b=self.config.bm25_config.b
                    )
                except Exception as exc:
                    import logging
                    logging.warning("Failed to initialize BM25 retriever: %s", exc)
        
        # Full-text retrievers
        if self.config.enable_fulltext:
            if self.config.whoosh_config:
                try:
                    self.retrievers["fulltext_whoosh"] = WhooshRetriever(
                        index_dir=self.config.whoosh_config.index_dir
                    )
                except Exception as exc:
                    import logging
                    logging.warning("Failed to initialize Whoosh retriever: %s", exc)
            
            if self.config.elasticsearch_config:
                try:
                    self.retrievers["fulltext_elasticsearch"] = ElasticsearchRetriever(
                        host=self.config.elasticsearch_config.host,
                        port=self.config.elasticsearch_config.port,
                        index_name=self.config.elasticsearch_config.index_name
                    )
                except Exception as exc:
                    import logging
                    logging.warning("Failed to initialize Elasticsearch retriever: %s", exc)
        
        # Graph retrievers
        if self.config.enable_graph and self.config.neo4j_config:
            try:
                self.retrievers["graph_neo4j"] = Neo4jGraphRetriever(
                    uri=self.config.neo4j_config.uri,
                    username=self.config.neo4j_config.username,
                    password=self.config.neo4j_config.password,
                    database=self.config.neo4j_config.database
                )
                
                if self.config.enable_graph_paths:
                    self.retrievers["graph_path"] = GraphPathRetriever(
                        uri=self.config.neo4j_config.uri,
                        username=self.config.neo4j_config.username,
                        password=self.config.neo4j_config.password,
                        database=self.config.neo4j_config.database,
                        max_path_length=self.config.max_path_length
                    )
            except Exception as exc:
                import logging
                logging.warning("Failed to initialize graph retrievers: %s", exc)
    
    def search(self, context: QueryContext) -> List[SearchResult]:
        """Execute hybrid search across all configured retrievers."""
        
        # Filter retrievers based on context
        active_retrievers = self._filter_retrievers(context)
        
        # Execute searches in parallel (could be improved with actual threading)
        results_by_source: Dict[str, List[SearchResult]] = {}
        
        for name, retriever in active_retrievers.items():
            try:
                # Create per-retriever context
                retriever_context = QueryContext(
                    query=context.query,
                    filters=context.filters,
                    top_k=min(context.top_k * 2, 20),  # Get more results for fusion
                    search_types=context.search_types,
                    fusion_method=context.fusion_method
                )
                
                results = retriever.search(retriever_context)
                if results:
                    results_by_source[name] = results
                    
            except Exception as exc:
                import logging
                logging.warning("Search failed for %s: %s", name, exc)
        
        # Fuse results
        if results_by_source:
            return self.fusion_engine.fuse_results(results_by_source, context)
        else:
            return []
    
    def _filter_retrievers(self, context: QueryContext) -> Dict[str, BaseRetriever]:
        """Filter retrievers based on search context."""
        if context.search_types:
            # Use only specified search types
            filtered = {}
            for search_type in context.search_types:
                if search_type == "dense" and "dense" in self.retrievers:
                    filtered["dense"] = self.retrievers["dense"]
                elif search_type == "sparse":
                    for name in ["sparse_tfidf", "sparse_bm25"]:
                        if name in self.retrievers:
                            filtered[name] = self.retrievers[name]
                elif search_type == "fulltext":
                    for name in ["fulltext_whoosh", "fulltext_elasticsearch"]:
                        if name in self.retrievers:
                            filtered[name] = self.retrievers[name]
                elif search_type == "graph":
                    for name in ["graph_neo4j", "graph_path"]:
                        if name in self.retrievers:
                            filtered[name] = self.retrievers[name]
            return filtered
        else:
            # Use all available retrievers
            return self.retrievers.copy()
    
    def get_name(self) -> str:
        return "hybrid_multi_modal"
    
    def get_retriever_status(self) -> Dict[str, bool]:
        """Get status of all retrievers."""
        return {name: True for name in self.retrievers.keys()}


class ChromaDenseRetriever(BaseRetriever):
    """Dense vector retriever using Chroma."""
    
    def __init__(
        self,
        collection_name: str,
        persist_directory: Optional[str] = None,
        embedding_model: Optional[str] = None
    ):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self._client = None
        self._collection = None
        
    def _get_collection(self):
        """Get or create Chroma collection."""
        if self._collection is None:
            try:
                import chromadb
                from chromadb.config import Settings
                
                if self.persist_directory:
                    settings = Settings(
                        persist_directory=self.persist_directory,
                        is_persistent=True
                    )
                    self._client = chromadb.Client(settings)
                else:
                    self._client = chromadb.Client()
                    
                self._collection = self._client.get_collection(self.collection_name)
                
            except ImportError as exc:
                raise ImportError("ChromaDB package required. Install with: pip install chromadb") from exc
        
        return self._collection
    
    def search(self, context: QueryContext) -> List[SearchResult]:
        """Execute dense vector search using Chroma."""
        collection = self._get_collection()
        
        try:
            # Query collection
            results = collection.query(
                query_texts=[context.query],
                n_results=context.top_k,
                where=context.filters
            )
            
            search_results = []
            
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    content = results["documents"][0][i] if results["documents"] else ""
                    distance = results["distances"][0][i] if results["distances"] else 0.0
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    
                    # Convert distance to similarity score (assuming cosine distance)
                    score = max(0.0, 1.0 - distance)
                    
                    result = SearchResult(
                        id=doc_id,
                        content=content,
                        score=score,
                        source="dense_chroma",
                        metadata={
                            "distance": distance,
                            "embedding_model": self.embedding_model,
                            **metadata
                        }
                    )
                    search_results.append(result)
            
            return search_results
            
        except Exception as exc:
            import logging
            logging.warning("Chroma search failed: %s", exc)
            return []
    
    def get_name(self) -> str:
        return f"dense_chroma_{self.collection_name}"


# Configuration classes

@dataclass
class ChromaConfig:
    collection_name: str
    persist_directory: Optional[str] = None
    embedding_model: Optional[str] = None

@dataclass 
class TFIDFConfig:
    vectorizer_path: Path
    documents_path: Path
    index_name: str = "tfidf"

@dataclass
class BM25Config:
    documents_path: Path
    k1: float = 1.2
    b: float = 0.75

@dataclass
class WhooshConfig:
    index_dir: Path

@dataclass
class ElasticsearchConfig:
    host: str = "localhost"
    port: int = 9200
    index_name: str = "help_documents"

@dataclass
class Neo4jConfig:
    uri: str
    username: str
    password: str
    database: Optional[str] = None

@dataclass
class HybridRetrieverConfig:
    # Enable/disable search types
    enable_dense: bool = True
    enable_sparse: bool = True
    enable_fulltext: bool = True
    enable_graph: bool = True
    enable_graph_paths: bool = False
    
    # Fusion configuration
    fusion_method: str = "adaptive"  # "rrf", "weighted", "borda", "adaptive"
    rrf_k: int = 60
    source_weights: Optional[Dict[str, float]] = None
    
    # Graph configuration
    max_path_length: int = 3
    
    # Retriever configurations
    chroma_config: Optional[ChromaConfig] = None
    tfidf_config: Optional[TFIDFConfig] = None
    bm25_config: Optional[BM25Config] = None
    whoosh_config: Optional[WhooshConfig] = None
    elasticsearch_config: Optional[ElasticsearchConfig] = None
    neo4j_config: Optional[Neo4jConfig] = None
