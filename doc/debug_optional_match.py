#!/usr/bin/env python3
"""
OPTIONAL MATCHの結果をデバッグするスクリプト
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

def debug_optional_match():
    """OPTIONAL MATCHの結果をデバッグする"""
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
                print("=== OPTIONAL MATCHデバッグ ===")
                
                # テスト用のパラメータ
                param_type = "bool"
                
                print(f"テストパラメータ: param_type = {param_type}")
                
                # 1. ObjectDefinitionの確認
                print("\n1. ObjectDefinitionの確認:")
                od_result = session.run("""
                    MATCH (od:ObjectDefinition {name: $param_type})
                    RETURN count(od) AS count
                """, param_type=param_type)
                od_count = od_result.single()['count']
                print(f"  ObjectDefinition '{param_type}': {od_count}個")
                
                # 2. Typeの確認
                print("\n2. Typeの確認:")
                t_result = session.run("""
                    MATCH (t:Type {name: $param_type})
                    RETURN count(t) AS count
                """, param_type=param_type)
                t_count = t_result.single()['count']
                print(f"  Type '{param_type}': {t_count}個")
                
                # 3. OPTIONAL MATCHの結果確認
                print("\n3. OPTIONAL MATCHの結果確認:")
                opt_result = session.run("""
                    OPTIONAL MATCH (od:ObjectDefinition {name: $param_type})
                    OPTIONAL MATCH (t:Type {name: $param_type})
                    RETURN od, t, COALESCE(od, t) as type_node
                """, param_type=param_type)
                
                for record in opt_result:
                    print(f"  od: {record['od']}")
                    print(f"  t: {record['t']}")
                    print(f"  type_node: {record['type_node']}")
                    print(f"  type_node IS NOT NULL: {record['type_node'] is not None}")
                
                # 4. 修正されたクエリの詳細デバッグ
                print("\n4. 修正されたクエリの詳細デバッグ:")
                debug_query = """
                MATCH (p:Parameter {name: 'bUpdate', parent_function: 'CreateLoftSheet'})
                OPTIONAL MATCH (od:ObjectDefinition {name: $param_type})
                OPTIONAL MATCH (t:Type {name: $param_type})
                WITH p, od, t, COALESCE(od, t) as type_node
                RETURN p.name AS paramName, 
                       od.name AS odName, 
                       t.name AS tName, 
                       type_node.name AS typeNodeName,
                       type_node IS NOT NULL AS typeNodeNotNull
                """
                
                debug_result = session.run(debug_query, param_type=param_type)
                for record in debug_result:
                    print(f"  paramName: {record['paramName']}")
                    print(f"  odName: {record['odName']}")
                    print(f"  tName: {record['tName']}")
                    print(f"  typeNodeName: {record['typeNodeName']}")
                    print(f"  typeNodeNotNull: {record['typeNodeNotNull']}")
                
                print("\nデバッグが完了しました")
                return True
                
    except Exception as e:
        print(f"エラー: {e}")
        return False

if __name__ == "__main__":
    success = debug_optional_match()
    if not success:
        sys.exit(1)

