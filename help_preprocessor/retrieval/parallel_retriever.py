"""Parallel and streaming retrieval implementations."""

from __future__ import annotations

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from typing import Dict, List, Iterator, Optional, Callable, Any
from functools import lru_cache
import hashlib

from .base import BaseRetriever, QueryContext, SearchResult


class ParallelRetriever(BaseRetriever):
    """Parallel execution wrapper for multiple retrievers."""
    
    def __init__(
        self, 
        retrievers: Dict[str, BaseRetriever], 
        max_workers: Optional[int] = None,
        timeout_seconds: float = 30.0
    ):
        self.retrievers = retrievers
        self.max_workers = max_workers or min(len(retrievers), 4)
        self.timeout_seconds = timeout_seconds
        self._logger = logging.getLogger(__name__)
        
    def search(self, context: QueryContext) -> List[SearchResult]:
        """Execute search across all retrievers in parallel."""
        if not self.retrievers:
            return []
        
        start_time = time.time()
        results_by_source: Dict[str, List[SearchResult]] = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all search tasks
            future_to_retriever = {
                executor.submit(self._safe_search, name, retriever, context): name
                for name, retriever in self.retrievers.items()
            }
            
            # Collect results with timeout
            for future in as_completed(future_to_retriever, timeout=self.timeout_seconds):
                retriever_name = future_to_retriever[future]
                try:
                    results = future.result(timeout=5.0)  # Per-retriever timeout
                    if results:
                        results_by_source[retriever_name] = results
                        self._logger.debug(
                            "Parallel search completed for %s: %d results", 
                            retriever_name, len(results)
                        )
                except Exception as exc:
                    self._logger.warning(
                        "Parallel search failed for %s: %s", 
                        retriever_name, exc
                    )
        
        # Flatten all results
        all_results = []
        for results in results_by_source.values():
            all_results.extend(results)
        
        execution_time = time.time() - start_time
        self._logger.info(
            "Parallel search completed in %.2fs: %d results from %d retrievers",
            execution_time, len(all_results), len(results_by_source)
        )
        
        return all_results
    
    def _safe_search(self, name: str, retriever: BaseRetriever, context: QueryContext) -> List[SearchResult]:
        """Safely execute search for a single retriever."""
        try:
            return retriever.search(context)
        except Exception as exc:
            self._logger.warning("Safe search failed for %s: %s", name, exc)
            return []
    
    def get_name(self) -> str:
        return f"parallel_retriever({len(self.retrievers)})"


class AsyncRetriever(BaseRetriever):
    """Async-based parallel retriever for better resource utilization."""
    
    def __init__(self, retrievers: Dict[str, BaseRetriever]):
        self.retrievers = retrievers
        self._logger = logging.getLogger(__name__)
    
    def search(self, context: QueryContext) -> List[SearchResult]:
        """Execute async search and return results."""
        return asyncio.run(self.async_search(context))
    
    async def async_search(self, context: QueryContext) -> List[SearchResult]:
        """Execute search across all retrievers asynchronously."""
        if not self.retrievers:
            return []
        
        start_time = time.time()
        
        # Create async tasks
        tasks = [
            self._async_search_wrapper(name, retriever, context)
            for name, retriever in self.retrievers.items()
        ]
        
        # Execute all tasks concurrently
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect successful results
        all_results = []
        successful_retrievers = 0
        
        for i, result in enumerate(results_list):
            retriever_name = list(self.retrievers.keys())[i]
            
            if isinstance(result, Exception):
                self._logger.warning(
                    "Async search failed for %s: %s", 
                    retriever_name, result
                )
            elif isinstance(result, list):
                all_results.extend(result)
                successful_retrievers += 1
                self._logger.debug(
                    "Async search completed for %s: %d results", 
                    retriever_name, len(result)
                )
        
        execution_time = time.time() - start_time
        self._logger.info(
            "Async search completed in %.2fs: %d results from %d/%d retrievers",
            execution_time, len(all_results), successful_retrievers, len(self.retrievers)
        )
        
        return all_results
    
    async def _async_search_wrapper(self, name: str, retriever: BaseRetriever, context: QueryContext) -> List[SearchResult]:
        """Async wrapper for synchronous retriever search."""
        loop = asyncio.get_event_loop()
        
        try:
            # Execute in thread pool to avoid blocking
            return await loop.run_in_executor(None, retriever.search, context)
        except Exception as exc:
            self._logger.warning("Async search wrapper failed for %s: %s", name, exc)
            return []
    
    def get_name(self) -> str:
        return f"async_retriever({len(self.retrievers)})"


