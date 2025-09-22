"""LangChain integration for help preprocessor retrieval."""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from pathlib import Path

from .base import QueryContext
from .hybrid_retriever import HybridRetriever, HybridRetrieverConfig


class HelpLangChainRetriever:
    """LangChain-compatible retriever wrapper."""
    
    def __init__(self, hybrid_retriever: HybridRetriever):
        self.hybrid_retriever = hybrid_retriever
        
    def get_relevant_documents(self, query: str, **kwargs) -> List[Any]:
        """LangChain-compatible retrieval method."""
        try:
            from langchain.schema import Document
        except ImportError as exc:
            raise ImportError("LangChain package required. Install with: pip install langchain") from exc
            
        # Convert to our query context
        context = QueryContext(
            query=query,
            top_k=kwargs.get("k", 5),
            filters=kwargs.get("filters"),
            search_types=kwargs.get("search_types")
        )
        
        # Execute search
        results = self.hybrid_retriever.search(context)
        
        # Convert to LangChain documents
        documents = []
        for result in results:
            doc = Document(
                page_content=result.content,
                metadata={
                    "id": result.id,
                    "score": result.score,
                    "source": result.source,
                    **result.metadata
                }
            )
            documents.append(doc)
            
        return documents
    
    async def aget_relevant_documents(self, query: str, **kwargs) -> List[Any]:
        """Async version of get_relevant_documents."""
        # For now, just call sync version
        # Could be improved with actual async implementation
        return self.get_relevant_documents(query, **kwargs)


class HelpRAGChain:
    """RAG (Retrieval-Augmented Generation) chain for help system."""
    
    def __init__(
        self,
        hybrid_retriever: HybridRetriever,
        llm_model: str = "gpt-3.5-turbo",
        temperature: float = 0.1,
        max_tokens: int = 500
    ):
        self.hybrid_retriever = hybrid_retriever
        self.llm_model = llm_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._chain = None
        
    def _build_chain(self):
        """Build LangChain RAG chain."""
        try:
            from langchain.chains import RetrievalQA
            from langchain.chat_models import ChatOpenAI
            from langchain.prompts import PromptTemplate
        except ImportError as exc:
            raise ImportError("LangChain package required. Install with: pip install langchain openai") from exc
            
        # Create LLM
        llm = ChatOpenAI(
            model_name=self.llm_model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        # Create retriever
        retriever = HelpLangChainRetriever(self.hybrid_retriever)
        
        # Custom prompt for help system
        prompt_template = """以下のヘルプドキュメントの内容を参考にして、質問に回答してください。

関連ドキュメント:
{context}

質問: {question}

回答: 関連するヘルプドキュメントの情報に基づいて、具体的で実用的な回答を提供してください。
情報が不十分な場合は、その旨を明記してください。"""

        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Build chain
        self._chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True
        )
        
        return self._chain
    
    def query(self, question: str, **kwargs) -> Dict[str, Any]:
        """Execute RAG query."""
        if self._chain is None:
            self._chain = self._build_chain()
            
        result = self._chain({"query": question})
        
        return {
            "answer": result["result"],
            "source_documents": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in result["source_documents"]
            ],
            "retrieval_method": "langchain_rag"
        }
    
    async def aquery(self, question: str, **kwargs) -> Dict[str, Any]:
        """Async version of query."""
        # For now, just call sync version
        return self.query(question, **kwargs)


class HelpConversationalChain:
    """Conversational RAG chain with memory."""
    
    def __init__(
        self,
        hybrid_retriever: HybridRetriever,
        llm_model: str = "gpt-3.5-turbo",
        memory_key: str = "chat_history"
    ):
        self.hybrid_retriever = hybrid_retriever
        self.llm_model = llm_model
        self.memory_key = memory_key
        self._chain = None
        self._memory = None
        
    def _build_chain(self):
        """Build conversational RAG chain."""
        try:
            from langchain.chains import ConversationalRetrievalChain
            from langchain.chat_models import ChatOpenAI
            from langchain.memory import ConversationBufferWindowMemory
            from langchain.prompts import PromptTemplate
        except ImportError as exc:
            raise ImportError("LangChain package required. Install with: pip install langchain openai") from exc
            
        # Create LLM
        llm = ChatOpenAI(
            model_name=self.llm_model,
            temperature=0.1
        )
        
        # Create memory
        self._memory = ConversationBufferWindowMemory(
            memory_key=self.memory_key,
            return_messages=True,
            k=5  # Keep last 5 exchanges
        )
        
        # Create retriever
        retriever = HelpLangChainRetriever(self.hybrid_retriever)
        
        # Build conversational chain
        self._chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=self._memory,
            return_source_documents=True
        )
        
        return self._chain
    
    def chat(self, message: str) -> Dict[str, Any]:
        """Execute conversational query."""
        if self._chain is None:
            self._chain = self._build_chain()
            
        result = self._chain({"question": message})
        
        return {
            "answer": result["answer"],
            "source_documents": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in result["source_documents"]
            ],
            "chat_history": self._memory.chat_memory.messages if self._memory else [],
            "retrieval_method": "langchain_conversational"
        }
    
    def clear_memory(self):
        """Clear conversation memory."""
        if self._memory:
            self._memory.clear()


