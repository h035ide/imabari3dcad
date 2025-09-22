"""Graph-based retrieval using Neo4j."""

from __future__ import annotations

from typing import List, Optional, Dict, Any

from .base import BaseRetriever, QueryContext, SearchResult


class Neo4jGraphRetriever(BaseRetriever):
    """Neo4j-based graph retrieval for help documents."""
    
    def __init__(
        self,
        uri: str,
        username: str, 
        password: str,
        database: Optional[str] = None
    ):
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self._driver = None
        
    def _get_driver(self):
        """Get or create Neo4j driver."""
        if self._driver is None:
            try:
                from neo4j import GraphDatabase
                self._driver = GraphDatabase.driver(
                    self.uri, 
                    auth=(self.username, self.password)
                )
            except ImportError as exc:
                raise ImportError("Neo4j package required. Install with: pip install neo4j") from exc
        return self._driver
    
    def _execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict]:
        """Execute Cypher query and return results."""
        driver = self._get_driver()
        parameters = parameters or {}
        
        try:
            with driver.session(database=self.database) as session:
                result = session.run(query, parameters)
                return [record.data() for record in result]
        except Exception as exc:
            import logging
            logging.warning("Neo4j query failed: %s", exc)
            return []
    
    def search(self, context: QueryContext) -> List[SearchResult]:
        """Execute graph-based search."""
        query_text = context.query.lower()
        
        # Multi-strategy graph search
        strategies = [
            self._search_by_topic_title,
            self._search_by_category_name,
            self._search_related_topics,
            self._search_by_content_similarity
        ]
        
        all_results = []
        for strategy in strategies:
            try:
                results = strategy(query_text, context.top_k)
                all_results.extend(results)
            except Exception as exc:
                import logging
                logging.debug("Graph search strategy failed: %s", exc)
                
        # Remove duplicates and limit results
        seen_ids = set()
        unique_results = []
        for result in all_results:
            if result.id not in seen_ids:
                seen_ids.add(result.id)
                unique_results.append(result)
                
        return unique_results[:context.top_k]
    
    def _search_by_topic_title(self, query: str, limit: int) -> List[SearchResult]:
        """Search topics by title similarity."""
        cypher = """
        MATCH (topic:HelpTopic)
        WHERE toLower(topic.title) CONTAINS $query
        RETURN topic.topic_id as id, 
               topic.title as title,
               topic.source_path as source_path,
               topic.section_count as section_count,
               1.0 - (size($query) - size(topic.title)) * 1.0 / size(topic.title) as score
        ORDER BY score DESC
        LIMIT $limit
        """
        
        records = self._execute_query(cypher, {"query": query, "limit": limit})
        
        results = []
        for record in records:
            result = SearchResult(
                id=record["id"],
                content=record["title"],
                score=max(0.0, record["score"]),
                source="graph_topic_title",
                metadata={
                    "title": record["title"],
                    "source_path": record["source_path"],
                    "section_count": record["section_count"],
                    "search_type": "topic_title"
                }
            )
            results.append(result)
            
        return results
    
    def _search_by_category_name(self, query: str, limit: int) -> List[SearchResult]:
        """Search by category names and return related topics."""
        cypher = """
        MATCH (cat:HelpCategory)-[:HAS_TOPIC]->(topic:HelpTopic)
        WHERE toLower(cat.name) CONTAINS $query
        RETURN topic.topic_id as id,
               topic.title as title,
               cat.name as category_name,
               topic.source_path as source_path,
               0.8 as score
        ORDER BY topic.title
        LIMIT $limit
        """
        
        records = self._execute_query(cypher, {"query": query, "limit": limit})
        
        results = []
        for record in records:
            result = SearchResult(
                id=record["id"],
                content=f"{record['category_name']}: {record['title']}",
                score=record["score"],
                source="graph_category",
                metadata={
                    "title": record["title"],
                    "category_name": record["category_name"],
                    "source_path": record["source_path"],
                    "search_type": "category_name"
                }
            )
            results.append(result)
            
        return results
    
    def _search_related_topics(self, query: str, limit: int) -> List[SearchResult]:
        """Find topics related to matching topics."""
        cypher = """
        MATCH (topic1:HelpTopic)
        WHERE toLower(topic1.title) CONTAINS $query
        MATCH (cat:HelpCategory)-[:HAS_TOPIC]->(topic1)
        MATCH (cat)-[:HAS_TOPIC]->(topic2:HelpTopic)
        WHERE topic1 <> topic2
        RETURN DISTINCT topic2.topic_id as id,
               topic2.title as title,
               topic2.source_path as source_path,
               cat.name as category_name,
               0.6 as score
        ORDER BY topic2.title
        LIMIT $limit
        """
        
        records = self._execute_query(cypher, {"query": query, "limit": limit})
        
        results = []
        for record in records:
            result = SearchResult(
                id=record["id"],
                content=record["title"],
                score=record["score"],
                source="graph_related",
                metadata={
                    "title": record["title"],
                    "category_name": record["category_name"],
                    "source_path": record["source_path"],
                    "search_type": "related_topics"
                }
            )
            results.append(result)
            
        return results
    
    def _search_by_content_similarity(self, query: str, limit: int) -> List[SearchResult]:
        """Search by content keywords (if available in graph)."""
        # This would require storing content or keywords in the graph
        # For now, return empty results
        return []
    
    def get_name(self) -> str:
        return "graph_neo4j"
    
    def close(self):
        """Close Neo4j driver."""
        if self._driver:
            self._driver.close()
            self._driver = None
    
    def __del__(self):
        """Clean up driver."""
        self.close()


