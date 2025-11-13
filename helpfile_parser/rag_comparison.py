"""
HTML形式のRAG化について、複数の方式を検討し、比較する機能を提供します。

各方式に対して同じ質問を行い、応答を比較することができます。
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from abc import ABC, abstractmethod
from dotenv import load_dotenv

try:
    from .ingest_neo4j import (
        ingest_help_files,
        _resolve_neo4j_config,
    )
    from .rag_config import (
        RAGComparisonConfig,
        RAGComparisonSettings,
        load_config_file,
        save_config_file,
        create_default_config_file,
        merge_configs,
    )
except ImportError:
    CURRENT_DIR = Path(__file__).resolve().parent
    if str(CURRENT_DIR) not in sys.path:
        sys.path.insert(0, str(CURRENT_DIR))
    from ingest_neo4j import (
        ingest_help_files,
        _resolve_neo4j_config,
    )
    try:
        from rag_config import (
            RAGComparisonConfig,
            RAGComparisonSettings,
            load_config_file,
            save_config_file,
            create_default_config_file,
            merge_configs,
        )
    except ImportError:
        # rag_configモジュールが存在しない場合のフォールバック
        RAGComparisonConfig = None
        RAGComparisonSettings = None
        load_config_file = None
        save_config_file = None
        create_default_config_file = None
        merge_configs = None


# RAG方式のタイプ定義
RAG_TYPE_PROPERTY_GRAPH = "property_graph"  # LlamaIndex PropertyGraphIndex
RAG_TYPE_VECTOR_STORE = "vector_store"  # LlamaIndex VectorStoreIndex (Chroma)
RAG_TYPE_LANGCHAIN_CHROMA = "langchain_chroma"  # LangChain + Chroma
RAG_TYPE_LANGCHAIN_NEO4J = "langchain_neo4j"  # LangChain + Neo4j Graph


@dataclass(frozen=True, slots=True)
class RAGConfig:
    """RAG方式の設定を定義するクラス"""

    name: str  # 方式名（例: "default", "small_chunks", "llm_extract"）
    description: str  # 方式の説明
    rag_type: str = RAG_TYPE_PROPERTY_GRAPH  # RAG方式のタイプ
    chunk_size: int = 800
    chunk_overlap: int = 120
    use_llm_extract: bool = False
    llm_model: Optional[str] = None
    embed_kg_nodes: bool = True
    database: Optional[str] = None  # Noneの場合はデフォルトDB、指定時は別DBを使用
    chroma_persist_dir: Optional[str] = None  # Chromaの永続化ディレクトリ
    chroma_collection: Optional[str] = None  # Chromaのコレクション名

    def get_database_name(self) -> str:
        """実際に使用するデータベース名を取得"""
        if self.database:
            return self.database
        return os.getenv("NEO4J_DATABASE", "neo4j")

    def to_dict(self) -> dict:
        """設定を辞書形式に変換"""
        return asdict(self)


@dataclass(slots=True)
class QueryResult:
    """1つの質問に対する応答結果"""

    config_name: str
    question: str
    answer: str
    retrieved_nodes: List[Dict[str, Any]] = field(default_factory=list)
    execution_time_seconds: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """結果を辞書形式に変換"""
        return {
            "config_name": self.config_name,
            "question": self.question,
            "answer": self.answer,
            "retrieved_nodes_count": len(self.retrieved_nodes),
            "execution_time_seconds": self.execution_time_seconds,
            "error": self.error,
            "timestamp": datetime.utcnow().isoformat(),
        }


@dataclass(slots=True)
class ComparisonResult:
    """複数方式の比較結果"""

    question: str
    results: List[QueryResult] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """比較結果を辞書形式に変換"""
        return {
            "question": self.question,
            "timestamp": self.timestamp.isoformat(),
            "results": [r.to_dict() for r in self.results],
        }

    def to_markdown(self) -> str:
        """比較結果をMarkdown形式で出力"""
        lines = [
            f"# 質問: {self.question}",
            "",
            f"**実行日時**: {self.timestamp.isoformat()}",
            "",
            "## 結果比較",
            "",
        ]

        for result in self.results:
            lines.append(f"### {result.config_name}")
            if result.error:
                lines.append(f"**エラー**: {result.error}")
            else:
                lines.append(f"**実行時間**: {result.execution_time_seconds:.2f}秒")
                lines.append(f"**取得ノード数**: {len(result.retrieved_nodes)}")
                lines.append("")
                lines.append("**回答**:")
                lines.append("```")
                lines.append(result.answer)
                lines.append("```")
                lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)


# デフォルトのRAG方式設定
# 注意: 各方式で異なるデータベースを使用する場合は、databaseパラメータを指定してください
# 例: database="rag_default" のように指定すると、そのデータベースに保存されます
DEFAULT_CONFIGS: List[RAGConfig] = [
    # PropertyGraphIndex方式
    RAGConfig(
        name="property_graph_default",
        description="PropertyGraphIndex（chunk_size=800, overlap=120, embed有効）",
        rag_type=RAG_TYPE_PROPERTY_GRAPH,
        chunk_size=800,
        chunk_overlap=120,
        embed_kg_nodes=True,
    ),
    # VectorStoreIndex方式
    RAGConfig(
        name="vector_store_default",
        description="VectorStoreIndex (Chroma)（chunk_size=800, overlap=120）",
        rag_type=RAG_TYPE_VECTOR_STORE,
        chunk_size=800,
        chunk_overlap=120,
    ),
    RAGConfig(
        name="vector_store_small",
        description="VectorStoreIndex (Chroma)（chunk_size=400, overlap=60）",
        rag_type=RAG_TYPE_VECTOR_STORE,
        chunk_size=400,
        chunk_overlap=60,
    ),
    # LangChain + Chroma方式
    RAGConfig(
        name="langchain_chroma_default",
        description="LangChain + Chroma（chunk_size=800, overlap=120）",
        rag_type=RAG_TYPE_LANGCHAIN_CHROMA,
        chunk_size=800,
        chunk_overlap=120,
    ),
    # LangChain + Neo4j方式
    RAGConfig(
        name="langchain_neo4j",
        description="LangChain + Neo4j Graph（既存のNeo4jデータを使用）",
        rag_type=RAG_TYPE_LANGCHAIN_NEO4J,
    ),
]


class RAGImplementation(ABC):
    """RAG方式の抽象基底クラス"""

    @abstractmethod
    def build_index(
        self,
        root: Path,
        config: RAGConfig,
        *,
        wipe: bool = False,
        max_files: Optional[int] = None,
        test_files: Optional[Sequence[Path]] = None,
        file_pattern: Optional[str] = None,
    ) -> None:
        """インデックスを構築"""
        pass

    @abstractmethod
    def query(
        self,
        config: RAGConfig,
        question: str,
        *,
        top_k: int = 5,
    ) -> QueryResult:
        """質問を実行"""
        pass


class PropertyGraphRAG(RAGImplementation):
    """LlamaIndex PropertyGraphIndex実装"""

    def build_index(
        self,
        root: Path,
        config: RAGConfig,
        *,
        wipe: bool = False,
        max_files: Optional[int] = None,
        test_files: Optional[Sequence[Path]] = None,
        file_pattern: Optional[str] = None,
    ) -> None:
        """PropertyGraphIndexを構築"""
        logging.info("方式 '%s' でPropertyGraphIndexを構築中...", config.name)

        # test_filesまたはfile_patternが指定されている場合は警告
        if test_files or file_pattern:
            logging.warning(
                "PropertyGraphIndex方式では、test_files/file_patternオプションは現在サポートされていません。"
                "すべてのファイルを読み込みます。"
            )

        stats = ingest_help_files(
            root,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            database=config.database,
            wipe=wipe,
            use_llm_extract=config.use_llm_extract,
            llm_model=config.llm_model,
            embed_kg_nodes=config.embed_kg_nodes,
            max_files=max_files,
        )
        logging.info("方式 '%s' のインデックス構築完了: %s", config.name, stats)

    def query(
        self,
        config: RAGConfig,
        question: str,
        *,
        top_k: int = 5,
    ) -> QueryResult:
        """PropertyGraphIndexで質問を実行"""
        import time
        from llama_index.core.indices.property_graph.base import PropertyGraphIndex
        from llama_index.core.query_engine import RetrieverQueryEngine
        from llama_index.core.retrievers import PropertyGraphRetriever
        from llama_index.core.settings import Settings
        from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore

        start_time = time.time()
        result = QueryResult(config_name=config.name, question=question)

        try:
            load_dotenv()
            uri, user, password, _ = _resolve_neo4j_config(config.database)
            database_name = config.get_database_name()

            graph_store = Neo4jPropertyGraphStore(
                username=user,
                password=password,
                url=uri,
                database=database_name,
            )

            try:
                # 埋め込みモデルを設定
                if config.embed_kg_nodes:
                    from llama_index.embeddings.openai import OpenAIEmbedding
                    if getattr(Settings, "embed_model", None) is None:
                        Settings.embed_model = OpenAIEmbedding(
                            model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
                        )

                # LLMを設定
                llm = None
                if config.use_llm_extract:
                    from llama_index.llms.openai import OpenAI
                    llm = OpenAI(model=config.llm_model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

                # PropertyGraphIndexを作成
                index = PropertyGraphIndex(
                    property_graph_store=graph_store,
                    llm=llm,
                    embed_kg_nodes=config.embed_kg_nodes,
                )

                # QueryEngineを作成
                retriever = PropertyGraphRetriever(
                    index=index,
                    similarity_top_k=top_k,
                )
                query_engine = RetrieverQueryEngine.from_args(
                    retriever=retriever,
                )

                # 質問を実行
                response = query_engine.query(question)

                result.answer = str(response)
                if hasattr(response, "source_nodes"):
                    result.retrieved_nodes = [
                        {
                            "node_id": node.node_id,
                            "text": node.get_content()[:200] if hasattr(node, "get_content") else str(node)[:200],
                        }
                        for node in response.source_nodes
                    ]

            finally:
                graph_store.close()

            result.execution_time_seconds = time.time() - start_time

        except Exception as exc:
            result.error = str(exc)
            result.execution_time_seconds = time.time() - start_time
            logging.error("方式 '%s' での質問実行中にエラー: %s", config.name, exc)

        return result


class VectorStoreRAG(RAGImplementation):
    """LlamaIndex VectorStoreIndex (Chroma)実装"""

    def build_index(
        self,
        root: Path,
        config: RAGConfig,
        *,
        wipe: bool = False,
        max_files: Optional[int] = None,
        test_files: Optional[Sequence[Path]] = None,
        file_pattern: Optional[str] = None,
    ) -> None:
        """VectorStoreIndexを構築"""
        logging.info("方式 '%s' でVectorStoreIndexを構築中...", config.name)
        from llama_index.core import VectorStoreIndex, Document, StorageContext, Settings
        from llama_index.core.node_parser import SimpleNodeParser
        from llama_index.vector_stores.chroma import ChromaVectorStore
        from llama_index.embeddings.openai import OpenAIEmbedding
        import chromadb

        # ドキュメントを読み込み
        from helpfile_parser import extract_help_document

        help_docs = []
        if test_files:
            # 特定のファイルのみを読み込む
            for file_path in test_files:
                if file_path.exists():
                    help_docs.append(extract_help_document(file_path))
                else:
                    # 相対パスの場合、rootからの相対パスとして扱う
                    full_path = root / file_path if not file_path.is_absolute() else file_path
                    if full_path.exists():
                        help_docs.append(extract_help_document(full_path))
                    else:
                        logging.warning("ファイルが見つかりません: %s", file_path)
        elif file_pattern:
            # ファイル名パターンでフィルタ
            import fnmatch
            from helpfile_parser import iter_help_documents
            documents_iter = iter_help_documents(root)
            for doc in documents_iter:
                if fnmatch.fnmatch(doc.source_path.name, file_pattern):
                    help_docs.append(doc)
                    if max_files and len(help_docs) >= max_files:
                        break
        else:
            # 通常の読み込み
            from helpfile_parser import iter_help_documents
            documents_iter = iter_help_documents(root)
            if max_files is not None:
                from itertools import islice
                documents_iter = islice(documents_iter, max_files)
            help_docs = list(documents_iter)

        # LlamaIndex Documentに変換
        llama_docs = []
        for help_doc in help_docs:
            for section in help_doc.sections:
                text = section.heading if not section.content else f"{section.heading}\n\n{section.content}"
                llama_docs.append(
                    Document(
                        text=text,
                        metadata={
                            "source_path": str(help_doc.source_path),
                            "title": help_doc.title,
                            "section_heading": section.heading,
                            "section_level": section.level,
                        },
                    )
                )

        # チャンク化
        parser = SimpleNodeParser.from_defaults(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
        )
        nodes = parser.get_nodes_from_documents(llama_docs)

        # 埋め込みモデルを設定
        Settings.embed_model = OpenAIEmbedding(
            model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        )

        # Chromaを設定
        persist_dir = config.chroma_persist_dir or f"data/chroma_{config.name}"
        collection_name = config.chroma_collection or f"help_{config.name}"
        Path(persist_dir).mkdir(parents=True, exist_ok=True)

        if wipe:
            # 既存のコレクションを削除
            try:
                client = chromadb.PersistentClient(path=persist_dir)
                client.delete_collection(name=collection_name)
            except Exception:
                pass

        chroma_client = chromadb.PersistentClient(path=persist_dir)
        chroma_collection = chroma_client.get_or_create_collection(name=collection_name)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # インデックスを構築
        VectorStoreIndex(nodes, storage_context=storage_context)
        logging.info("方式 '%s' のインデックス構築完了: %d ノード", config.name, len(nodes))

    def query(
        self,
        config: RAGConfig,
        question: str,
        *,
        top_k: int = 5,
    ) -> QueryResult:
        """VectorStoreIndexで質問を実行"""
        import time
        from llama_index.core import VectorStoreIndex, StorageContext, Settings
        from llama_index.vector_stores.chroma import ChromaVectorStore
        from llama_index.embeddings.openai import OpenAIEmbedding
        import chromadb

        start_time = time.time()
        result = QueryResult(config_name=config.name, question=question)

        try:
            # 埋め込みモデルを設定
            Settings.embed_model = OpenAIEmbedding(
                model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            )

            # Chromaを読み込み
            persist_dir = config.chroma_persist_dir or f"data/chroma_{config.name}"
            collection_name = config.chroma_collection or f"help_{config.name}"

            chroma_client = chromadb.PersistentClient(path=persist_dir)
            chroma_collection = chroma_client.get_collection(name=collection_name)
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)

            # インデックスを読み込み
            index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)

            # QueryEngineを作成
            query_engine = index.as_query_engine(similarity_top_k=top_k)

            # 質問を実行
            response = query_engine.query(question)

            result.answer = str(response)
            if hasattr(response, "source_nodes"):
                result.retrieved_nodes = [
                    {
                        "node_id": node.node_id,
                        "text": node.get_content()[:200] if hasattr(node, "get_content") else str(node)[:200],
                    }
                    for node in response.source_nodes
                ]

            result.execution_time_seconds = time.time() - start_time

        except Exception as exc:
            result.error = str(exc)
            result.execution_time_seconds = time.time() - start_time
            logging.error("方式 '%s' での質問実行中にエラー: %s", config.name, exc)

        return result


class LangChainChromaRAG(RAGImplementation):
    """LangChain + Chroma実装"""

    def build_index(
        self,
        root: Path,
        config: RAGConfig,
        *,
        wipe: bool = False,
        max_files: Optional[int] = None,
        test_files: Optional[Sequence[Path]] = None,
        file_pattern: Optional[str] = None,
    ) -> None:
        """LangChain + Chromaでインデックスを構築"""
        logging.info("方式 '%s' でLangChain + Chromaを構築中...", config.name)
        from langchain_community.vectorstores import Chroma
        from langchain_openai import OpenAIEmbeddings
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        try:
            from .helpfile_parser import extract_help_document
        except ImportError:
            from helpfile_parser import extract_help_document

        # ドキュメントを読み込み
        help_docs = []
        if test_files:
            # 特定のファイルのみを読み込む
            for file_path in test_files:
                if file_path.exists():
                    help_docs.append(extract_help_document(file_path))
                else:
                    # 相対パスの場合、rootからの相対パスとして扱う
                    full_path = root / file_path if not file_path.is_absolute() else file_path
                    if full_path.exists():
                        help_docs.append(extract_help_document(full_path))
                    else:
                        logging.warning("ファイルが見つかりません: %s", file_path)
        elif file_pattern:
            # ファイル名パターンでフィルタ
            import fnmatch
            try:
                from .helpfile_parser import iter_help_documents
            except ImportError:
                from helpfile_parser import iter_help_documents
            documents_iter = iter_help_documents(root)
            for doc in documents_iter:
                if fnmatch.fnmatch(doc.source_path.name, file_pattern):
                    help_docs.append(doc)
                    if max_files and len(help_docs) >= max_files:
                        break
        else:
            # 通常の読み込み
            try:
                from .helpfile_parser import iter_help_documents
            except ImportError:
                from helpfile_parser import iter_help_documents
            documents_iter = iter_help_documents(root)
            if max_files is not None:
                from itertools import islice
                documents_iter = islice(documents_iter, max_files)
            help_docs = list(documents_iter)

        # テキストに変換
        texts = []
        metadatas = []
        for help_doc in help_docs:
            for section in help_doc.sections:
                text = section.heading if not section.content else f"{section.heading}\n\n{section.content}"
                texts.append(text)
                metadatas.append({
                    "source_path": str(help_doc.source_path),
                    "title": help_doc.title,
                    "section_heading": section.heading,
                    "section_level": section.level,
                })

        # チャンク化
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
        )
        splits = text_splitter.create_documents(texts, metadatas=metadatas)

        # Chromaに保存
        persist_directory = config.chroma_persist_dir or f"data/chroma_langchain_{config.name}"
        collection_name = config.chroma_collection or f"help_langchain_{config.name}"

        if wipe:
            # 既存のディレクトリを削除
            import shutil
            if Path(persist_directory).exists():
                shutil.rmtree(persist_directory)

        embeddings = OpenAIEmbeddings(
            model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        )

        Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=persist_directory,
            collection_name=collection_name,
        )
        logging.info("方式 '%s' のインデックス構築完了: %d チャンク", config.name, len(splits))

    def query(
        self,
        config: RAGConfig,
        question: str,
        *,
        top_k: int = 5,
    ) -> QueryResult:
        """LangChain + Chromaで質問を実行"""
        import time
        from langchain_community.vectorstores import Chroma
        from langchain_openai import OpenAIEmbeddings, ChatOpenAI
        from langchain.chains import RetrievalQA

        start_time = time.time()
        result = QueryResult(config_name=config.name, question=question)

        try:
            # Chromaを読み込み
            persist_directory = config.chroma_persist_dir or f"data/chroma_langchain_{config.name}"
            collection_name = config.chroma_collection or f"help_langchain_{config.name}"

            embeddings = OpenAIEmbeddings(
                model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            )

            vectordb = Chroma(
                persist_directory=persist_directory,
                embedding_function=embeddings,
                collection_name=collection_name,
            )

            # LLMを設定
            llm = ChatOpenAI(
                model=config.llm_model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=0.1,
            )

            # RetrievalQAチェーンを作成
            qa_chain = RetrievalQA.from_llm(
                llm=llm,
                retriever=vectordb.as_retriever(search_kwargs={"k": top_k}),
            )

            # 質問を実行
            answer = qa_chain.run(question)

            result.answer = answer
            # LangChainのRetrievalQAはsource_documentsを返さないため、手動で取得
            retriever = vectordb.as_retriever(search_kwargs={"k": top_k})
            docs = retriever.get_relevant_documents(question)
            result.retrieved_nodes = [
                {
                    "content": doc.page_content[:200],
                    "metadata": doc.metadata,
                }
                for doc in docs
            ]

            result.execution_time_seconds = time.time() - start_time

        except Exception as exc:
            result.error = str(exc)
            result.execution_time_seconds = time.time() - start_time
            logging.error("方式 '%s' での質問実行中にエラー: %s", config.name, exc)

        return result


class LangChainNeo4jRAG(RAGImplementation):
    """LangChain + Neo4j Graph実装"""

    def build_index(
        self,
        root: Path,
        config: RAGConfig,
        *,
        wipe: bool = False,
        max_files: Optional[int] = None,
        test_files: Optional[Sequence[Path]] = None,
        file_pattern: Optional[str] = None,
    ) -> None:
        """LangChain + Neo4j Graphは既存のNeo4jデータを使用（構築不要）"""
        logging.info("方式 '%s' は既存のNeo4jデータを使用します", config.name)
        # LangChain Neo4jは既存のNeo4jグラフを使用するため、構築処理は不要
        # 必要に応じて、既存のingest_neo4j.pyを使用してデータを構築

    def query(
        self,
        config: RAGConfig,
        question: str,
        *,
        top_k: int = 5,
    ) -> QueryResult:
        """LangChain + Neo4j Graphで質問を実行"""
        import time
        from langchain_neo4j import Neo4jGraph
        from langchain_neo4j.chains.graph_qa.cypher import GraphCypherQAChain
        from langchain_openai import ChatOpenAI

        start_time = time.time()
        result = QueryResult(config_name=config.name, question=question)

        try:
            load_dotenv()
            uri, user, password, _ = _resolve_neo4j_config(config.database)
            database_name = config.get_database_name()

            # Neo4jグラフを作成
            graph = Neo4jGraph(
                url=uri,
                username=user,
                password=password,
                database=database_name,
            )

            # LLMを設定
            llm = ChatOpenAI(
                model=config.llm_model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=0.1,
            )

            # GraphCypherQAChainを作成
            qa_chain = GraphCypherQAChain.from_llm(
                llm=llm,
                graph=graph,
                verbose=False,
                top_k=top_k,
                allow_dangerous_requests=True,
            )

            # 質問を実行
            answer = qa_chain.run(question)

            result.answer = answer
            # Neo4j Graph QAはsource_documentsを返さないため、空リスト
            result.retrieved_nodes = []

            result.execution_time_seconds = time.time() - start_time

        except Exception as exc:
            result.error = str(exc)
            result.execution_time_seconds = time.time() - start_time
            logging.error("方式 '%s' での質問実行中にエラー: %s", config.name, exc)

        return result


def get_rag_implementation(config: RAGConfig) -> RAGImplementation:
    """RAG方式に応じた実装を取得"""
    if config.rag_type == RAG_TYPE_PROPERTY_GRAPH:
        return PropertyGraphRAG()
    elif config.rag_type == RAG_TYPE_VECTOR_STORE:
        return VectorStoreRAG()
    elif config.rag_type == RAG_TYPE_LANGCHAIN_CHROMA:
        return LangChainChromaRAG()
    elif config.rag_type == RAG_TYPE_LANGCHAIN_NEO4J:
        return LangChainNeo4jRAG()
    else:
        raise ValueError(f"未知のRAG方式: {config.rag_type}")


def build_index_for_config(
    root: Path,
    config: RAGConfig,
    *,
    wipe: bool = False,
    max_files: Optional[int] = None,
    test_files: Optional[Sequence[Path]] = None,
    file_pattern: Optional[str] = None,
) -> None:
    """指定された設定でインデックスを構築"""
    logging.info("方式 '%s' でインデックスを構築中...", config.name)
    logging.info("設定: %s", config.description)
    logging.info("RAG方式: %s", config.rag_type)
    if test_files:
        logging.info("テストファイルを読み込み: %s", [str(f) for f in test_files])
    elif file_pattern:
        logging.info("ファイルパターンでフィルタ: %s", file_pattern)

    implementation = get_rag_implementation(config)
    implementation.build_index(
        root, config, wipe=wipe, max_files=max_files, test_files=test_files, file_pattern=file_pattern
    )


def query_with_config(
    config: RAGConfig,
    question: str,
    *,
    top_k: int = 5,
) -> QueryResult:
    """指定された設定で質問を実行"""
    implementation = get_rag_implementation(config)
    return implementation.query(config, question, top_k=top_k)


def compare_rag_configs(
    configs: Sequence[RAGConfig],
    questions: Sequence[str],
    *,
    top_k: int = 5,
) -> List[ComparisonResult]:
    """複数のRAG方式で同じ質問を実行し、結果を比較"""
    comparison_results: List[ComparisonResult] = []

    for question in questions:
        logging.info("質問を実行中: %s", question)
        comparison = ComparisonResult(question=question)

        for config in configs:
            logging.info("方式 '%s' で質問を実行中...", config.name)
            result = query_with_config(config, question, top_k=top_k)
            comparison.results.append(result)

        comparison_results.append(comparison)

    return comparison_results


def build_all_indices(
    root: Path,
    configs: Sequence[RAGConfig],
    *,
    wipe: bool = False,
    max_files: Optional[int] = None,
    test_files: Optional[Sequence[Path]] = None,
    file_pattern: Optional[str] = None,
) -> None:
    """すべての設定でインデックスを構築"""
    for config in configs:
        build_index_for_config(
            root, config, wipe=wipe, max_files=max_files, test_files=test_files, file_pattern=file_pattern
        )


class ExecutionSession:
    """実行セッションを管理するクラス"""

    def __init__(self, base_dir: Path = None, command: str = "unknown"):
        """実行セッションを作成"""
        if base_dir is None:
            base_dir = Path(__file__).parent / "logs"
        self.base_dir = Path(base_dir)
        self.command = command
        self.timestamp = datetime.now()
        self.session_dir = self._create_session_dir()
        self.queries: List[str] = []
        self.configs: List[RAGConfig] = []

    def _create_session_dir(self) -> Path:
        """実行セッション用のディレクトリを作成"""
        timestamp_str = self.timestamp.strftime("%Y%m%d_%H%M%S")
        session_name = f"{self.command}_{timestamp_str}"
        session_dir = self.base_dir / session_name
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def get_log_file(self) -> Path:
        """ログファイルのパスを取得"""
        return self.session_dir / "execution.log"

    def get_results_dir(self) -> Path:
        """結果保存用ディレクトリのパスを取得"""
        results_dir = self.session_dir / "results"
        results_dir.mkdir(exist_ok=True)
        return results_dir

    def save_query(self, question: str) -> None:
        """クエリを記録"""
        self.queries.append(question)
        queries_file = self.session_dir / "queries.txt"
        with queries_file.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()}: {question}\n")

    def save_configs(self, configs: Sequence[RAGConfig]) -> None:
        """使用した設定を保存"""
        self.configs = list(configs)
        configs_file = self.session_dir / "configs.json"
        configs_data = [config.to_dict() for config in configs]
        configs_file.write_text(
            json.dumps(configs_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def save_results(self, comparison_results: List[ComparisonResult], format: str = "both") -> None:
        """結果を保存（format: 'json', 'markdown', 'both'）"""
        results_dir = self.get_results_dir()

        if format in ("json", "both"):
            json_file = results_dir / "comparison_results.json"
            json_data = [cr.to_dict() for cr in comparison_results]
            json_file.write_text(
                json.dumps(json_data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        if format in ("markdown", "both"):
            markdown_file = results_dir / "comparison_results.md"
            markdown_lines = [cr.to_markdown() for cr in comparison_results]
            markdown_file.write_text("\n\n".join(markdown_lines), encoding="utf-8")

    def save_summary(self, summary: Dict[str, Any]) -> None:
        """実行サマリーを保存"""
        summary_file = self.session_dir / "summary.json"
        summary_data = {
            "command": self.command,
            "timestamp": self.timestamp.isoformat(),
            "session_dir": str(self.session_dir),
            **summary,
        }
        summary_file.write_text(
            json.dumps(summary_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _configure_logging(
    *,
    log_level: str,
    console_level: str,
    log_file: Optional[Path],
    session: Optional[ExecutionSession] = None,
) -> None:
    """ロギングを設定"""
    if sys.platform == "win32":
        try:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    numeric_log_level = getattr(logging, log_level.upper(), logging.INFO)
    numeric_console_level = getattr(logging, console_level.upper(), logging.WARNING)
    root_logger.setLevel(numeric_log_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_console_level)
    console_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    root_logger.addHandler(console_handler)

    # ログファイルを設定（sessionが指定されている場合はsessionのログファイルを使用）
    target_log_file = log_file
    if session and not target_log_file:
        target_log_file = session.get_log_file()

    if target_log_file:
        try:
            log_path = Path(target_log_file)
            if log_path.parent:
                log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setLevel(numeric_log_level)
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
            )
            root_logger.addHandler(file_handler)
        except Exception as exc:
            logging.getLogger(__name__).warning("ログファイルの設定に失敗しました: %s", exc)


def build_argument_parser() -> argparse.ArgumentParser:
    """コマンドライン引数パーサーを構築"""
    parser = argparse.ArgumentParser(
        description="HTML形式のRAG化について、複数の方式を検討し、比較します。",
    )

    subparsers = parser.add_subparsers(dest="command", help="実行するコマンド")

    # build コマンド: インデックスを構築
    build_parser = subparsers.add_parser("build", help="指定された方式でインデックスを構築")
    build_parser.add_argument(
        "root",
        type=Path,
        help="EVOSHIP_HELP_FILES ディレクトリへのパス",
    )
    build_parser.add_argument(
        "--configs",
        nargs="+",
        help="使用する方式名（未指定時はすべてのデフォルト方式）",
    )
    build_parser.add_argument(
        "--wipe",
        action="store_true",
        help="既存のインデックスを削除してから構築",
    )
    build_parser.add_argument(
        "--max-files",
        type=int,
        help="読み込む最大ファイル数",
    )
    build_parser.add_argument(
        "--test-files",
        nargs="+",
        type=Path,
        help="評価用に読み込む特定のファイル（複数指定可）。例: --test-files about_datum.html",
    )
    build_parser.add_argument(
        "--file-pattern",
        type=str,
        help="読み込むファイル名のパターン（ワイルドカード使用可）。例: --file-pattern 'about_*.html'",
    )

    # query コマンド: 質問を実行して比較
    query_parser = subparsers.add_parser("query", help="複数の方式で質問を実行して比較")
    query_parser.add_argument(
        "question",
        type=str,
        help="質問文",
    )
    query_parser.add_argument(
        "--configs",
        nargs="+",
        help="使用する方式名（未指定時はすべてのデフォルト方式）",
    )
    query_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="取得するノード数（デフォルト: 5）",
    )
    query_parser.add_argument(
        "--output",
        type=Path,
        help="結果を保存するファイルパス（JSON形式）",
    )
    query_parser.add_argument(
        "--markdown",
        type=Path,
        help="結果をMarkdown形式で保存するファイルパス",
    )

    # compare コマンド: 複数の質問を一括で比較
    compare_parser = subparsers.add_parser("compare", help="複数の質問を一括で比較")
    compare_parser.add_argument(
        "--questions",
        nargs="+",
        required=True,
        help="質問文のリスト",
    )
    compare_parser.add_argument(
        "--configs",
        nargs="+",
        help="使用する方式名（未指定時はすべてのデフォルト方式）",
    )
    compare_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="取得するノード数（デフォルト: 5）",
    )
    compare_parser.add_argument(
        "--output",
        type=Path,
        help="結果を保存するファイルパス（JSON形式）",
    )
    compare_parser.add_argument(
        "--markdown",
        type=Path,
        help="結果をMarkdown形式で保存するファイルパス",
    )

    # list コマンド: 利用可能な方式を一覧表示
    list_parser = subparsers.add_parser("list", help="利用可能な方式を一覧表示")

    # init-config コマンド: デフォルト設定ファイルを作成
    init_parser = subparsers.add_parser("init-config", help="デフォルト設定ファイルを作成")
    init_parser.add_argument(
        "--output",
        type=Path,
        default=Path("rag_comparison_config.json"),
        help="出力先の設定ファイルパス（デフォルト: rag_comparison_config.json）",
    )

    # 共通オプション（設定ファイル関連）
    for p in [build_parser, query_parser, compare_parser, list_parser]:
        p.add_argument(
            "--config-file",
            type=Path,
            help="設定ファイルのパス（未指定時はデフォルト設定を使用）",
        )
        p.add_argument(
            "--use-file-only",
            action="store_true",
            help="設定ファイルの設定のみを使用（デフォルト設定を無視）",
        )

    for p in [build_parser, query_parser, compare_parser]:
        p.add_argument(
            "--log-level",
            default="INFO",
            choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
            help="ログレベル（デフォルト: INFO）",
        )
        p.add_argument(
            "--log-file",
            type=Path,
            help="ログファイルの出力先パス",
        )
        p.add_argument(
            "--console-level",
            default="WARNING",
            choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
            help="コンソール出力のログレベル（デフォルト: WARNING）",
        )

    return parser


def get_configs_by_names(
    names: Optional[Sequence[str]],
    config_file: Optional[Path] = None,
    use_file_only: bool = False,
) -> List[RAGConfig]:
    """方式名のリストからRAGConfigのリストを取得"""
    # 設定ファイルから読み込む
    file_configs = []
    if config_file and config_file.exists() and load_config_file:
        try:
            config_data = load_config_file(config_file)
            file_configs = config_data.load_rag_configs()
            logging.info("設定ファイルから %d 個のRAG方式を読み込みました: %s", len(file_configs), config_file)
        except Exception as exc:
            logging.warning("設定ファイルの読み込みに失敗しました: %s, エラー: %s", config_file, exc)

    # 設定ファイルとデフォルト設定をマージ
    if file_configs and merge_configs:
        all_configs = merge_configs(file_configs, DEFAULT_CONFIGS, use_file_only=use_file_only)
    else:
        all_configs = DEFAULT_CONFIGS.copy()

    # 名前でフィルタ
    if names is None:
        return all_configs

    config_map = {config.name: config for config in all_configs}
    configs = []
    for name in names:
        if name in config_map:
            configs.append(config_map[name])
        else:
            logging.warning("方式 '%s' が見つかりません。スキップします。", name)
    return configs


def main(argv: Optional[Sequence[str]] = None) -> int:
    """メインエントリーポイント"""
    parser = build_argument_parser()
    args = parser.parse_args(argv if argv is not None else None)

    if args.command is None:
        parser.print_help()
        return 1

    # 実行セッションを作成（listコマンド以外）
    session = None
    if args.command != "list":
        session = ExecutionSession(command=args.command)
        logging.info("実行セッションを作成しました: %s", session.session_dir)

    # ロギング設定
    if hasattr(args, "log_level"):
        _configure_logging(
            log_level=args.log_level,
            console_level=args.console_level,
            log_file=getattr(args, "log_file", None),
            session=session,
        )

    try:
        if args.command == "init-config":
            if create_default_config_file:
                create_default_config_file(args.output)
                print(f"デフォルト設定ファイルを作成しました: {args.output}")
                print("\n設定ファイルを編集して、RAG方式をカスタマイズできます。")
                print("機密情報（APIキー、パスワードなど）は.envファイルで管理してください。")
            else:
                logging.error("設定ファイル機能が利用できません。")
                return 1
            return 0

        if args.command == "list":
            # 設定ファイルから読み込む
            config_file = getattr(args, "config_file", None)
            use_file_only = getattr(args, "use_file_only", False)
            configs = get_configs_by_names(None, config_file=config_file, use_file_only=use_file_only)

            print("利用可能なRAG方式:")
            if config_file and config_file.exists():
                print(f"（設定ファイル: {config_file}）")
            print()
            for config in configs:
                print(f"  {config.name}: {config.description}")
                print(f"    - rag_type: {config.rag_type}")
                print(f"    - chunk_size: {config.chunk_size}")
                print(f"    - chunk_overlap: {config.chunk_overlap}")
                print(f"    - use_llm_extract: {config.use_llm_extract}")
                print(f"    - embed_kg_nodes: {config.embed_kg_nodes}")
                print(f"    - database: {config.get_database_name()}")
                print()
            return 0

        # 設定ファイルから読み込む
        config_file = getattr(args, "config_file", None)
        use_file_only = getattr(args, "use_file_only", False)
        configs = get_configs_by_names(
            getattr(args, "configs", None),
            config_file=config_file,
            use_file_only=use_file_only,
        )

        # 設定ファイルからデフォルト設定を読み込む
        settings = None
        if config_file and config_file.exists() and load_config_file:
            try:
                config_data = load_config_file(config_file)
                settings = config_data.get_settings()
                # コマンドライン引数で上書きされていない場合のみ設定ファイルの値を使用
                if hasattr(args, "top_k") and args.top_k == 5:  # デフォルト値の場合
                    args.top_k = settings.top_k
                if hasattr(args, "log_level") and args.log_level == "INFO":
                    args.log_level = settings.log_level
                if hasattr(args, "console_level") and args.console_level == "WARNING":
                    args.console_level = settings.console_level
            except Exception as exc:
                logging.warning("設定ファイルからデフォルト設定の読み込みに失敗しました: %s", exc)

        # 設定を保存
        if session:
            session.save_configs(configs)
            logging.info("設定を保存しました: %s", session.session_dir / "configs.json")

        if args.command == "build":
            # test_filesを処理（相対パスの場合はrootからの相対パスとして扱う）
            test_files = None
            if hasattr(args, "test_files") and args.test_files:
                test_files = []
                for file_path in args.test_files:
                    if file_path.is_absolute():
                        test_files.append(file_path)
                    else:
                        # 相対パスの場合、rootからの相対パスとして扱う
                        full_path = args.root / file_path
                        test_files.append(full_path)

            build_all_indices(
                args.root,
                configs,
                wipe=args.wipe,
                max_files=getattr(args, "max_files", None),
                test_files=test_files,
                file_pattern=getattr(args, "file_pattern", None),
            )
            # サマリーを保存
            if session:
                session.save_summary({
                    "command": "build",
                    "root_path": str(args.root),
                    "configs_count": len(configs),
                    "wipe": args.wipe,
                    "max_files": getattr(args, "max_files", None),
                    "test_files": [str(f) for f in test_files] if test_files else None,
                    "file_pattern": getattr(args, "file_pattern", None),
                })
                logging.info("実行サマリーを保存しました: %s", session.session_dir / "summary.json")
            return 0

        if args.command == "query":
            # クエリを記録
            if session:
                session.save_query(args.question)

            comparison_results = compare_rag_configs(
                configs,
                [args.question],
                top_k=getattr(args, "top_k", 5),
            )

            # セッションに結果を保存
            if session:
                session.save_results(comparison_results, format="both")
                session.save_summary({
                    "command": "query",
                    "question": args.question,
                    "configs_count": len(configs),
                    "top_k": getattr(args, "top_k", 5),
                    "results_count": len(comparison_results),
                })
                logging.info("結果を保存しました: %s", session.get_results_dir())

            # 指定されたパスにも保存（後方互換性のため）
            if args.output:
                output_data = [cr.to_dict() for cr in comparison_results]
                args.output.write_text(
                    json.dumps(output_data, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                logging.info("結果を保存しました: %s", args.output)

            if args.markdown:
                markdown_content = comparison_results[0].to_markdown()
                args.markdown.write_text(markdown_content, encoding="utf-8")
                logging.info("Markdown形式で結果を保存しました: %s", args.markdown)

            # コンソールにも出力
            print(comparison_results[0].to_markdown())
            if session:
                print(f"\n実行セッション: {session.session_dir}")
            return 0

        if args.command == "compare":
            # クエリを記録
            if session:
                for question in args.questions:
                    session.save_query(question)

            comparison_results = compare_rag_configs(
                configs,
                args.questions,
                top_k=args.top_k,
            )

            # セッションに結果を保存
            if session:
                session.save_results(comparison_results, format="both")
                session.save_summary({
                    "command": "compare",
                    "questions_count": len(args.questions),
                    "questions": args.questions,
                    "configs_count": len(configs),
                    "top_k": args.top_k,
                    "results_count": len(comparison_results),
                })
                logging.info("結果を保存しました: %s", session.get_results_dir())

            # 指定されたパスにも保存（後方互換性のため）
            if args.output:
                output_data = [cr.to_dict() for cr in comparison_results]
                args.output.write_text(
                    json.dumps(output_data, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                logging.info("結果を保存しました: %s", args.output)

            if args.markdown:
                markdown_lines = [cr.to_markdown() for cr in comparison_results]
                args.markdown.write_text("\n\n".join(markdown_lines), encoding="utf-8")
                logging.info("Markdown形式で結果を保存しました: %s", args.markdown)

            # コンソールにも出力
            for comparison in comparison_results:
                print(comparison.to_markdown())
                print("\n" + "=" * 80 + "\n")
            if session:
                print(f"実行セッション: {session.session_dir}")
            return 0

    except Exception as exc:
        logging.error("処理中にエラーが発生しました: %s", exc, exc_info=True)
        if session:
            error_file = session.session_dir / "error.log"
            error_file.write_text(
                f"エラー発生時刻: {datetime.now().isoformat()}\n"
                f"エラー内容: {str(exc)}\n"
                f"トレースバック:\n{traceback.format_exc()}",
                encoding="utf-8",
            )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
