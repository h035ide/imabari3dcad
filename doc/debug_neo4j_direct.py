#!/usr/bin/env python3
"""
Neo4jで直接クエリを実行してParameterとTypeの関係をデバッグするスクリプト
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

def debug_neo4j_direct():
    """Neo4jで直接クエリを実行してデバッグする"""
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
                print("=== Neo4j直接デバッグ ===")
                
                # 1. Parameterノードのtypeプロパティの一意な値を取得
                print("\n1. Parameterノードのtypeプロパティ:")
                param_types = session.run("""
                    MATCH (p:Parameter)
                    RETURN DISTINCT p.type AS typeName, count(p) AS count
                    ORDER BY typeName
                """)
                param_type_list = []
                for record in param_types:
                    param_type_list.append(record['typeName'])
                    print(f"  {record['typeName']}: {record['count']}個")
                
                # 2. Typeノードのnameプロパティの一意な値を取得
                print("\n2. Typeノードのnameプロパティ:")
                type_names = session.run("""
                    MATCH (t:Type)
                    RETURN DISTINCT t.name AS typeName, count(t) AS count
                    ORDER BY typeName
                """)
                type_name_list = []
                for record in type_names:
                    type_name_list.append(record['typeName'])
                    print(f"  {record['typeName']}: {record['count']}個")
                
                # 3. 一致しないものをチェック
                print("\n3. 一致しないtype:")
                missing_in_type = set(param_type_list) - set(type_name_list)
                missing_in_param = set(type_name_list) - set(param_type_list)
                
                if missing_in_type:
                    print("  ParameterにあってTypeにないもの:")
                    for t in missing_in_type:
                        print(f"    '{t}'")
                
                if missing_in_param:
                    print("  TypeにあってParameterにないもの:")
                    for t in missing_in_param:
                        print(f"    '{t}'")
                
                if not missing_in_type and not missing_in_param:
                    print("  すべて一致しています")
                
                # 4. 具体的なParameterノードとTypeノードのペアを確認
                print("\n4. 具体的なペアの確認（最初の5個）:")
                pairs = session.run("""
                    MATCH (p:Parameter)
                    WITH p LIMIT 5
                    MATCH (t:Type {name: p.type})
                    RETURN p.name AS paramName, p.type AS paramType, t.name AS typeName
                """)
                for record in pairs:
                    print(f"  Parameter: {record['paramName']} (type: {record['paramType']}) -> Type: {record['typeName']}")
                
                # 5. HAS_TYPEリレーションの作成を試してみる
                print("\n5. HAS_TYPEリレーションの作成テスト:")
                test_result = session.run("""
                    MATCH (p:Parameter {name: 'StartPoint'})
                    MATCH (t:Type {name: '点'})
                    MERGE (p)-[:HAS_TYPE]->(t)
                    RETURN p.name AS paramName, t.name AS typeName
                """)
                for record in test_result:
                    print(f"  テスト成功: {record['paramName']} -> {record['typeName']}")
                
                # 6. 作成されたリレーションを確認
                print("\n6. 作成されたHAS_TYPEリレーション:")
                has_type_count = session.run("""
                    MATCH (p:Parameter)-[:HAS_TYPE]->(t:Type)
                    RETURN count(*) AS count
                """).single()['count']
                print(f"  HAS_TYPEリレーション数: {has_type_count}個")
                
                print("\nデバッグが完了しました")
                return True
                
    except Exception as e:
        print(f"エラー: {e}")
        return False

if __name__ == "__main__":
    success = debug_neo4j_direct()
    if not success:
        sys.exit(1)