class GraphPathRetriever(BaseRetriever):
    """Retriever that finds paths between concepts in the graph."""
    
    def __init__(
        self,
        uri: str,
        username: str,
        password: str,
        database: Optional[str] = None,
        max_path_length: int = 3
    ):
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.max_path_length = max_path_length
        self._driver = None
        
    def _get_driver(self):
        """Get or create Neo4j driver."""
        if self._driver is None:
            try:
                from neo4j import GraphDatabase
                self._driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.username, self.password)
                )
            except ImportError as exc:
                raise ImportError("Neo4j package required. Install with: pip install neo4j") from exc
        return self._driver
    
    def search(self, context: QueryContext) -> List[SearchResult]:
        """Find conceptual paths in the help system."""
        driver = self._get_driver()
        query_terms = context.query.lower().split()
        
        if len(query_terms) < 2:
            return []
            
        # Find paths between concepts
        cypher = """
        MATCH (start:HelpTopic), (end:HelpTopic)
        WHERE toLower(start.title) CONTAINS $term1 
          AND toLower(end.title) CONTAINS $term2
          AND start <> end
        MATCH path = shortestPath((start)-[*1..{max_length}]-(end))
        RETURN path,
               length(path) as path_length,
               start.title as start_title,
               end.title as end_title,
               1.0 / (length(path) + 1) as score
        ORDER BY score DESC
        LIMIT $limit
        """.format(max_length=self.max_path_length)
        
        results = []
        
        # Try all pairs of terms
        for i, term1 in enumerate(query_terms):
            for term2 in query_terms[i+1:]:
                try:
                    with driver.session(database=self.database) as session:
                        records = session.run(cypher, {
                            "term1": term1,
                            "term2": term2,
                            "limit": context.top_k
                        })
                        
                        for record in records:
                            path_info = f"Path from '{record['start_title']}' to '{record['end_title']}'"
                            
                            result = SearchResult(
                                id=f"path_{term1}_{term2}_{record['path_length']}",
                                content=path_info,
                                score=record["score"],
                                source="graph_path",
                                metadata={
                                    "start_title": record["start_title"],
                                    "end_title": record["end_title"],
                                    "path_length": record["path_length"],
                                    "search_terms": [term1, term2],
                                    "search_type": "concept_path"
                                }
                            )
                            results.append(result)
                            
                except Exception as exc:
                    import logging
                    logging.debug("Path search failed for %s -> %s: %s", term1, term2, exc)
                    
        return results[:context.top_k]
    
    def get_name(self) -> str:
        return "graph_path"
    
    def close(self):
        """Close Neo4j driver."""
        if self._driver:
            self._driver.close()
            self._driver = None
    
    def __del__(self):
        """Clean up driver."""
        self.close()
