#!/usr/bin/env python3
"""
修正されたクエリをテストするスクリプト
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

def test_fixed_query():
    """修正されたクエリをテストする"""
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
                print("=== 修正されたクエリのテスト ===")
                
                # テスト用のパラメータ
                parent_name = "CreateLoftSheet"
                param_name = "bUpdate"
                param_type = "bool"
                
                print(f"テストパラメータ:")
                print(f"  parent_name: {parent_name}")
                print(f"  param_name: {param_name}")
                print(f"  param_type: {param_type}")
                
                # 1. 現在のHAS_TYPEリレーション数
                current_count = session.run("""
                    MATCH ()-[r:HAS_TYPE]->()
                    RETURN count(r) AS count
                """).single()['count']
                print(f"\n現在のHAS_TYPEリレーション数: {current_count}個")
                
                # 2. 修正されたクエリ（WHERE句を削除）
                print("\n2. 修正されたクエリ（WHERE句を削除）:")
                query1 = """
                MATCH (f:Function {name: $parent_name})
                MERGE (p:Parameter {name: $param_name,
                   kind: 'function',
                   parent_function: $parent_name})
                ON CREATE SET p.description = $param_description,
                    p.is_required = $param_required,
                    p.position = $param_position,
                    p.type = $param_type
                SET p.description = COALESCE($param_description, p.description)
                MERGE (f)-[r:USES_PARAMETER]->(p)
                SET r.parameter_description = $param_description,
                    r.is_required = $param_required,
                    r.position = $param_position

                WITH p
                // パラメータの型を確保（ObjectDefinitionまたはType）
                OPTIONAL MATCH (od:ObjectDefinition {name: $param_type})
                OPTIONAL MATCH (t:Type {name: $param_type})
                WITH p, COALESCE(od, t) as type_node
                FOREACH (x IN CASE WHEN type_node IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (p)-[:HAS_TYPE]->(type_node)
                )
                """
                
                try:
                    result = session.run(
                        query1,
                        parent_name=parent_name,
                        param_name=param_name,
                        param_description="",
                        param_required=False,
                        param_position=0,
                        param_type=param_type
                    )
                    # 結果を消費
                    list(result)
                    print("  クエリ1: 成功")
                except Exception as e:
                    print(f"  クエリ1: エラー - {e}")
                
                # 3. よりシンプルなクエリ
                print("\n3. よりシンプルなクエリ:")
                query2 = """
                MATCH (f:Function {name: $parent_name})
                MERGE (p:Parameter {name: $param_name,
                   kind: 'function',
                   parent_function: $parent_name})
                ON CREATE SET p.description = $param_description,
                    p.is_required = $param_required,
                    p.position = $param_position,
                    p.type = $param_type
                SET p.description = COALESCE($param_description, p.description)
                MERGE (f)-[r:USES_PARAMETER]->(p)
                SET r.parameter_description = $param_description,
                    r.is_required = $param_required,
                    r.position = $param_position

                WITH p
                MATCH (t:Type {name: $param_type})
                MERGE (p)-[:HAS_TYPE]->(t)
                """
                
                try:
                    result = session.run(
                        query2,
                        parent_name=parent_name,
                        param_name=param_name,
                        param_description="",
                        param_required=False,
                        param_position=0,
                        param_type=param_type
                    )
                    # 結果を消費
                    list(result)
                    print("  クエリ2: 成功")
                except Exception as e:
                    print(f"  クエリ2: エラー - {e}")
                
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
    success = test_fixed_query()
    if not success:
        sys.exit(1)

