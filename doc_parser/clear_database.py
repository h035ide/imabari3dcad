# Neo4jデータベースを完全にクリアするスクリプト
import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

def clear_database():
    load_dotenv()
    
    NEO4J_URI = os.getenv("NEO4J_URI")
    # NEO4J_USER と NEO4J_USERNAME の両方に対応
    NEO4J_USER = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    NEO4J_DATABASE = "docparser"
    
    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print("Error: NEO4J_URI, NEO4J_USER (or NEO4J_USERNAME), and NEO4J_PASSWORD must be set in the .env file.")
        return
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        # まずsystemデータベースでdocparserデータベースの存在確認
        with driver.session(database="system") as session:
            print("=== docparserデータベースの確認 ===")
            result = session.run("SHOW DATABASES")
            databases = [record["name"] for record in result]
            
            if NEO4J_DATABASE not in databases:
                print(f"データベース '{NEO4J_DATABASE}' が存在しません。作成します...")
                session.run(f"CREATE DATABASE {NEO4J_DATABASE}")
                print(f"データベース '{NEO4J_DATABASE}' を作成しました。")
            else:
                print(f"データベース '{NEO4J_DATABASE}' が存在します。")
        
        # docparserデータベースでデータをクリア
        with driver.session(database=NEO4J_DATABASE) as session:
            print(f"\n=== データベース '{NEO4J_DATABASE}' のクリアを開始 ===")
            
            # すべての関係を削除
            print("すべての関係を削除中...")
            result = session.run("MATCH ()-[r]-() DELETE r")
            print("  関係の削除完了")
            
            # すべてのノードを削除
            print("すべてのノードを削除中...")
            result = session.run("MATCH (n) DELETE n")
            print("  ノードの削除完了")
            
            print(f"\n=== データベース '{NEO4J_DATABASE}' のクリア完了 ===")
            
            # 現在の状態を確認
            print("\n=== 現在の状態 ===")
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            node_count = result.single()['node_count']
            print(f"  ノード数: {node_count}")
            
            result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            rel_count = result.single()['rel_count']
            print(f"  関係数: {rel_count}")
                
    finally:
        driver.close()

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    clear_database()
