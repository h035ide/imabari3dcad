# Neo4jデータベースの重複関係をクリーンアップするスクリプト
import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

def cleanup_duplicates():
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
            print("=== 重複関係のクリーンアップを開始 ===")
            
            # HAS_PARAMETER関係の重複を削除
            print("HAS_PARAMETER関係の重複を削除中...")
            result = session.run("""
                MATCH (f:Function)-[r1:HAS_PARAMETER]->(p:Parameter)
                MATCH (f)-[r2:HAS_PARAMETER]->(p)
                WHERE r1 <> r2
                WITH f, p, r1, r2
                DELETE r2
                RETURN count(r2) as deleted_count
            """)
            
            deleted_count = result.single()['deleted_count']
            print(f"  削除された重複関係: {deleted_count}個")
            
            # HAS_ARGUMENT関係を削除（HAS_PARAMETERに統一）
            print("HAS_ARGUMENT関係を削除中...")
            result = session.run("""
                MATCH ()-[r:HAS_ARGUMENT]->()
                DELETE r
                RETURN count(r) as deleted_count
            """)
            
            deleted_count = result.single()['deleted_count']
            print(f"  削除されたHAS_ARGUMENT関係: {deleted_count}個")
            
            # 孤立したParameterノードを削除
            print("孤立したParameterノードを削除中...")
            result = session.run("""
                MATCH (p:Parameter)
                WHERE NOT (p)-[:HAS_PARAMETER]-() AND NOT (p)-[:HAS_PROPERTY]-()
                DELETE p
                RETURN count(p) as deleted_count
            """)
            
            deleted_count = result.single()['deleted_count']
            print(f"  削除された孤立Parameterノード: {deleted_count}個")
            
            # 孤立したTypeノードを削除
            print("孤立したTypeノードを削除中...")
            result = session.run("""
                MATCH (t:Type)
                WHERE NOT (t)<-[:HAS_TYPE]-() AND NOT (t)<-[:RETURNS]-()
                DELETE t
                RETURN count(t) as deleted_count
            """)
            
            deleted_count = result.single()['deleted_count']
            print(f"  削除された孤立Typeノード: {deleted_count}個")
            
            print("\n=== クリーンアップ完了 ===")
            
            # 現在の状態を確認
            print("\n=== 現在の関係数 ===")
            for rel_type in ["HAS_PARAMETER", "HAS_ARGUMENT", "HAS_TYPE", "HAS_PROPERTY", "RETURNS"]:
                result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                count = result.single()['count']
                print(f"  {rel_type}: {count}")
                
    finally:
        driver.close()

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    cleanup_duplicates()
