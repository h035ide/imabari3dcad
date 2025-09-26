"""Sparse vector retrieval using TF-IDF and BM25."""

from __future__ import annotations

import pickle
import re
from collections import Counter
from pathlib import Path
from typing import List, Optional

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .base import BaseRetriever, QueryContext, SearchResult


class SparseVectorRetriever(BaseRetriever):
    """TF-IDF based sparse vector retrieval."""
    
    def __init__(
        self, 
        vectorizer_path: Path,
        documents_path: Path,
        index_name: str = "tfidf"
    ):
        self.vectorizer_path = vectorizer_path
        self.documents_path = documents_path
        self.index_name = index_name
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._documents: Optional[List[dict]] = None
        self._doc_vectors: Optional[np.ndarray] = None
        
    def _load_index(self) -> None:
        """Load TF-IDF vectorizer and documents."""
        if self._vectorizer is None:
            self._vectorizer = joblib.load(self.vectorizer_path)
            
        if self._documents is None:
            with open(self.documents_path, 'rb') as f:
                self._documents = pickle.load(f)
                
        if self._doc_vectors is None:
            # Pre-compute document vectors for efficiency
            doc_texts = [doc.get('content', '') for doc in self._documents]
            self._doc_vectors = self._vectorizer.transform(doc_texts)
    
    def search(self, context: QueryContext) -> List[SearchResult]:
        """Search using TF-IDF sparse vectors."""
        self._load_index()
        
        if not self._vectorizer or not self._documents:
            return []
            
        # Transform query to sparse vector
        query_vector = self._vectorizer.transform([context.query])
        
        # Compute similarities
        similarities = cosine_similarity(query_vector, self._doc_vectors).flatten()
        
        # Get top-k results
        top_indices = np.argsort(similarities)[::-1][:context.top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Only return relevant results
                doc = self._documents[idx]
                result = SearchResult(
                    id=doc.get('id', f'sparse_{idx}'),
                    content=doc.get('content', ''),
                    score=float(similarities[idx]),
                    source="sparse_tfidf",
                    metadata={
                        "index_name": self.index_name,
                        "original_score": float(similarities[idx]),
                        "section_id": doc.get('section_id'),
                        "title": doc.get('title'),
                        **doc.get('metadata', {})
                    }
                )
                results.append(result)
                
        return results
    
    def get_name(self) -> str:
        return f"sparse_tfidf_{self.index_name}"


class BM25Retriever(BaseRetriever):
    """BM25-based sparse retrieval (simplified implementation)."""
    
    def __init__(
        self,
        documents_path: Path,
        k1: float = 1.2,
        b: float = 0.75
    ):
        self.documents_path = documents_path
        self.k1 = k1  # Term frequency saturation parameter
        self.b = b    # Length normalization parameter
        self._documents: Optional[List[dict]] = None
        self._doc_lengths: Optional[List[int]] = None
        self._avg_doc_length: Optional[float] = None
        self._vocab: Optional[dict[str, int]] = None
        self._idf: Optional[dict[str, float]] = None
        
    def _load_documents(self) -> None:
        """Load and preprocess documents for BM25."""
        if self._documents is not None:
            return
            
        with open(self.documents_path, 'rb') as f:
            self._documents = pickle.load(f)
            
        # Preprocess documents
        
        doc_texts = []
        doc_lengths = []
        vocab_counter = Counter()
        
        for doc in self._documents:
            text = doc.get('content', '').lower()
            # Simple tokenization (can be improved with proper tokenizer)
            tokens = re.findall(r'\w+', text)
            doc_texts.append(tokens)
            doc_lengths.append(len(tokens))
            vocab_counter.update(set(tokens))  # Document frequency
            
        self._doc_texts = doc_texts
        self._doc_lengths = doc_lengths
        self._avg_doc_length = sum(doc_lengths) / len(doc_lengths)
        
        # Build vocabulary and compute IDF
        self._vocab = {word: idx for idx, word in enumerate(vocab_counter.keys())}
        import math
        N = len(self._documents)
        self._idf = {
            word: math.log((N - freq + 0.5) / (freq + 0.5))
            for word, freq in vocab_counter.items()
        }
    
    def _bm25_score(self, query_tokens: List[str], doc_idx: int) -> float:
        """Calculate BM25 score for a document."""
        if not self._doc_texts or not self._idf:
            return 0.0
            
        doc_tokens = self._doc_texts[doc_idx]
        doc_length = self._doc_lengths[doc_idx]
        
        score = 0.0
        doc_token_counts = Counter(doc_tokens)
        
        for term in query_tokens:
            if term in self._idf:
                tf = doc_token_counts.get(term, 0)
                idf = self._idf[term]
                
                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (
                    1 - self.b + self.b * doc_length / self._avg_doc_length
                )
                score += idf * (numerator / denominator)
                
        return score
    
    def search(self, context: QueryContext) -> List[SearchResult]:
        """Search using BM25 scoring."""
        self._load_documents()
        
        if not self._documents:
            return []
            
        # Tokenize query
        query_tokens = re.findall(r'\w+', context.query.lower())
        
        # Calculate BM25 scores for all documents
        scores = []
        for doc_idx in range(len(self._documents)):
            score = self._bm25_score(query_tokens, doc_idx)
            scores.append((doc_idx, score))
            
        # Sort by score and get top-k
        scores.sort(key=lambda x: x[1], reverse=True)
        top_results = scores[:context.top_k]
        
        results = []
        max_score = max(score for _, score in top_results) if top_results else 1.0
        
        for doc_idx, score in top_results:
            if score > 0:
                doc = self._documents[doc_idx]
                normalized_score = score / max_score if max_score > 0 else 0.0
                
                result = SearchResult(
                    id=doc.get('id', f'bm25_{doc_idx}'),
                    content=doc.get('content', ''),
                    score=normalized_score,
                    source="sparse_bm25",
                    metadata={
                        "bm25_score": score,
                        "normalized_score": normalized_score,
                        "section_id": doc.get('section_id'),
                        "title": doc.get('title'),
                        **doc.get('metadata', {})
                    }
                )
                results.append(result)
                
        return results
    
    def get_name(self) -> str:
        return "sparse_bm25"
