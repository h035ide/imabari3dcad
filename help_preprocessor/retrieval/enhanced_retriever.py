"""Enhanced retriever with parallel processing, caching, and streaming."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Iterator

from .base import BaseRetriever, QueryContext, SearchResult
from .hybrid_retriever import HybridRetriever, HybridRetrieverConfig
from .parallel_retriever import (
    ParallelRetriever, AsyncRetriever, StreamingRetriever, 
    CachedRetriever, PerformanceMonitoringRetriever
)


class EnhancedHybridRetriever(BaseRetriever):
    """Enhanced hybrid retriever with parallel processing and caching."""
    
    def __init__(
        self, 
        config: HybridRetrieverConfig,
        enable_parallel: bool = True,
        enable_caching: bool = True,
        enable_monitoring: bool = True,
        cache_size: int = 128,
        cache_ttl_seconds: int = 3600,
        parallel_timeout: float = 30.0
    ):
        self.config = config
        self.enable_parallel = enable_parallel
        self.enable_caching = enable_caching
        self.enable_monitoring = enable_monitoring
        self.cache_size = cache_size
        self.cache_ttl_seconds = cache_ttl_seconds
        self.parallel_timeout = parallel_timeout
        
        # Initialize logger first
        self._logger = logging.getLogger(__name__)
        
        # Create base hybrid retriever
        self.base_retriever = HybridRetriever(config)
        
        # Wrap with enhancements
        self.enhanced_retriever = self._build_enhanced_retriever()
    
    def _build_enhanced_retriever(self) -> BaseRetriever:
        """Build enhanced retriever with all optimizations."""
        retriever = self.base_retriever
        
        # Add performance monitoring
        if self.enable_monitoring:
            retriever = PerformanceMonitoringRetriever(retriever)
            self._logger.debug("Performance monitoring enabled")
        
        # Add caching
        if self.enable_caching:
            retriever = CachedRetriever(
                retriever, 
                cache_size=self.cache_size,
                cache_ttl_seconds=self.cache_ttl_seconds
            )
            self._logger.debug("Caching enabled: size=%d, ttl=%ds", 
                             self.cache_size, self.cache_ttl_seconds)
        
        return retriever
    
    def search(self, context: QueryContext) -> List[SearchResult]:
        """Execute enhanced search with all optimizations."""
        return self.enhanced_retriever.search(context)
    
    def stream_search(self, context: QueryContext, batch_size: int = 5) -> Iterator[SearchResult]:
        """Stream search results for memory efficiency."""
        # Create streaming version of the retriever
        if hasattr(self.base_retriever, 'retrievers'):
            streaming_retriever = StreamingRetriever(
                retrievers=self.base_retriever.retrievers,
                batch_size=batch_size,
                max_total_results=context.top_k * 2
            )
            yield from streaming_retriever.stream_search(context)
        else:
            # Fallback to regular search
            results = self.search(context)
            for result in results:
                yield result
    
    def get_performance_report(self) -> Dict:
        """Get performance statistics."""
        report = {
            "retriever_type": "enhanced_hybrid",
            "parallel_enabled": self.enable_parallel,
            "caching_enabled": self.enable_caching,
            "monitoring_enabled": self.enable_monitoring
        }
        
        # Get monitoring data if available
        if self.enable_monitoring and isinstance(self.enhanced_retriever, PerformanceMonitoringRetriever):
            report.update(self.enhanced_retriever.get_performance_report())
        
        # Get cache statistics if available
        if self.enable_caching:
            current = self.enhanced_retriever
            while hasattr(current, 'base_retriever'):
                if isinstance(current, CachedRetriever):
                    report["cache_info"] = current.get_cache_info()
                    break
                current = current.base_retriever
        
        return report
    
    def clear_cache(self):
        """Clear all caches."""
        if self.enable_caching:
            current = self.enhanced_retriever
            while hasattr(current, 'base_retriever'):
                if isinstance(current, CachedRetriever):
                    current.clear_cache()
                    break
                current = current.base_retriever
    
    def get_name(self) -> str:
        return "enhanced_hybrid_retriever"


class AdaptiveRetriever(BaseRetriever):
    """Adaptive retriever that chooses optimal strategy based on query characteristics."""
    
    def __init__(self, base_retriever: EnhancedHybridRetriever):
        self.base_retriever = base_retriever
        self._logger = logging.getLogger(__name__)
    
    def search(self, context: QueryContext) -> List[SearchResult]:
        """Execute adaptive search based on query characteristics."""
        strategy = self._analyze_query_strategy(context)
        
        if strategy == "streaming":
            # Use streaming for large result sets
            results = list(self.base_retriever.stream_search(context, batch_size=3))
            return results[:context.top_k]
        elif strategy == "cached":
            # Use cached search for common queries
            return self.base_retriever.search(context)
        else:
            # Default parallel search
            return self.base_retriever.search(context)
    
    def _analyze_query_strategy(self, context: QueryContext) -> str:
        """Analyze query to determine optimal search strategy."""
        query = context.query.lower()
        
        # Large result set queries - use streaming
        if context.top_k > 20 or any(word in query for word in ["全て", "すべて", "一覧", "リスト"]):
            return "streaming"
        
        # Common/simple queries - use caching
        if len(query.split()) <= 3 or any(word in query for word in ["とは", "について", "方法", "手順"]):
            return "cached"
        
        # Default to parallel
        return "parallel"
    
    def get_name(self) -> str:
        return "adaptive_retriever"


def create_enhanced_retrieval_system(
    config: HybridRetrieverConfig,
    performance_mode: str = "balanced"  # "speed", "memory", "balanced"
) -> Dict[str, BaseRetriever]:
    """Factory function to create optimized retrieval system."""
    
    # Configure based on performance mode
    if performance_mode == "speed":
        enhanced_config = {
            "enable_parallel": True,
            "enable_caching": True,
            "enable_monitoring": False,
            "cache_size": 256,
            "cache_ttl_seconds": 7200,
            "parallel_timeout": 15.0
        }
    elif performance_mode == "memory":
        enhanced_config = {
            "enable_parallel": False,
            "enable_caching": False,
            "enable_monitoring": True,
            "cache_size": 32,
            "cache_ttl_seconds": 1800,
            "parallel_timeout": 60.0
        }
    else:  # balanced
        enhanced_config = {
            "enable_parallel": True,
            "enable_caching": True,
            "enable_monitoring": True,
            "cache_size": 128,
            "cache_ttl_seconds": 3600,
            "parallel_timeout": 30.0
        }
    
    # Create enhanced retriever
    enhanced_retriever = EnhancedHybridRetriever(config, **enhanced_config)
    
    # Create adaptive wrapper
    adaptive_retriever = AdaptiveRetriever(enhanced_retriever)
    
    # Create streaming-only version
    if hasattr(enhanced_retriever.base_retriever, 'retrievers'):
        streaming_retriever = StreamingRetriever(
            retrievers=enhanced_retriever.base_retriever.retrievers,
            batch_size=5,
            max_total_results=100
        )
    else:
        streaming_retriever = enhanced_retriever
    
    return {
        "enhanced": enhanced_retriever,
        "adaptive": adaptive_retriever,
        "streaming": streaming_retriever,
        "base": enhanced_retriever.base_retriever,
        "performance_mode": performance_mode
    }
