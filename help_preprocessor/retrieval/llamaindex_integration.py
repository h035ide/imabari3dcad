"""LlamaIndex integration for help preprocessor retrieval."""

from __future__ import annotations

from typing import List, Optional, Dict, Any, Sequence
from pathlib import Path

from .base import QueryContext, SearchResult
from .hybrid_retriever import HybridRetriever, HybridRetrieverConfig


class HelpLlamaIndexRetriever:
    """LlamaIndex-compatible retriever wrapper."""
    
    def __init__(self, hybrid_retriever: HybridRetriever):
        self.hybrid_retriever = hybrid_retriever
        
    def retrieve(self, query_str: str, **kwargs) -> List["NodeWithScore"]:
        """LlamaIndex-compatible retrieval method."""
        try:
            from llama_index.schema import NodeWithScore, TextNode
        except ImportError as exc:
            raise ImportError("LlamaIndex package required. Install with: pip install llama-index") from exc
            
        # Convert to our query context
        context = QueryContext(
            query=query_str,
            top_k=kwargs.get("similarity_top_k", 5),
            filters=kwargs.get("filters"),
            search_types=kwargs.get("search_types")
        )
        
        # Execute search
        results = self.hybrid_retriever.search(context)
        
        # Convert to LlamaIndex nodes
        nodes_with_scores = []
        for result in results:
            # Create TextNode
            node = TextNode(
                text=result.content,
                id_=result.id,
                metadata={
                    "source": result.source,
                    **result.metadata
                }
            )
            
            # Wrap in NodeWithScore
            node_with_score = NodeWithScore(
                node=node,
                score=result.score
            )
            nodes_with_scores.append(node_with_score)
            
        return nodes_with_scores


class HelpQueryEngine:
    """LlamaIndex QueryEngine for help system."""
    
    def __init__(
        self,
        hybrid_retriever: HybridRetriever,
        llm_model: str = "gpt-3.5-turbo",
        similarity_top_k: int = 5,
        response_mode: str = "compact"
    ):
        self.hybrid_retriever = hybrid_retriever
        self.llm_model = llm_model
        self.similarity_top_k = similarity_top_k
        self.response_mode = response_mode
        self._query_engine = None
        
    def _build_query_engine(self):
        """Build LlamaIndex query engine."""
        try:
            from llama_index import QueryEngine, ServiceContext
            from llama_index.llms import OpenAI
            from llama_index.response_synthesizers import get_response_synthesizer
            from llama_index.query_engine import RetrieverQueryEngine
            from llama_index.prompts import PromptTemplate
        except ImportError as exc:
            raise ImportError("LlamaIndex package required. Install with: pip install llama-index openai") from exc
            
        # Create LLM
        llm = OpenAI(model=self.llm_model, temperature=0.1)
        
        # Create service context
        service_context = ServiceContext.from_defaults(llm=llm)
        
        # Create retriever
        retriever = HelpLlamaIndexRetriever(self.hybrid_retriever)
        
        # Create response synthesizer with custom prompt
        help_qa_prompt = PromptTemplate(
            "以下のヘルプドキュメントの情報を使用して質問に回答してください。\n"
            "情報が不十分な場合は、その旨を明記してください。\n\n"
            "コンテキスト情報:\n"
            "---------------------\n"
            "{context_str}\n"
            "---------------------\n"
            "質問: {query_str}\n"
            "回答: "
        )
        
        response_synthesizer = get_response_synthesizer(
            service_context=service_context,
            response_mode=self.response_mode,
            text_qa_template=help_qa_prompt
        )
        
        # Build query engine
        self._query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer
        )
        
        return self._query_engine
    
    def query(self, query_str: str, **kwargs) -> Dict[str, Any]:
        """Execute query using LlamaIndex."""
        if self._query_engine is None:
            self._query_engine = self._build_query_engine()
            
        # Execute query
        response = self._query_engine.query(query_str)
        
        # Extract source information
        source_nodes = []
        if hasattr(response, 'source_nodes'):
            for node_with_score in response.source_nodes:
                source_nodes.append({
                    "content": node_with_score.node.text,
                    "score": node_with_score.score,
                    "metadata": node_with_score.node.metadata
                })
        
        return {
            "answer": str(response),
            "source_nodes": source_nodes,
            "retrieval_method": "llamaindex_query_engine"
        }
    
    async def aquery(self, query_str: str, **kwargs) -> Dict[str, Any]:
        """Async version of query."""
        if self._query_engine is None:
            self._query_engine = self._build_query_engine()
            
        # Execute async query
        response = await self._query_engine.aquery(query_str)
        
        # Extract source information
        source_nodes = []
        if hasattr(response, 'source_nodes'):
            for node_with_score in response.source_nodes:
                source_nodes.append({
                    "content": node_with_score.node.text,
                    "score": node_with_score.score,
                    "metadata": node_with_score.node.metadata
                })
        
        return {
            "answer": str(response),
            "source_nodes": source_nodes,
            "retrieval_method": "llamaindex_query_engine_async"
        }