def create_help_langchain_system(
    config_path: Optional[Path] = None,
    **override_config
) -> Dict[str, Any]:
    """Factory function to create complete LangChain help system."""
    
    # Load configuration
    if config_path and config_path.exists():
        import json
        with open(config_path) as f:
            config_dict = json.load(f)
    else:
        config_dict = {}
    
    # Apply overrides
    config_dict.update(override_config)
    
    # Create hybrid retriever config
    from .hybrid_retriever import (
        ChromaConfig, TFIDFConfig, BM25Config, WhooshConfig, 
        Neo4jConfig
    )
    
    retriever_config = HybridRetrieverConfig(
        enable_dense=config_dict.get("enable_dense", True),
        enable_sparse=config_dict.get("enable_sparse", True),
        enable_fulltext=config_dict.get("enable_fulltext", True),
        enable_graph=config_dict.get("enable_graph", True),
        fusion_method=config_dict.get("fusion_method", "adaptive")
    )
    
    # Configure retrievers based on available data
    data_dir = Path(config_dict.get("data_dir", "data"))
    
    # Chroma config
    if retriever_config.enable_dense:
        retriever_config.chroma_config = ChromaConfig(
            collection_name=config_dict.get("chroma_collection", "evoship-help"),
            persist_directory=config_dict.get("chroma_persist_dir"),
            embedding_model=config_dict.get("embedding_model", "text-embedding-3-small")
        )
    
    # TF-IDF config
    if retriever_config.enable_sparse:
        tfidf_dir = data_dir / "sparse_index"
        if (tfidf_dir / "tfidf_vectorizer.joblib").exists():
            retriever_config.tfidf_config = TFIDFConfig(
                vectorizer_path=tfidf_dir / "tfidf_vectorizer.joblib",
                documents_path=tfidf_dir / "documents.pkl"
            )
        
        # BM25 uses same documents
        if (tfidf_dir / "documents.pkl").exists():
            retriever_config.bm25_config = BM25Config(
                documents_path=tfidf_dir / "documents.pkl"
            )
    
    # Whoosh config
    if retriever_config.enable_fulltext:
        whoosh_dir = data_dir / "whoosh_index"
        if whoosh_dir.exists():
            retriever_config.whoosh_config = WhooshConfig(index_dir=whoosh_dir)
    
    # Neo4j config
    if retriever_config.enable_graph:
        retriever_config.neo4j_config = Neo4jConfig(
            uri=config_dict.get("neo4j_uri", "bolt://localhost:7687"),
            username=config_dict.get("neo4j_username", "neo4j"),
            password=config_dict.get("neo4j_password", "password"),
            database=config_dict.get("neo4j_database")
        )
    
    # Create hybrid retriever
    hybrid_retriever = HybridRetriever(retriever_config)
    
    # Create LangChain components
    rag_chain = HelpRAGChain(
        hybrid_retriever=hybrid_retriever,
        llm_model=config_dict.get("llm_model", "gpt-3.5-turbo")
    )
    
    conversational_chain = HelpConversationalChain(
        hybrid_retriever=hybrid_retriever,
        llm_model=config_dict.get("llm_model", "gpt-3.5-turbo")
    )
    
    return {
        "hybrid_retriever": hybrid_retriever,
        "rag_chain": rag_chain,
        "conversational_chain": conversational_chain,
        "langchain_retriever": HelpLangChainRetriever(hybrid_retriever),
        "config": retriever_config
    }