class StreamingRetriever(BaseRetriever):
    """Memory-efficient streaming retriever."""
    
    def __init__(
        self, 
        retrievers: Dict[str, BaseRetriever],
        batch_size: int = 5,
        max_total_results: int = 100
    ):
        self.retrievers = retrievers
        self.batch_size = batch_size
        self.max_total_results = max_total_results
        self._logger = logging.getLogger(__name__)
    
    def search(self, context: QueryContext) -> List[SearchResult]:
        """Execute streaming search and return limited results."""
        results = list(self.stream_search(context))
        return results[:self.max_total_results]
    
    def stream_search(self, context: QueryContext) -> Iterator[SearchResult]:
        """Stream search results to minimize memory usage."""
        total_results = 0
        
        for name, retriever in self.retrievers.items():
            if total_results >= self.max_total_results:
                break
                
            try:
                # Get results from retriever
                retriever_results = retriever.search(context)
                
                # Stream results in batches
                for i in range(0, len(retriever_results), self.batch_size):
                    if total_results >= self.max_total_results:
                        break
                        
                    batch = retriever_results[i:i + self.batch_size]
                    for result in batch:
                        if total_results >= self.max_total_results:
                            break
                        yield result
                        total_results += 1
                        
                self._logger.debug(
                    "Streaming search completed for %s: %d results yielded", 
                    name, min(len(retriever_results), self.max_total_results - (total_results - len(batch)))
                )
                
            except Exception as exc:
                self._logger.warning("Streaming search failed for %s: %s", name, exc)
                continue
        
        self._logger.info("Streaming search completed: %d total results", total_results)
    
    def get_name(self) -> str:
        return f"streaming_retriever({len(self.retrievers)})"


