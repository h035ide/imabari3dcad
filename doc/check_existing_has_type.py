#!/usr/bin/env python3
"""
既存のHAS_TYPEリレーションを確認するスクリプト
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

def check_existing_has_type():
    """既存のHAS_TYPEリレーションを確認する"""
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
                print("=== 既存のHAS_TYPEリレーション確認 ===")
                
                # 1. 既存のHAS_TYPEリレーション
                existing_rels = session.run("""
                    MATCH (p:Parameter)-[r:HAS_TYPE]->(t:Type)
                    RETURN p.name AS paramName, t.name AS typeName, count(r) AS count
                    ORDER BY paramName
                """)
                
                print("既存のHAS_TYPEリレーション:")
                for record in existing_rels:
                    print(f"  {record['paramName']} -> {record['typeName']} ({record['count']}個)")
                
                # 2. 特定のParameterノードのHAS_TYPEリレーション
                test_param = session.run("""
                    MATCH (p:Parameter {name: 'bUpdate', parent_function: 'CreateLoftSheet'})
                    OPTIONAL MATCH (p)-[r:HAS_TYPE]->(t:Type)
                    RETURN p.name AS paramName, t.name AS typeName, count(r) AS count
                """)
                
                print("\n特定のParameterノード (bUpdate in CreateLoftSheet):")
                for record in test_param:
                    if record['typeName']:
                        print(f"  {record['paramName']} -> {record['typeName']} ({record['count']}個)")
                    else:
                        print(f"  {record['paramName']} -> リレーションなし")
                
                # 3. 該当するTypeノードの存在確認
                type_exists = session.run("""
                    MATCH (t:Type {name: 'bool'})
                    RETURN count(t) AS count
                """).single()['count']
                print(f"\nType 'bool' の存在: {type_exists}個")
                
                # 4. 該当するParameterノードの存在確認
                param_exists = session.run("""
                    MATCH (p:Parameter {name: 'bUpdate', parent_function: 'CreateLoftSheet'})
                    RETURN count(p) AS count
                """).single()['count']
                print(f"Parameter 'bUpdate' in 'CreateLoftSheet' の存在: {param_exists}個")
                
                print("\n確認が完了しました")
                return True
                
    except Exception as e:
        print(f"エラー: {e}")
        return False

if __name__ == "__main__":
    success = check_existing_has_type()
    if not success:
        sys.exit(1)

