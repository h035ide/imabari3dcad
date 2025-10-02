#!/usr/bin/env python3
"""
HAS_TYPEリレーションの作成をテストするスクリプト
"""

import os
import sys
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

load_dotenv()

def test_has_type_creation():
    """HAS_TYPEリレーションの作成をテストする"""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "docparser")
    
    if not password:
        print("エラー: NEO4J_PASSWORDが設定されていません")
        return False
    
    try:
        with GraphDatabase.driver(uri, auth=(user, password)) as driver:
            with driver.session(database=database) as session:
                print("=== HAS_TYPEリレーション作成テスト ===")
                
                # 1. 現在のHAS_TYPEリレーション数
                current_count = session.run("""
                    MATCH ()-[r:HAS_TYPE]->()
                    RETURN count(r) AS count
                """).single()['count']
                print(f"現在のHAS_TYPEリレーション数: {current_count}個")
                
                # 2. テスト用のParameterノードを取得
                test_params = session.run("""
                    MATCH (p:Parameter)
                    WHERE p.type = 'bool'
                    RETURN p.name AS name, p.type AS type, p.parent_function AS parent_function
                    LIMIT 5
                """)
                
                print("\nテスト対象のParameterノード:")
                param_list = []
                for record in test_params:
                    param_list.append({
                        'name': record['name'],
                        'type': record['type'],
                        'parent_function': record['parent_function']
                    })
                    print(f"  {record['name']} (type: {record['type']}, parent: {record['parent_function']})")
                
                # 3. 修正されたCypherクエリをテスト
                print("\n修正されたCypherクエリをテスト:")
                for param in param_list[:3]:  # 最初の3個をテスト
                    print(f"\nテスト: {param['name']} -> {param['type']}")
                    
                    # 修正されたクエリ（function type用）
                    query = """
                    MATCH (f:Function {name: $parent_name})
                    MATCH (p:Parameter {name: $param_name, kind: 'function', parent_function: $parent_name})
                    MATCH (t:Type {name: $param_type})
                    MERGE (p)-[:HAS_TYPE]->(t)
                    RETURN count(*) AS created
                    """
                    
                    try:
                        result = session.run(
                            query,
                            parent_name=param['parent_function'],
                            param_name=param['name'],
                            param_type=param['type']
                        )
                        created = result.single()['created']
                        print(f"  結果: {created}個のリレーションが作成されました")
                    except Exception as e:
                        print(f"  エラー: {e}")
                
                # 4. 最終的なHAS_TYPEリレーション数
                final_count = session.run("""
                    MATCH ()-[r:HAS_TYPE]->()
                    RETURN count(r) AS count
                """).single()['count']
                print(f"\n最終的なHAS_TYPEリレーション数: {final_count}個")
                
                print("\nテストが完了しました")
                return True
                
    except Exception as e:
        print(f"エラー: {e}")
        return False

if __name__ == "__main__":
    success = test_has_type_creation()
    if not success:
        sys.exit(1)