class CachedRetriever(BaseRetriever):
    """LRU cache wrapper for retriever results."""
    
    def __init__(
        self, 
        base_retriever: BaseRetriever, 
        cache_size: int = 128,
        cache_ttl_seconds: int = 3600
    ):
        self.base_retriever = base_retriever
        self.cache_size = cache_size
        self.cache_ttl_seconds = cache_ttl_seconds
        self._logger = logging.getLogger(__name__)
        
        # Create cached search function with string-based caching
        self._cache = {}
        self._cache_timestamps = {}
        self._max_cache_size = cache_size
        self._cache_hits = 0
        self._cache_misses = 0
    
    def search(self, context: QueryContext) -> List[SearchResult]:
        """Execute cached search."""
        cache_key = self._create_cache_key(context)
        current_time = time.time()
        
        # Check cache hit
        if cache_key in self._cache:
            timestamp = self._cache_timestamps.get(cache_key, 0)
            if current_time - timestamp <= self.cache_ttl_seconds:
                self._cache_hits += 1
                self._logger.debug("Cache hit for query: %s", context.query[:50])
                return self._cache[cache_key]
            else:
                # Cache expired
                del self._cache[cache_key]
                del self._cache_timestamps[cache_key]
                self._logger.debug("Cache expired for query: %s", context.query[:50])
        
        # Cache miss
        self._cache_misses += 1
        
        # Cache miss - execute search
        try:
            results = self.base_retriever.search(context)
            
            # Store in cache (with size limit)
            if len(self._cache) >= self._max_cache_size:
                # Remove oldest entry
                oldest_key = min(self._cache_timestamps.keys(), 
                               key=lambda k: self._cache_timestamps[k])
                del self._cache[oldest_key]
                del self._cache_timestamps[oldest_key]
            
            self._cache[cache_key] = results
            self._cache_timestamps[cache_key] = current_time
            
            self._logger.debug("Cache store for query: %s", context.query[:50])
            return results
            
        except Exception as exc:
            self._logger.warning("Cached search failed: %s", exc)
            return []
    
    def _create_cache_key(self, context: QueryContext) -> str:
        """Create cache key from query context."""
        search_types_str = ",".join(context.search_types) if context.search_types else "all"
        filters_str = str(sorted(context.filters.items())) if context.filters else "none"
        key_data = f"{context.query}|{context.top_k}|{search_types_str}|{context.fusion_method}|{filters_str}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _search_with_ttl(self, cache_key: str, context: QueryContext) -> tuple[List[SearchResult], float]:
        """Search with timestamp for TTL checking."""
        results = self.base_retriever.search(context)
        timestamp = time.time()
        return results, timestamp
    
    def get_cache_info(self) -> dict:
        """Get cache statistics."""
        total_requests = getattr(self, '_cache_hits', 0) + getattr(self, '_cache_misses', 0)
        hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0.0
        
        return {
            "hits": getattr(self, '_cache_hits', 0),
            "misses": getattr(self, '_cache_misses', 0),
            "maxsize": self._max_cache_size,
            "currsize": len(self._cache),
            "hit_rate": hit_rate
        }
    
    def clear_cache(self):
        """Clear the cache."""
        self._cache.clear()
        self._cache_timestamps.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        self._logger.info("Cache cleared for %s", self.base_retriever.get_name())
    
    def get_name(self) -> str:
        return f"cached_{self.base_retriever.get_name()}"


class PerformanceMonitoringRetriever(BaseRetriever):
    """Retriever wrapper that monitors performance metrics."""
    
    def __init__(self, base_retriever: BaseRetriever):
        self.base_retriever = base_retriever
        self.metrics = {
            "total_searches": 0,
            "total_time": 0.0,
            "total_results": 0,
            "error_count": 0,
            "average_time": 0.0,
            "average_results": 0.0
        }
        self._logger = logging.getLogger(__name__)
    
    def search(self, context: QueryContext) -> List[SearchResult]:
        """Execute search with performance monitoring."""
        start_time = time.time()
        
        try:
            results = self.base_retriever.search(context)
            
            # Update success metrics
            execution_time = time.time() - start_time
            self.metrics["total_searches"] += 1
            self.metrics["total_time"] += execution_time
            self.metrics["total_results"] += len(results)
            
            # Calculate averages
            self.metrics["average_time"] = self.metrics["total_time"] / self.metrics["total_searches"]
            self.metrics["average_results"] = self.metrics["total_results"] / self.metrics["total_searches"]
            
            self._logger.debug(
                "Search completed in %.3fs: %d results (avg: %.3fs, %.1f results)",
                execution_time, len(results), 
                self.metrics["average_time"], self.metrics["average_results"]
            )
            
            return results
            
        except Exception as exc:
            # Update error metrics
            self.metrics["error_count"] += 1
            self._logger.error("Monitored search failed: %s", exc)
            raise
    
    def get_performance_report(self) -> dict:
        """Get detailed performance report."""
        return {
            **self.metrics,
            "error_rate": self.metrics["error_count"] / max(1, self.metrics["total_searches"]),
            "retriever_name": self.base_retriever.get_name()
        }
    
    def reset_metrics(self):
        """Reset all metrics."""
        for key in self.metrics:
            self.metrics[key] = 0 if isinstance(self.metrics[key], int) else 0.0
        self._logger.info("Metrics reset for %s", self.base_retriever.get_name())
    
    def get_name(self) -> str:
        return f"monitored_{self.base_retriever.get_name()}"
