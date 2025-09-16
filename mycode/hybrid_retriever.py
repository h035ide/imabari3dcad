# mycode/hybrid_retriever.py
"""
This module defines the HybridRetriever, which combines the results from
dense, sparse, and full-text search using Reciprocal Rank Fusion (RRF).
"""
from typing import List, Dict
import logging
from concurrent.futures import ThreadPoolExecutor

from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma

from mycode.fulltext_search import WhooshSearch
from mycode.sparse_vector_db import SparseVectorSearch

logger = logging.getLogger(__name__)


class HybridRetriever(BaseRetriever):
    """
    A retriever that combines results from a dense vector store, a sparse
    vector store, and a full-text search engine.
    """
    def __init__(
        self,
        dense_retriever: Chroma,
        sparse_search: SparseVectorSearch,
        fulltext_search: WhooshSearch,
        k: int = 10,
        rrf_k: int = 60,
    ):
        """
        Args:
            dense_retriever: A Chroma vector store instance.
            sparse_search: An instance of our SparseVectorSearch.
            fulltext_search: An instance of our WhooshSearch.
            k: The final number of documents to return.
            rrf_k: The 'k' parameter for the RRF formula.
        """
        super().__init__()
        self.dense_retriever = dense_retriever
        self.sparse_search = sparse_search
        self.fulltext_search = fulltext_search
        self.k = k
        self.rrf_k = rrf_k

    def _get_relevant_documents(self, query: str, *, run_manager=None) -> List[Document]:
        """
        The core logic for fetching documents. It queries the three backends
        and fuses the results using RRF.
        """
        # --- 1. Query all retrievers in parallel ---
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_dense = executor.submit(self.dense_retriever.similarity_search_with_score, query, k=self.k * 2)
            future_sparse = executor.submit(self.sparse_search.search, query, limit=self.k * 2)
            future_fulltext = executor.submit(self.fulltext_search.search, query, limit=self.k * 2)

            dense_results = future_dense.result()
            sparse_results = future_sparse.result()
            fulltext_results = future_fulltext.result()

        # --- 2. Process results into a common format ---
        # The dense retriever returns (Document, score), others return (doc_id, score)
        dense_docs = [(doc.metadata["doc_id"], score) for doc, score in dense_results]

        all_results = {
            "dense": dense_docs,
            "sparse": sparse_results,
            "fulltext": fulltext_results,
        }

        # --- 3. Apply Reciprocal Rank Fusion (RRF) ---
        fused_scores: Dict[str, float] = {}
        for retriever_name, results in all_results.items():
            for i, (doc_id, _) in enumerate(results):
                rank = i + 1
                if doc_id not in fused_scores:
                    fused_scores[doc_id] = 0.0
                fused_scores[doc_id] += 1.0 / (self.rrf_k + rank)

        # --- 4. Sort documents by their fused scores ---
        reranked_results = sorted(
            fused_scores.items(), key=lambda x: x[1], reverse=True
        )

        # --- 5. Fetch the full documents for the top K results ---
        top_k_doc_ids = [doc_id for doc_id, _ in reranked_results[:self.k]]

        final_documents: List[Document] = []
        # We can fetch the documents from any of our stores.
        # The sparse store keeps them in a convenient map.
        for doc_id in top_k_doc_ids:
            try:
                # We need to ensure the sparse search object has loaded its docs
                if not self.sparse_search._doc_map:
                    self.sparse_search._load_from_disk()
                final_documents.append(self.sparse_search.get_document(doc_id))
            except KeyError:
                # Fallback in case a doc_id somehow doesn't exist in one store
                logger.warning("doc_id %s not found in sparse store, trying fulltext.", doc_id)
                try:
                    final_documents.append(self.fulltext_search.get_document(doc_id))
                except KeyError:
                    logger.error("doc_id %s could not be retrieved from any store.", doc_id)

        return final_documents
