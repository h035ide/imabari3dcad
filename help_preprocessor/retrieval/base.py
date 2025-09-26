"""Base classes for retrieval components."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class SearchResult:
    """Individual search result with metadata."""
    
    id: str
    content: str
    score: float
    source: str  # "dense", "sparse", "fulltext", "graph"
    metadata: dict[str, Any]
    
    def __post_init__(self):
        # Normalize score to 0-1 range if needed
        if self.score < 0:
            self.score = 0.0
        elif self.score > 1:
            self.score = min(self.score, 10.0) / 10.0


@dataclass
class QueryContext:
    """Context information for search queries."""
    
    query: str
    filters: Optional[dict[str, Any]] = None
    top_k: int = 5
    search_types: Optional[List[str]] = None  # ["dense", "sparse", "fulltext", "graph"]
    fusion_method: str = "reciprocal_rank"  # "reciprocal_rank", "weighted_sum", "borda_count"
    
    def __post_init__(self):
        """Validate and normalize query context."""
        # Basic validation
        if not self.query or not self.query.strip():
            raise ValueError("Query cannot be empty")
        
        # Normalize query
        self.query = self.query.strip()
        
        # Validate top_k
        if self.top_k <= 0:
            raise ValueError("top_k must be positive")
        elif self.top_k > 100:
            self.top_k = 100  # Clamp to maximum
        
        # Validate search_types
        if self.search_types:
            valid_types = {"dense", "sparse", "fulltext", "graph"}
            invalid_types = set(self.search_types) - valid_types
            if invalid_types:
                raise ValueError(f"Invalid search_types: {invalid_types}")
        
        # Validate fusion_method
        valid_fusion = {"reciprocal_rank", "weighted_sum", "borda_count", "adaptive"}
        if self.fusion_method not in valid_fusion:
            self.fusion_method = "reciprocal_rank"  # Default fallback


class BaseRetriever(ABC):
    """Abstract base class for all retrieval components."""
    
    @abstractmethod
    def search(self, context: QueryContext) -> List[SearchResult]:
        """Execute search and return results."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return retriever name for identification."""
        pass


class BaseResultFusion(ABC):
    """Abstract base class for result fusion strategies."""
    
    @abstractmethod
    def fuse_results(
        self, 
        results_by_source: dict[str, List[SearchResult]], 
        context: QueryContext
    ) -> List[SearchResult]:
        """Combine results from multiple retrievers."""
        pass
