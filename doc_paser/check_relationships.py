# Neo4jデータベースの関係を確認するスクリプト
import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

def check_relationships():
    load_dotenv()
    
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    
    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print("Error: NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD must be set in the .env file.")
        return
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            # すべての関係タイプを確認
            print("=== 関係タイプの一覧 ===")
            result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType")
            for record in result:
                print(f"  - {record['relationshipType']}")
            
            print("\n=== 各関係タイプの数 ===")
            for rel_type in ["HAS_PARAMETER", "HAS_ARGUMENT", "HAS_TYPE", "HAS_PROPERTY", "RETURNS", "FEEDS_INTO"]:
                result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                count = result.single()['count']
                print(f"  {rel_type}: {count}")
            
            print("\n=== 重複関係の確認 ===")
            # 同じノード間で複数の関係が作成されているかチェック
            result = session.run("""
                MATCH (a)-[r1]->(b)
                MATCH (a)-[r2]->(b)
                WHERE r1 <> r2 AND type(r1) = type(r2)
                RETURN a.name as from_node, b.name as to_node, type(r1) as rel_type, count(*) as duplicate_count
                ORDER BY duplicate_count DESC
                LIMIT 10
            """)
            
            duplicates = list(result)
            if duplicates:
                print("重複関係が見つかりました:")
                for record in duplicates:
                    print(f"  {record['from_node']} -> {record['to_node']} ({record['rel_type']}): {record['duplicate_count']}個")
            else:
                print("重複関係は見つかりませんでした。")
            
            print("\n=== 関数とパラメータの関係詳細 ===")
            result = session.run("""
                MATCH (f:Function)-[r]->(p:Parameter)
                RETURN f.name as function, type(r) as rel_type, p.name as parameter, count(r) as rel_count
                ORDER BY rel_count DESC
                LIMIT 10
            """)
            
            for record in result:
                print(f"  {record['function']} -[{record['rel_type']}]-> {record['parameter']} (x{record['rel_count']})")
                
    finally:
        driver.close()

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    check_relationships()