class HelpChatEngine:
    """LlamaIndex ChatEngine for conversational help."""
    
    def __init__(
        self,
        hybrid_retriever: HybridRetriever,
        llm_model: str = "gpt-3.5-turbo",
        similarity_top_k: int = 5,
        chat_mode: str = "context"
    ):
        self.hybrid_retriever = hybrid_retriever
        self.llm_model = llm_model
        self.similarity_top_k = similarity_top_k
        self.chat_mode = chat_mode
        self._chat_engine = None
        
    def _build_chat_engine(self):
        """Build LlamaIndex chat engine."""
        try:
            from llama_index import ServiceContext
            from llama_index.llms import OpenAI
            from llama_index.chat_engine import ContextChatEngine
            from llama_index.memory import ChatMemoryBuffer
        except ImportError as exc:
            raise ImportError("LlamaIndex package required. Install with: pip install llama-index openai") from exc
            
        # Create LLM
        llm = OpenAI(model=self.llm_model, temperature=0.1)
        
        # Create service context
        service_context = ServiceContext.from_defaults(llm=llm)
        
        # Create retriever
        retriever = HelpLlamaIndexRetriever(self.hybrid_retriever)
        
        # Create chat memory
        memory = ChatMemoryBuffer.from_defaults(token_limit=3000)
        
        # Build chat engine
        self._chat_engine = ContextChatEngine.from_defaults(
            retriever=retriever,
            service_context=service_context,
            memory=memory,
            system_prompt=(
                "あなたはEVOSHIPヘルプシステムのアシスタントです。"
                "提供されたヘルプドキュメントの情報を使用して、"
                "ユーザーの質問に正確で実用的な回答を提供してください。"
                "情報が不十分な場合は、その旨を明記してください。"
            )
        )
        
        return self._chat_engine
    
    def chat(self, message: str, **kwargs) -> Dict[str, Any]:
        """Execute chat using LlamaIndex."""
        if self._chat_engine is None:
            self._chat_engine = self._build_chat_engine()
            
        # Execute chat
        response = self._chat_engine.chat(message)
        
        # Extract source information
        source_nodes = []
        if hasattr(response, 'source_nodes'):
            for node_with_score in response.source_nodes:
                source_nodes.append({
                    "content": node_with_score.node.text,
                    "score": node_with_score.score,
                    "metadata": node_with_score.node.metadata
                })
        
        return {
            "answer": str(response),
            "source_nodes": source_nodes,
            "retrieval_method": "llamaindex_chat_engine"
        }
    
    async def achat(self, message: str, **kwargs) -> Dict[str, Any]:
        """Async version of chat."""
        if self._chat_engine is None:
            self._chat_engine = self._build_chat_engine()
            
        # Execute async chat
        response = await self._chat_engine.achat(message)
        
        # Extract source information
        source_nodes = []
        if hasattr(response, 'source_nodes'):
            for node_with_score in response.source_nodes:
                source_nodes.append({
                    "content": node_with_score.node.text,
                    "score": node_with_score.score,
                    "metadata": node_with_score.node.metadata
                })
        
        return {
            "answer": str(response),
            "source_nodes": source_nodes,
            "retrieval_method": "llamaindex_chat_engine_async"
        }
    
    def reset(self):
        """Reset chat memory."""
        if self._chat_engine and hasattr(self._chat_engine, 'reset'):
            self._chat_engine.reset()


