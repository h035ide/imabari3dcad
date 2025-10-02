#!/usr/bin/env python3
"""
現在のNeo4jデータベースの重複とリレーション問題を分析するスクリプト
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


def analyze_duplicates_and_relations():
    """重複とリレーション問題を分析"""
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
                print("=== 重複ノード分析 ===")
                
                # 1. Typeノードの重複チェック
                print("\n1. Typeノードの重複:")
                result = session.run("""
                    MATCH (t:Type)
                    WITH t.name as name, count(t) as count, collect(t) as nodes
                    WHERE count > 1
                    RETURN name, count, nodes
                    ORDER BY count DESC
                """)
                
                type_duplicates = list(result)
                if type_duplicates:
                    for record in type_duplicates:
                        print(f"  {record['name']}: {record['count']}個")
                        for i, node in enumerate(record['nodes']):
                            print(f"    {i+1}. ID: {node.id}, id: '{node.get('id', '')}', description: '{node.get('description', '')[:50]}...'")
                else:
                    print("  Typeノードの重複はありません")
                
                # 2. Functionノードの重複チェック
                print("\n2. Functionノードの重複:")
                result = session.run("""
                    MATCH (f:Function)
                    WITH f.name as name, count(f) as count, collect(f) as nodes
                    WHERE count > 1
                    RETURN name, count, nodes
                    ORDER BY count DESC
                """)
                
                function_duplicates = list(result)
                if function_duplicates:
                    for record in function_duplicates:
                        print(f"  {record['name']}: {record['count']}個")
                        for i, node in enumerate(record['nodes']):
                            print(f"    {i+1}. ID: {node.id}, description: '{node.get('description', '')[:50]}...'")
                else:
                    print("  Functionノードの重複はありません")
                
                # 3. LlamaIndexエンティティの重複チェック
                print("\n3. __Entity__ノードの重複:")
                result = session.run("""
                    MATCH (e:__Entity__)
                    WITH e.id as entity_id, count(e) as count, collect(e) as nodes
                    WHERE count > 1
                    RETURN entity_id, count, nodes
                    ORDER BY count DESC
                """)
                
                entity_duplicates = list(result)
                if entity_duplicates:
                    for record in entity_duplicates:
                        print(f"  {record['entity_id']}: {record['count']}個")
                        for i, node in enumerate(record['nodes']):
                            print(f"    {i+1}. ID: {node.id}, labels: {list(node.labels)}")
                else:
                    print("  __Entity__ノードの重複はありません")
                
                # 4. __Node__ノードの重複チェック
                print("\n4. __Node__ノードの重複:")
                result = session.run("""
                    MATCH (n:__Node__)
                    WITH n.id as node_id, count(n) as count, collect(n) as nodes
                    WHERE count > 1
                    RETURN node_id, count, nodes
                    ORDER BY count DESC
                """)
                
                node_duplicates = list(result)
                if node_duplicates:
                    for record in node_duplicates:
                        print(f"  {record['node_id']}: {record['count']}個")
                        for i, node in enumerate(record['nodes']):
                            print(f"    {i+1}. ID: {node.id}, text: '{node.get('text', '')[:50]}...'")
                else:
                    print("  __Node__ノードの重複はありません")
                
                # 5. リレーション分析
                print("\n5. リレーション分析:")
                
                # MAPS_TOリレーションの分析
                result = session.run("""
                    MATCH (n)-[r:MAPS_TO]->(e)
                    WITH n, e, count(r) as rel_count
                    WHERE rel_count > 1
                    RETURN n, e, rel_count
                    ORDER BY rel_count DESC
                    LIMIT 10
                """)
                
                map_duplicates = list(result)
                if map_duplicates:
                    print("  MAPS_TOリレーションの重複:")
                    for record in map_duplicates:
                        print(f"    {record['n'].id} -> {record['e'].id}: {record['rel_count']}個")
                else:
                    print("  MAPS_TOリレーションの重複はありません")
                
                # HAS_TYPEリレーションの分析
                result = session.run("""
                    MATCH (p)-[r:HAS_TYPE]->(t)
                    WITH p, t, count(r) as rel_count
                    WHERE rel_count > 1
                    RETURN p, t, rel_count
                    ORDER BY rel_count DESC
                    LIMIT 10
                """)
                
                type_rel_duplicates = list(result)
                if type_rel_duplicates:
                    print("  HAS_TYPEリレーションの重複:")
                    for record in type_rel_duplicates:
                        print(f"    {record['p'].id} -> {record['t'].id}: {record['rel_count']}個")
                else:
                    print("  HAS_TYPEリレーションの重複はありません")
                
                # 6. 孤立ノードのチェック
                print("\n6. 孤立ノードのチェック:")
                
                # 関係のないTypeノード
                result = session.run("""
                    MATCH (t:Type)
                    WHERE NOT (t)-[:HAS_TYPE]-() AND NOT (t)-[:MAPS_TO]-()
                    RETURN count(t) as isolated_types
                """)
                isolated_types = result.single()['isolated_types']
                print(f"  孤立したTypeノード: {isolated_types}個")
                
                # 関係のないFunctionノード
                result = session.run("""
                    MATCH (f:Function)
                    WHERE NOT (f)-[:HAS_PARAMETER]-() AND NOT (f)-[:RETURNS]-() AND NOT (f)-[:MAPS_TO]-()
                    RETURN count(f) as isolated_functions
                """)
                isolated_functions = result.single()['isolated_functions']
                print(f"  孤立したFunctionノード: {isolated_functions}個")
                
                # 7. 統計情報
                print("\n7. 統計情報:")
                stats = session.run("""
                    MATCH (n)
                    RETURN labels(n)[0] as label, count(n) as count
                    ORDER BY count DESC
                """)
                
                for record in stats:
                    print(f"  {record['label']}: {record['count']}個")
                
                return True
                
    except Exception as e:
        print(f"エラー: {e}")
        return False


if __name__ == "__main__":
    success = analyze_duplicates_and_relations()
    if success:
        print("\n分析が完了しました")
        sys.exit(0)
    else:
        print("分析に失敗しました")
        sys.exit(1)

