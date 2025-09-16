# mycode/fulltext_search.py
"""
This module provides a full-text search engine using Whoosh.
"""
import os
from pathlib import Path
from typing import List, Tuple

from langchain_core.documents import Document
from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import Schema, TEXT, ID
from whoosh import index
from whoosh.qparser import QueryParser

# --- Constants ---

DEFAULT_INDEX_DIR = Path("data/whoosh_index")

# --- Whoosh Search Engine ---

class WhooshSearch:
    """
    A wrapper class for a Whoosh full-text search index.
    """
    def __init__(self, index_dir: Path = DEFAULT_INDEX_DIR):
        self.index_dir = index_dir
        self.ix = None
        self.schema = Schema(
            doc_id=ID(stored=True, unique=True),
            content=TEXT(stored=True, analyzer=StemmingAnalyzer()),
            object=ID(stored=True),
            method_name=ID(stored=True)
        )

    def _ensure_index_exists(self) -> None:
        """Opens an existing index or raises an error if it doesn't exist."""
        if self.ix is None:
            if not self.index_dir.exists() or not index.exists_in(self.index_dir):
                raise FileNotFoundError(f"Whoosh index not found at {self.index_dir}. Please run the ingestion script first.")
            self.ix = index.open_dir(self.index_dir)

    def index_documents(self, documents: List[Document], force_recreate: bool = True):
        """
        Creates or overwrites a Whoosh index with the given documents.

        Args:
            documents: A list of LangChain Document objects.
            force_recreate: If True, deletes the existing index before creating a new one.
        """
        if self.index_dir.exists() and force_recreate:
            import shutil
            shutil.rmtree(self.index_dir)

        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.ix = index.create_in(self.index_dir, self.schema)
        writer = self.ix.writer()

        for doc in documents:
            writer.add_document(
                doc_id=doc.metadata.get("doc_id"),
                content=doc.page_content,
                object=doc.metadata.get("object"),
                method_name=doc.metadata.get("method_name")
            )

        writer.commit()
        print(f"✔ Whoosh index created with {len(documents)} documents at: {self.index_dir}")

    def search(self, query_text: str, limit: int = 10) -> List[Tuple[str, float]]:
        """
        Searches the index for the given query text.

        Args:
            query_text: The string to search for.
            limit: The maximum number of results to return.

        Returns:
            A list of tuples, where each tuple contains the doc_id and the relevance score.
        """
        self._ensure_index_exists()

        results_list = []
        with self.ix.searcher() as searcher:
            # We search in the 'content' field by default
            parser = QueryParser("content", self.ix.schema)
            query = parser.parse(query_text)

            results = searcher.search(query, limit=limit)

            for hit in results:
                results_list.append((hit['doc_id'], hit.score))

        return results_list

    def get_document(self, doc_id: str) -> Document:
        """
        Retrieves a document from the index by its doc_id.
        """
        self._ensure_index_exists()

        with self.ix.searcher() as searcher:
            results = searcher.document(doc_id=doc_id)
            if results:
                return Document(
                    page_content=results['content'],
                    metadata={
                        "doc_id": results['doc_id'],
                        "object": results['object'],
                        "method_name": results['method_name'],
                    }
                )
        raise KeyError(f"Document with doc_id '{doc_id}' not found in Whoosh index.")
