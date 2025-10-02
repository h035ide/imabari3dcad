#!/usr/bin/env python3
"""
ParameterノードとTypeノードの関係をデバッグするスクリプト
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


def debug_parameter_relationships():
    """ParameterノードとTypeノードの関係をデバッグする"""
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
                print("=== ParameterノードとTypeノードの関係デバッグ ===")
                
                # 1. Parameterノードの数
                param_count = session.run("MATCH (p:Parameter) RETURN count(p) as count").single()['count']
                print(f"Parameterノード数: {param_count}個")
                
                # 2. Typeノードの数
                type_count = session.run("MATCH (t:Type) RETURN count(t) as count").single()['count']
                print(f"Typeノード数: {type_count}個")
                
                # 3. Parameterノードの型情報
                print("\nParameterノードの型情報（最初の10個）:")
                param_types = session.run("""
                    MATCH (p:Parameter)
                    RETURN p.name as name, p.type as type, p.parent_function as parent_function
                    LIMIT 10
                """)
                for record in param_types:
                    print(f"  {record['name']} (parent: {record['parent_function']}, type: {record['type']})")
                
                # 4. 対応するTypeノードの存在確認
                print("\n対応するTypeノードの存在確認:")
                param_types = session.run("""
                    MATCH (p:Parameter)
                    RETURN DISTINCT p.type as type
                    LIMIT 10
                """)
                for record in param_types:
                    param_type = record['type']
                    if param_type:
                        type_exists = session.run("""
                            MATCH (t:Type {name: $type_name})
                            RETURN count(t) as count
                        """, type_name=param_type).single()['count'] > 0
                        print(f"  {param_type}: {'存在' if type_exists else '不存在'}")
                
                # 5. HAS_TYPEリレーションの詳細確認
                print("\nHAS_TYPEリレーションの詳細確認:")
                has_type_rels = session.run("""
                    MATCH (p:Parameter)-[r:HAS_TYPE]->(t)
                    RETURN p.name as param_name, t.name as type_name, labels(t) as type_labels
                    LIMIT 10
                """)
                for record in has_type_rels:
                    print(f"  {record['param_name']} -> {record['type_name']} ({record['type_labels']})")
                
                # 6. ParameterノードのUSES_PARAMETERリレーション確認
                print("\nParameterノードのUSES_PARAMETERリレーション確認:")
                uses_param_rels = session.run("""
                    MATCH (f:Function)-[r:USES_PARAMETER]->(p:Parameter)
                    RETURN f.name as func_name, p.name as param_name, count(r) as count
                    LIMIT 10
                """)
                for record in uses_param_rels:
                    print(f"  {record['func_name']} -> {record['param_name']} ({record['count']}個)")
                
                return True
                
    except Exception as e:
        print(f"エラー: {e}")
        return False


if __name__ == "__main__":
    success = debug_parameter_relationships()
    if not success:
        sys.exit(1)

