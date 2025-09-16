# mycode/sparse_vector_db.py
"""
This module provides a sparse vector search engine using scikit-learn's
TF-IDF implementation. It's a simple, effective baseline for keyword-based search.
"""
import pickle
from pathlib import Path
from typing import List, Tuple, Dict, Any

import joblib
from langchain_core.documents import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# --- Constants ---

DEFAULT_SPARSE_INDEX_DIR = Path("data/sparse_index")
VECTORIZER_FILE = "tfidf_vectorizer.joblib"
DOCS_FILE = "documents.pkl"

# --- Sparse Vector Search Engine ---

class SparseVectorSearch:
    """
    A wrapper class for a TF-IDF based sparse vector search engine.
    """
    def __init__(self, index_dir: Path = DEFAULT_SPARSE_INDEX_DIR):
        self.index_dir = index_dir
        self.vectorizer: TfidfVectorizer = None
        self.tfidf_matrix = None
        self.documents: List[Document] = []
        self._doc_map: Dict[str, Document] = {}

    def _load_from_disk(self):
        """Loads the vectorizer and documents from the index directory."""
        if not self.index_dir.exists():
            raise FileNotFoundError(f"Sparse index directory not found at {self.index_dir}. Please run ingestion.")

        vectorizer_path = self.index_dir / VECTORIZER_FILE
        docs_path = self.index_dir / DOCS_FILE

        if not vectorizer_path.exists() or not docs_path.exists():
            raise FileNotFoundError("Vectorizer or documents file missing from index directory.")

        self.vectorizer, self.tfidf_matrix = joblib.load(vectorizer_path)
        with open(docs_path, 'rb') as f:
            self.documents = pickle.load(f)

        self._doc_map = {doc.metadata["doc_id"]: doc for doc in self.documents}


    def index_documents(self, documents: List[Document], force_recreate: bool = True):
        """
        Creates or overwrites a sparse vector index with the given documents.

        Args:
            documents: A list of LangChain Document objects.
            force_recreate: If True, deletes the existing index before creating a new one.
        """
        if self.index_dir.exists() and force_recreate:
            import shutil
            shutil.rmtree(self.index_dir)

        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.documents = documents
        self._doc_map = {doc.metadata["doc_id"]: doc for doc in self.documents}

        # We need a corpus of text to fit the vectorizer
        corpus = [doc.page_content for doc in documents]

        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

        # Save the fitted vectorizer and the document list
        joblib.dump((self.vectorizer, self.tfidf_matrix), self.index_dir / VECTORIZER_FILE)
        with open(self.index_dir / DOCS_FILE, 'wb') as f:
            pickle.dump(self.documents, f)

        print(f"✔ Sparse vector index created with {len(documents)} documents at: {self.index_dir}")

    def search(self, query_text: str, limit: int = 10) -> List[Tuple[str, float]]:
        """
        Searches the index for the given query text using cosine similarity.

        Args:
            query_text: The string to search for.
            limit: The maximum number of results to return.

        Returns:
            A list of tuples, where each tuple contains the doc_id and the cosine similarity score.
        """
        if self.vectorizer is None or self.tfidf_matrix is None:
            self._load_from_disk()

        query_vector = self.vectorizer.transform([query_text])

        # Compute cosine similarity between the query and all documents
        scores = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

        # Get the top N results
        # We use argpartition for efficiency if N is much smaller than the total number of docs
        if limit < len(self.documents):
            top_k_indices = np.argpartition(scores, -limit)[-limit:]
        else:
            top_k_indices = np.argsort(scores)[::-1]

        # Sort the top k results by score
        results = sorted([(i, scores[i]) for i in top_k_indices], key=lambda x: x[1], reverse=True)

        # Map back to doc_ids
        return [(self.documents[i].metadata["doc_id"], score) for i, score in results]

    def get_document(self, doc_id: str) -> Document:
        """Retrieves a document by its doc_id."""
        if not self._doc_map:
            self._load_from_disk()

        doc = self._doc_map.get(doc_id)
        if doc is None:
            raise KeyError(f"Document with doc_id '{doc_id}' not found in sparse vector index.")
        return doc
