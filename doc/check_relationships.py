#!/usr/bin/env python3
"""
Neo4jデータベース内のリレーション状況をチェックするスクリプト
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


def check_relationships():
    """リレーション状況をチェックする"""
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
                print("=== リレーション分析 ===")
                
                # 1. 全リレーションの種類と数を確認
                print("\n1. リレーション種類と数:")
                rel_counts = session.run("""
                    MATCH ()-[r]->()
                    RETURN type(r) as relType, count(r) as count
                    ORDER BY count DESC
                """)
                for record in rel_counts:
                    print(f"  {record['relType']}: {record['count']}個")
                
                # 2. ParameterノードのHAS_TYPEリレーション確認
                print("\n2. ParameterノードのHAS_TYPEリレーション:")
                param_rels = session.run("""
                    MATCH (p:Parameter)-[r:HAS_TYPE]->(t)
                    RETURN count(r) as count
                """)
                param_count = param_rels.single()['count']
                print(f"  Parameter -> Type: {param_count}個")
                
                # 3. 孤立したParameterノード
                print("\n3. 孤立したParameterノード:")
                isolated_params = session.run("""
                    MATCH (p:Parameter) WHERE NOT (p)-[:HAS_TYPE]->()
                    RETURN count(p) as count
                """)
                isolated_count = isolated_params.single()['count']
                print(f"  孤立したParameter: {isolated_count}個")
                
                # 4. 孤立したTypeノード
                print("\n4. 孤立したTypeノード:")
                isolated_types = session.run("""
                    MATCH (t:Type) WHERE NOT ()-[:HAS_TYPE]->(t)
                    RETURN count(t) as count
                """)
                isolated_type_count = isolated_types.single()['count']
                print(f"  孤立したType: {isolated_type_count}個")
                
                # 5. Functionノードのリレーション
                print("\n5. Functionノードのリレーション:")
                func_rels = session.run("""
                    MATCH (f:Function)-[r]->(n)
                    RETURN type(r) as relType, count(r) as count
                    ORDER BY count DESC
                """)
                for record in func_rels:
                    print(f"  Function -> {record['relType']}: {record['count']}個")
                
                # 6. __Entity__ノードのMAPS_TOリレーション
                print("\n6. __Entity__ノードのMAPS_TOリレーション:")
                entity_rels = session.run("""
                    MATCH (n)-[r:MAPS_TO]->(e:__Entity__)
                    RETURN count(r) as count
                """)
                entity_count = entity_rels.single()['count']
                print(f"  MAPS_TO -> __Entity__: {entity_count}個")
                
                # 7. Parameterノードの詳細確認
                print("\n7. Parameterノードの詳細:")
                param_details = session.run("""
                    MATCH (p:Parameter)
                    RETURN p.name as name, p.parent_function as parent_function, 
                           p.type as type, p.is_required as is_required
                    LIMIT 10
                """)
                for record in param_details:
                    print(f"  {record['name']} (parent: {record['parent_function']}, type: {record['type']}, required: {record['is_required']})")
                
                return True
                
    except Exception as e:
        print(f"エラー: {e}")
        return False


if __name__ == "__main__":
    success = check_relationships()
    if not success:
        sys.exit(1)

