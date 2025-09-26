"""Input validation and configuration checking utilities."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from .base import QueryContext
from .hybrid_retriever import HybridRetrieverConfig


class ValidationError(Exception):
    """Base exception for validation errors."""
    pass


class QueryValidationError(ValidationError):
    """Query validation error."""
    pass


class ConfigValidationError(ValidationError):
    """Configuration validation error."""
    pass


def validate_query(query: str) -> str:
    """Validate and sanitize user query."""
    if not query or not query.strip():
        raise QueryValidationError("Query cannot be empty")
    
    # Length limit
    if len(query) > 10000:
        raise QueryValidationError("Query too long (max 10000 characters)")
    
    # Remove dangerous patterns
    dangerous_patterns = [
        r"<script[^>]*>.*?</script>",  # Script injection
        r"javascript:",               # JavaScript URLs
        r"data:text/html",           # Data URLs
    ]
    
    cleaned_query = query.strip()
    for pattern in dangerous_patterns:
        cleaned_query = re.sub(pattern, "", cleaned_query, flags=re.IGNORECASE | re.DOTALL)
    
    return cleaned_query


def validate_query_context(context: QueryContext) -> List[str]:
    """Validate QueryContext and return error messages."""
    errors = []
    
    # Validate query
    try:
        validate_query(context.query)
    except QueryValidationError as e:
        errors.append(str(e))
    
    # Validate top_k
    if context.top_k <= 0:
        errors.append("top_k must be positive")
    elif context.top_k > 100:
        errors.append("top_k too large (max 100)")
    
    # Validate search_types
    if context.search_types:
        valid_types = {"dense", "sparse", "fulltext", "graph"}
        invalid_types = set(context.search_types) - valid_types
        if invalid_types:
            errors.append(f"Invalid search_types: {invalid_types}")
    
    # Validate fusion_method
    valid_fusion = {"rrf", "weighted", "borda", "adaptive"}
    if context.fusion_method not in valid_fusion:
        errors.append(f"Invalid fusion_method: {context.fusion_method}")
    
    return errors


def validate_hybrid_config(config: HybridRetrieverConfig) -> List[str]:
    """Validate HybridRetrieverConfig and return error messages."""
    errors = []
    
    # Check if any search type is enabled
    if not any([
        config.enable_dense,
        config.enable_sparse,
        config.enable_fulltext,
        config.enable_graph
    ]):
        errors.append("At least one search type must be enabled")
    
    # Validate dense search config
    if config.enable_dense and not config.chroma_config:
        errors.append("Dense search enabled but chroma_config is None")
    
    # Validate sparse search config
    if config.enable_sparse and not (config.tfidf_config or config.bm25_config):
        errors.append("Sparse search enabled but no sparse config provided")
    
    # Validate fulltext search config
    if config.enable_fulltext and not (config.whoosh_config or config.elasticsearch_config):
        errors.append("Fulltext search enabled but no fulltext config provided")
    
    # Validate graph search config
    if config.enable_graph and not config.neo4j_config:
        errors.append("Graph search enabled but neo4j_config is None")
    
    # Validate fusion method
    valid_fusion = {"rrf", "weighted", "borda", "adaptive"}
    if config.fusion_method not in valid_fusion:
        errors.append(f"Invalid fusion_method: {config.fusion_method}")
    
    # Validate RRF parameter
    if config.fusion_method == "rrf" and config.rrf_k <= 0:
        errors.append("rrf_k must be positive")
    
    # Validate source weights
    if config.fusion_method == "weighted" and config.source_weights:
        for source, weight in config.source_weights.items():
            if weight < 0:
                errors.append(f"Negative weight for {source}: {weight}")
    
    return errors


def validate_data_files(config: HybridRetrieverConfig) -> List[str]:
    """Validate required data files exist and are accessible."""
    errors = []
    
    # Check TF-IDF files
    if config.tfidf_config:
        if not config.tfidf_config.vectorizer_path.exists():
            errors.append(f"TF-IDF vectorizer file not found: {config.tfidf_config.vectorizer_path}")
        if not config.tfidf_config.documents_path.exists():
            errors.append(f"TF-IDF documents file not found: {config.tfidf_config.documents_path}")
    
    # Check BM25 files
    if config.bm25_config:
        if not config.bm25_config.documents_path.exists():
            errors.append(f"BM25 documents file not found: {config.bm25_config.documents_path}")
    
    # Check Whoosh index
    if config.whoosh_config:
        if not config.whoosh_config.index_dir.exists():
            errors.append(f"Whoosh index directory not found: {config.whoosh_config.index_dir}")
    
    # Check Chroma persistence directory
    if config.chroma_config and config.chroma_config.persist_directory:
        persist_dir = Path(config.chroma_config.persist_directory)
        if not persist_dir.exists():
            errors.append(f"Chroma persist directory not found: {persist_dir}")
    
    return errors


def safe_validate_and_create_context(
    query: str,
    top_k: int = 5,
    search_types: Optional[List[str]] = None,
    fusion_method: str = "adaptive",
    filters: Optional[dict] = None
) -> QueryContext:
    """Safely create and validate QueryContext."""
    
    # Validate and clean query
    clean_query = validate_query(query)
    
    # Create context
    context = QueryContext(
        query=clean_query,
        top_k=max(1, min(top_k, 100)),  # Clamp to valid range
        search_types=search_types,
        fusion_method=fusion_method if fusion_method in {"rrf", "weighted", "borda", "adaptive"} else "adaptive",
        filters=filters
    )
    
    # Validate context
    errors = validate_query_context(context)
    if errors:
        raise QueryValidationError(f"Invalid query context: {'; '.join(errors)}")
    
    return context
