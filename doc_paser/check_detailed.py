# Neo4jデータベースの詳細な状態を確認するスクリプト
import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

def check_detailed():
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
            print("=== データベースの詳細状態 ===")
            
            # ノードの種類と数を確認
            print("\n--- ノードの種類と数 ---")
            result = session.run("CALL db.labels() YIELD label RETURN label")
            labels = [record['label'] for record in result]
            
            for label in labels:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                count = result.single()['count']
                print(f"  {label}: {count}個")
            
            # 関係の種類と数を確認
            print("\n--- 関係の種類と数 ---")
            result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType")
            rel_types = [record['relationshipType'] for record in result]
            
            for rel_type in rel_types:
                result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                count = result.single()['count']
                print(f"  {rel_type}: {count}個")
            
            # 関数ノードの詳細
            print("\n--- 関数ノードの詳細 ---")
            result = session.run("MATCH (f:Function) RETURN f.name as name, f.description as desc")
            functions = list(result)
            if functions:
                for record in functions:
                    print(f"  関数: {record['name']}")
                    print(f"    説明: {record['desc']}")
            else:
                print("  関数ノードが見つかりません")
            
            # パラメータノードの詳細
            print("\n--- パラメータノードの詳細 ---")
            result = session.run("MATCH (p:Parameter) RETURN p.name as name, p.parent_function as parent")
            params = list(result)
            if params:
                for record in params:
                    print(f"  パラメータ: {record['name']} (親関数: {record['parent']})")
            else:
                print("  パラメータノードが見つかりません")
            
            # 型定義ノードの詳細
            print("\n--- 型定義ノードの詳細 ---")
            result = session.run("MATCH (t:Type) RETURN t.name as name, t.description as desc LIMIT 5")
            types = list(result)
            if types:
                for record in types:
                    print(f"  型: {record['name']}")
                    print(f"    説明: {record['desc']}")
            else:
                print("  型定義ノードが見つかりません")
                
    finally:
        driver.close()

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    check_detailed()
