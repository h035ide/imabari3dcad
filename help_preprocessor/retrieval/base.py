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
