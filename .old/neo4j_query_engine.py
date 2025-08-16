from neo4j import GraphDatabase
import os
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class Neo4jQueryEngine:
    """Neo4jクエリエンジン"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str, 
                 database_name: str = "treesitter_advanced"):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.database_name = database_name
    
    def find_functions_by_complexity(self, min_complexity: float = 5.0) -> List[Dict]:
        """複雑性が高い関数を検索"""
        driver = GraphDatabase.driver(self.neo4j_uri, 
                                    auth=(self.neo4j_user, self.neo4j_password))
        
        try:
            with driver.session(database=self.database_name) as session:
                result = session.run("""
                MATCH (f:Function)
                WHERE f.complexity_score >= $min_complexity
                RETURN f.name as name, f.complexity_score as complexity, 
                       f.file_path as file_path, f.text as text
                ORDER BY f.complexity_score DESC
                """, min_complexity=min_complexity)
                
                return [record.data() for record in result]
        finally:
            driver.close()
    
    def find_function_dependencies(self, function_name: str) -> Dict:
        """関数の依存関係を検索"""
        driver = GraphDatabase.driver(self.neo4j_uri, 
                                    auth=(self.neo4j_user, self.neo4j_password))
        
        try:
            with driver.session(database=self.database_name) as session:
                # 関数が呼び出す他の関数
                calls_result = session.run("""
                MATCH (f:Function {name: $function_name})-[r:CALLS]->(called:Function)
                RETURN called.name as called_function
                """, function_name=function_name)
                
                # 関数を呼び出す他の関数
                called_by_result = session.run("""
                MATCH (caller:Function)-[r:CALLS]->(f:Function {name: $function_name})
                RETURN caller.name as caller_function
                """, function_name=function_name)
                
                return {
                    "calls": [record["called_function"] for record in calls_result],
                    "called_by": [record["caller_function"] for record in called_by_result]
                }
        finally:
            driver.close()
    
    def find_high_complexity_paths(self, max_depth: int = 3) -> List[Dict]:
        """高複雑性のパスを検索"""
        driver = GraphDatabase.driver(self.neo4j_uri, 
                                    auth=(self.neo4j_user, self.neo4j_password))
        
        try:
            with driver.session(database=self.database_name) as session:
                result = session.run("""
                MATCH path = (start:Function)-[r:CALLS*1..$max_depth]->(end:Function)
                WHERE start.complexity_score > 5 OR end.complexity_score > 5
                RETURN start.name as start_function, end.name as end_function,
                       length(path) as path_length,
                       start.complexity_score + end.complexity_score as total_complexity
                ORDER BY total_complexity DESC
                LIMIT 20
                """, max_depth=max_depth)
                
                return [record.data() for record in result]
        finally:
            driver.close()
    
    def find_classes_with_methods(self) -> List[Dict]:
        """メソッドを持つクラスを検索"""
        driver = GraphDatabase.driver(self.neo4j_uri, 
                                    auth=(self.neo4j_user, self.neo4j_password))
        
        try:
            with driver.session(database=self.database_name) as session:
                result = session.run("""
                MATCH (c:Class)-[:CONTAINS]->(f:Function)
                RETURN c.name as class_name, 
                       collect(f.name) as methods,
                       count(f) as method_count
                ORDER BY method_count DESC
                """)
                
                return [record.data() for record in result]
        finally:
            driver.close()
    
    def find_import_relationships(self) -> List[Dict]:
        """インポート関係を検索"""
        driver = GraphDatabase.driver(self.neo4j_uri, 
                                    auth=(self.neo4j_user, self.neo4j_password))
        
        try:
            with driver.session(database=self.database_name) as session:
                result = session.run("""
                MATCH (i:Import)-[:IMPORTS]->(target)
                RETURN i.import_name as import_name,
                       labels(target)[0] as target_type,
                       target.name as target_name
                """)
                
                return [record.data() for record in result]
        finally:
            driver.close()
    
    def find_code_metrics(self) -> Dict:
        """コードメトリクスを取得"""
        driver = GraphDatabase.driver(self.neo4j_uri, 
                                    auth=(self.neo4j_user, self.neo4j_password))
        
        try:
            with driver.session(database=self.database_name) as session:
                # 基本統計
                basic_stats = session.run("""
                MATCH (n)
                RETURN count(n) as total_nodes,
                       count(DISTINCT labels(n)[0]) as node_types
                """).single()
                
                # 関数統計
                function_stats = session.run("""
                MATCH (f:Function)
                RETURN count(f) as total_functions,
                       avg(f.complexity_score) as avg_complexity,
                       max(f.complexity_score) as max_complexity
                """).single()
                
                # クラス統計
                class_stats = session.run("""
                MATCH (c:Class)
                RETURN count(c) as total_classes
                """).single()
                
                # リレーション統計
                relation_stats = session.run("""
                MATCH ()-[r]->()
                RETURN count(r) as total_relations,
                       count(DISTINCT type(r)) as relation_types
                """).single()
                
                return {
                    "basic": basic_stats.data() if basic_stats else {},
                    "functions": function_stats.data() if function_stats else {},
                    "classes": class_stats.data() if class_stats else {},
                    "relations": relation_stats.data() if relation_stats else {}
                }
        finally:
            driver.close()
    
    def find_llm_analyzed_nodes(self) -> List[Dict]:
        """LLM分析済みのノードを検索"""
        driver = GraphDatabase.driver(self.neo4j_uri, 
                                    auth=(self.neo4j_user, self.neo4j_password))
        
        try:
            with driver.session(database=self.database_name) as session:
                result = session.run("""
                MATCH (n)
                WHERE n.llm_analysis IS NOT NULL
                RETURN n.name as name,
                       labels(n)[0] as type,
                       n.llm_analysis as llm_analysis
                """)
                
                return [record.data() for record in result]
        finally:
            driver.close()
    
    def find_code_patterns(self, pattern_type: str = "all") -> List[Dict]:
        """コードパターンを検索"""
        driver = GraphDatabase.driver(self.neo4j_uri, 
                                    auth=(self.neo4j_user, self.neo4j_password))
        
        try:
            with driver.session(database=self.database_name) as session:
                if pattern_type == "decorators":
                    result = session.run("""
                    MATCH (f:Function)
                    WHERE f.decorators IS NOT NULL
                    RETURN f.name as function_name,
                           f.decorators as decorators
                    """)
                elif pattern_type == "inheritance":
                    result = session.run("""
                    MATCH (c:Class)
                    WHERE c.superclasses IS NOT NULL
                    RETURN c.name as class_name,
                           c.superclasses as superclasses
                    """)
                else:
                    result = session.run("""
                    MATCH (n)
                    WHERE n.decorators IS NOT NULL OR n.superclasses IS NOT NULL
                    RETURN n.name as name,
                           labels(n)[0] as type,
                           n.decorators as decorators,
                           n.superclasses as superclasses
                    """)
                
                return [record.data() for record in result]
        finally:
            driver.close()
    
    def export_graph_data(self, output_file: str = "graph_export.json") -> None:
        """グラフデータをエクスポート"""
        driver = GraphDatabase.driver(self.neo4j_uri, 
                                    auth=(self.neo4j_user, self.neo4j_password))
        
        try:
            with driver.session(database=self.database_name) as session:
                # ノードの取得
                nodes_result = session.run("""
                MATCH (n)
                RETURN n
                """)
                
                # リレーションの取得
                relations_result = session.run("""
                MATCH (source)-[r]->(target)
                RETURN source.id as source_id,
                       target.id as target_id,
                       type(r) as relation_type,
                       properties(r) as relation_properties
                """)
                
                # データの構造化
                nodes = [record["n"] for record in nodes_result]
                relations = [record.data() for record in relations_result]
                
                export_data = {
                    "nodes": nodes,
                    "relations": relations,
                    "metadata": {
                        "total_nodes": len(nodes),
                        "total_relations": len(relations)
                    }
                }
                
                import json
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"グラフデータを {output_file} にエクスポートしました")
        
        finally:
            driver.close()

def main():
    """メイン関数"""
    # Neo4j接続情報
    neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    
    # クエリエンジンの作成
    query_engine = Neo4jQueryEngine(neo4j_uri, neo4j_user, neo4j_password)
    
    # 高複雑性関数の検索
    complex_functions = query_engine.find_functions_by_complexity(min_complexity=3.0)
    logger.info(f"高複雑性関数: {len(complex_functions)}個")
    
    # 依存関係の検索
    if complex_functions:
        first_function = complex_functions[0]["name"]
        dependencies = query_engine.find_function_dependencies(first_function)
        logger.info(f"関数 '{first_function}' の依存関係: {dependencies}")
    
    # コードメトリクスの取得
    metrics = query_engine.find_code_metrics()
    logger.info(f"コードメトリクス: {metrics}")
    
    # LLM分析済みノードの検索
    llm_nodes = query_engine.find_llm_analyzed_nodes()
    logger.info(f"LLM分析済みノード: {len(llm_nodes)}個")
    
    # グラフデータのエクスポート
    query_engine.export_graph_data("treesitter_graph_export.json")
    
    logger.info("クエリ処理が完了しました。")

if __name__ == "__main__":
    main() 