class HelpIndexBuilder:
    """Build LlamaIndex index from help documents."""
    
    def __init__(self, documents_path: Path):
        self.documents_path = documents_path
        
    def build_vector_store_index(self, persist_dir: Optional[Path] = None):
        """Build vector store index from documents."""
        try:
            from llama_index import VectorStoreIndex, Document, ServiceContext, StorageContext
            from llama_index.vector_stores import ChromaVectorStore
            import chromadb
        except ImportError as exc:
            raise ImportError("LlamaIndex and ChromaDB packages required") from exc
            
        # Load documents
        import pickle
        with open(self.documents_path, 'rb') as f:
            raw_documents = pickle.load(f)
            
        # Convert to LlamaIndex documents
        documents = []
        for doc in raw_documents:
            llama_doc = Document(
                text=doc.get('content', ''),
                doc_id=doc.get('id'),
                metadata=doc.get('metadata', {})
            )
            documents.append(llama_doc)
            
        # Create service context
        service_context = ServiceContext.from_defaults()
        
        # Create vector store
        if persist_dir:
            persist_dir.mkdir(parents=True, exist_ok=True)
            chroma_client = chromadb.PersistentClient(path=str(persist_dir))
            chroma_collection = chroma_client.get_or_create_collection("help_documents")
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
        else:
            storage_context = StorageContext.from_defaults()
            
        # Build index
        index = VectorStoreIndex.from_documents(
            documents,
            service_context=service_context,
            storage_context=storage_context
        )
        
        # Persist if directory provided
        if persist_dir:
            index.storage_context.persist(persist_dir=str(persist_dir))
            
        return index


def create_help_llamaindex_system(
    config_path: Optional[Path] = None,
    **override_config
) -> Dict[str, Any]:
    """Factory function to create complete LlamaIndex help system."""
    
    # Load configuration
    if config_path and config_path.exists():
        import json
        with open(config_path) as f:
            config_dict = json.load(f)
    else:
        config_dict = {}
    
    # Apply overrides
    config_dict.update(override_config)
    
    # Create hybrid retriever (same as LangChain)
    from .langchain_integration import create_help_langchain_system
    langchain_system = create_help_langchain_system(config_path, **override_config)
    hybrid_retriever = langchain_system["hybrid_retriever"]
    
    # Create LlamaIndex components
    query_engine = HelpQueryEngine(
        hybrid_retriever=hybrid_retriever,
        llm_model=config_dict.get("llm_model", "gpt-3.5-turbo"),
        similarity_top_k=config_dict.get("similarity_top_k", 5)
    )
    
    chat_engine = HelpChatEngine(
        hybrid_retriever=hybrid_retriever,
        llm_model=config_dict.get("llm_model", "gpt-3.5-turbo"),
        similarity_top_k=config_dict.get("similarity_top_k", 5)
    )
    
    # Create index builder if documents path provided
    index_builder = None
    data_dir = Path(config_dict.get("data_dir", "data"))
    documents_path = data_dir / "sparse_index" / "documents.pkl"
    if documents_path.exists():
        index_builder = HelpIndexBuilder(documents_path)
    
    return {
        "hybrid_retriever": hybrid_retriever,
        "query_engine": query_engine,
        "chat_engine": chat_engine,
        "llamaindex_retriever": HelpLlamaIndexRetriever(hybrid_retriever),
        "index_builder": index_builder,
        "config": langchain_system["config"]
    }
