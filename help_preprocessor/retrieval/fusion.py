"""Result fusion strategies for combining multiple search results."""

from __future__ import annotations

from typing import Dict, List
import math
from collections import defaultdict

from .base import BaseResultFusion, SearchResult, QueryContext


class ReciprocalRankFusion(BaseResultFusion):
    """Reciprocal Rank Fusion (RRF) for combining search results."""
    
    def __init__(self, k: int = 60):
        self.k = k  # RRF parameter
        
    def fuse_results(
        self, 
        results_by_source: Dict[str, List[SearchResult]], 
        context: QueryContext
    ) -> List[SearchResult]:
        """Combine results using Reciprocal Rank Fusion."""
        
        # Collect all unique results
        all_results: Dict[str, SearchResult] = {}
        rrf_scores: Dict[str, float] = defaultdict(float)
        
        for source, results in results_by_source.items():
            for rank, result in enumerate(results, 1):
                result_id = result.id
                
                # Store the result (first occurrence wins for metadata)
                if result_id not in all_results:
                    all_results[result_id] = result
                    
                # Add RRF score: 1 / (k + rank)
                rrf_scores[result_id] += 1.0 / (self.k + rank)
        
        # Create fused results with RRF scores
        fused_results = []
        for result_id, rrf_score in rrf_scores.items():
            result = all_results[result_id]
            
            # Create new result with fused score
            fused_result = SearchResult(
                id=result.id,
                content=result.content,
                score=rrf_score,
                source="fusion_rrf",
                metadata={
                    **result.metadata,
                    "original_score": result.score,
                    "original_source": result.source,
                    "rrf_score": rrf_score,
                    "fusion_method": "reciprocal_rank"
                }
            )
            fused_results.append(fused_result)
            
        # Sort by RRF score and return top-k
        fused_results.sort(key=lambda x: x.score, reverse=True)
        return fused_results[:context.top_k]


class WeightedSumFusion(BaseResultFusion):
    """Weighted sum fusion with configurable source weights."""
    
    def __init__(self, source_weights: Dict[str, float] = None):
        self.source_weights = source_weights or {
            "dense": 1.0,
            "sparse_tfidf": 0.8,
            "sparse_bm25": 0.8,
            "fulltext_whoosh": 0.6,
            "fulltext_elasticsearch": 0.7,
            "graph_neo4j": 0.5,
            "graph_path": 0.3
        }
        
    def fuse_results(
        self,
        results_by_source: Dict[str, List[SearchResult]],
        context: QueryContext
    ) -> List[SearchResult]:
        """Combine results using weighted sum of normalized scores."""
        
        # Normalize scores within each source
        normalized_results: Dict[str, List[SearchResult]] = {}
        
        for source, results in results_by_source.items():
            if not results:
                continue
                
            max_score = max(r.score for r in results)
            min_score = min(r.score for r in results)
            score_range = max_score - min_score if max_score > min_score else 1.0
            
            normalized = []
            for result in results:
                normalized_score = (result.score - min_score) / score_range
                
                new_result = SearchResult(
                    id=result.id,
                    content=result.content,
                    score=normalized_score,
                    source=result.source,
                    metadata=result.metadata
                )
                normalized.append(new_result)
                
            normalized_results[source] = normalized
        
        # Combine with weighted sum
        all_results: Dict[str, SearchResult] = {}
        weighted_scores: Dict[str, float] = defaultdict(float)
        
        for source, results in normalized_results.items():
            weight = self.source_weights.get(source, 1.0)
            
            for result in results:
                result_id = result.id
                
                if result_id not in all_results:
                    all_results[result_id] = result
                    
                weighted_scores[result_id] += result.score * weight
        
        # Create fused results
        fused_results = []
        for result_id, weighted_score in weighted_scores.items():
            result = all_results[result_id]
            
            fused_result = SearchResult(
                id=result.id,
                content=result.content,
                score=weighted_score,
                source="fusion_weighted",
                metadata={
                    **result.metadata,
                    "original_score": result.score,
                    "original_source": result.source,
                    "weighted_score": weighted_score,
                    "fusion_method": "weighted_sum"
                }
            )
            fused_results.append(fused_result)
            
        # Sort and return top-k
        fused_results.sort(key=lambda x: x.score, reverse=True)
        return fused_results[:context.top_k]


class BordaCountFusion(BaseResultFusion):
    """Borda Count fusion based on ranking positions."""
    
    def fuse_results(
        self,
        results_by_source: Dict[str, List[SearchResult]],
        context: QueryContext
    ) -> List[SearchResult]:
        """Combine results using Borda count method."""
        
        all_results: Dict[str, SearchResult] = {}
        borda_scores: Dict[str, int] = defaultdict(int)
        
        for source, results in results_by_source.items():
            n_results = len(results)
            
            for rank, result in enumerate(results):
                result_id = result.id
                
                if result_id not in all_results:
                    all_results[result_id] = result
                    
                # Borda score: n - rank (higher is better)
                borda_scores[result_id] += n_results - rank
        
        # Create fused results
        fused_results = []
        max_borda = max(borda_scores.values()) if borda_scores else 1
        
        for result_id, borda_score in borda_scores.items():
            result = all_results[result_id]
            normalized_score = borda_score / max_borda
            
            fused_result = SearchResult(
                id=result.id,
                content=result.content,
                score=normalized_score,
                source="fusion_borda",
                metadata={
                    **result.metadata,
                    "original_score": result.score,
                    "original_source": result.source,
                    "borda_score": borda_score,
                    "normalized_borda": normalized_score,
                    "fusion_method": "borda_count"
                }
            )
            fused_results.append(fused_result)
            
        # Sort and return top-k
        fused_results.sort(key=lambda x: x.score, reverse=True)
        return fused_results[:context.top_k]


class AdaptiveFusion(BaseResultFusion):
    """Adaptive fusion that chooses strategy based on query characteristics."""
    
    def __init__(self):
        self.rrf_fusion = ReciprocalRankFusion()
        self.weighted_fusion = WeightedSumFusion()
        self.borda_fusion = BordaCountFusion()
        
    def _analyze_query(self, context: QueryContext) -> str:
        """Analyze query to choose best fusion strategy."""
        query = context.query.lower()
        
        # Short queries: prefer RRF
        if len(query.split()) <= 2:
            return "rrf"
            
        # Technical queries: prefer weighted sum
        technical_terms = ["設定", "コマンド", "機能", "操作", "エラー", "問題"]
        if any(term in query for term in technical_terms):
            return "weighted"
            
        # Default to Borda count for balanced results
        return "borda"
    
    def fuse_results(
        self,
        results_by_source: Dict[str, List[SearchResult]],
        context: QueryContext
    ) -> List[SearchResult]:
        """Choose and apply best fusion strategy."""
        
        strategy = self._analyze_query(context)
        
        if strategy == "rrf":
            return self.rrf_fusion.fuse_results(results_by_source, context)
        elif strategy == "weighted":
            return self.weighted_fusion.fuse_results(results_by_source, context)
        else:
            return self.borda_fusion.fuse_results(results_by_source, context)
