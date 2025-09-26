"""Full-text search using Whoosh and Elasticsearch."""

from __future__ import annotations

from pathlib import Path
from typing import List

from .base import BaseRetriever, QueryContext, SearchResult


class WhooshRetriever(BaseRetriever):
    """Whoosh-based full-text search retriever."""
    
    def __init__(self, index_dir: Path):
        self.index_dir = index_dir
        self._index = None
        self._searcher = None
        
    def _get_index(self):
        """Get or create Whoosh index."""
        if self._index is None:
            try:
                from whoosh import index
                self._index = index.open_dir(str(self.index_dir))
            except ImportError as exc:
                raise ImportError("Whoosh package required. Install with: pip install whoosh") from exc
            except Exception as exc:
                raise RuntimeError(f"Failed to open Whoosh index at {self.index_dir}") from exc
        return self._index
    
    def _get_searcher(self):
        """Get Whoosh searcher."""
        if self._searcher is None:
            idx = self._get_index()
            self._searcher = idx.searcher()
        return self._searcher
    
    def search(self, context: QueryContext) -> List[SearchResult]:
        """Execute full-text search using Whoosh."""
        try:
            from whoosh.qparser import QueryParser, MultifieldParser
            from whoosh.query import Every
        except ImportError as exc:
            raise ImportError("Whoosh package required. Install with: pip install whoosh") from exc
            
        searcher = self._get_searcher()
        
        # Create query parser (assuming common field names)
        schema_fields = list(searcher.schema.names())
        content_fields = [f for f in schema_fields if f in ['content', 'title', 'text', 'body']]
        
        if content_fields:
            if len(content_fields) == 1:
                parser = QueryParser(content_fields[0], searcher.schema)
            else:
                parser = MultifieldParser(content_fields, searcher.schema)
        else:
            # Fallback to first field
            parser = QueryParser(schema_fields[0], searcher.schema) if schema_fields else None
            
        if not parser:
            return []
            
        try:
            # Parse and execute query
            if context.query.strip():
                query = parser.parse(context.query)
            else:
                query = Every()  # Match all documents if empty query
                
            search_results = searcher.search(query, limit=context.top_k)
            
            results = []
            max_score = max(hit.score for hit in search_results) if search_results else 1.0
            
            for hit in search_results:
                # Extract content from available fields
                content = ""
                for field in content_fields:
                    if field in hit and hit[field]:
                        content = str(hit[field])
                        break
                        
                # Normalize score
                normalized_score = hit.score / max_score if max_score > 0 else 0.0
                
                result = SearchResult(
                    id=hit.get('id', hit.get('section_id', f'whoosh_{hit.docnum}')),
                    content=content,
                    score=normalized_score,
                    source="fulltext_whoosh",
                    metadata={
                        "whoosh_score": hit.score,
                        "docnum": hit.docnum,
                        "matched_fields": [f for f in content_fields if f in hit],
                        **{k: v for k, v in hit.items() if k not in content_fields}
                    }
                )
                results.append(result)
                
            return results
            
        except Exception as exc:
            # Log error but return empty results
            import logging
            logging.warning("Whoosh search failed: %s", exc)
            return []
    
    def get_name(self) -> str:
        return "fulltext_whoosh"
    
    def __del__(self):
        """Clean up searcher."""
        if self._searcher:
            self._searcher.close()


class ElasticsearchRetriever(BaseRetriever):
    """Elasticsearch-based full-text search retriever."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 9200,
        index_name: str = "help_documents",
        **es_kwargs
    ):
        self.host = host
        self.port = port
        self.index_name = index_name
        self.es_kwargs = es_kwargs
        self._client = None
        
    def _get_client(self):
        """Get or create Elasticsearch client."""
        if self._client is None:
            try:
                from elasticsearch import Elasticsearch
                self._client = Elasticsearch(
                    [{"host": self.host, "port": self.port}],
                    **self.es_kwargs
                )
                # Test connection
                if not self._client.ping():
                    raise ConnectionError("Elasticsearch server not reachable")
            except ImportError as exc:
                raise ImportError("Elasticsearch package required. Install with: pip install elasticsearch") from exc
        return self._client
    
    def search(self, context: QueryContext) -> List[SearchResult]:
        """Execute full-text search using Elasticsearch."""
        client = self._get_client()
        
        # Build Elasticsearch query
        es_query = {
            "query": {
                "multi_match": {
                    "query": context.query,
                    "fields": ["content^2", "title^3", "text", "body"],  # Boost title and content
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            },
            "size": context.top_k,
            "highlight": {
                "fields": {
                    "content": {"fragment_size": 150, "number_of_fragments": 3},
                    "title": {}
                }
            }
        }
        
        # Add filters if provided
        if context.filters:
            filter_clauses = []
            for field, value in context.filters.items():
                if isinstance(value, list):
                    filter_clauses.append({"terms": {field: value}})
                else:
                    filter_clauses.append({"term": {field: value}})
                    
            if filter_clauses:
                es_query["query"] = {
                    "bool": {
                        "must": es_query["query"],
                        "filter": filter_clauses
                    }
                }
        
        try:
            response = client.search(index=self.index_name, body=es_query)
            
            results = []
            max_score = response["hits"]["max_score"] or 1.0
            
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                
                # Extract content with highlights if available
                content = source.get("content", "")
                if "highlight" in hit and "content" in hit["highlight"]:
                    content = " ... ".join(hit["highlight"]["content"])
                
                # Normalize score
                normalized_score = hit["_score"] / max_score if max_score > 0 else 0.0
                
                result = SearchResult(
                    id=hit["_id"],
                    content=content,
                    score=normalized_score,
                    source="fulltext_elasticsearch",
                    metadata={
                        "es_score": hit["_score"],
                        "highlights": hit.get("highlight", {}),
                        "index": hit["_index"],
                        **source
                    }
                )
                results.append(result)
                
            return results
            
        except Exception as exc:
            import logging
            logging.warning("Elasticsearch search failed: %s", exc)
            return []
    
    def get_name(self) -> str:
        return f"fulltext_elasticsearch_{self.index_name}"
