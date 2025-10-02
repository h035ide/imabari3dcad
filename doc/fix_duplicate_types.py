#!/usr/bin/env python3
"""
重複したTypeノードを修正するスクリプト
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

def fix_duplicate_types():
    """重複したTypeノードを修正する"""
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
                print("=== 重複Typeノードの修正 ===")
                
                # 1. 重複したTypeノードを特定
                print("\n1. 重複したTypeノードを特定:")
                duplicates = session.run("""
                    MATCH (t:Type)
                    WITH t.name AS typeName, COLLECT(t) AS nodes
                    WHERE SIZE(nodes) > 1
                    RETURN typeName, nodes
                """)
                
                for record in duplicates:
                    type_name = record['typeName']
                    nodes = record['nodes']
                    print(f"  {type_name}: {len(nodes)}個の重複")
                    
                    # 2. 各重複ノードの詳細を確認
                    for i, node in enumerate(nodes):
                        print(f"    {i+1}. ID: {node.id}, id: '{node.get('id', '')}', description: '{node.get('description', '')[:50]}...'")
                    
                    # 3. 重複を統合（最初のノードを保持し、残りを削除）
                    if len(nodes) > 1:
                        # 最初のノードを保持
                        keep_node = nodes[0]
                        delete_nodes = nodes[1:]
                        
                        print(f"    保持するノード: ID {keep_node.id}")
                        print(f"    削除するノード: {[n.id for n in delete_nodes]}")
                        
                        # 重複ノードを単純に削除（リレーションは保持ノードに移行しない）
                        for delete_node in delete_nodes:
                            # ノードを削除
                            session.run("""
                                MATCH (d:Type) WHERE id(d) = $delete_id
                                DETACH DELETE d
                            """, delete_id=delete_node.id)
                        
                        print(f"    {type_name}の重複を修正しました")
                
                # 4. 修正後の確認
                print("\n2. 修正後の確認:")
                remaining_duplicates = session.run("""
                    MATCH (t:Type)
                    WITH t.name AS typeName, COLLECT(t) AS nodes
                    WHERE SIZE(nodes) > 1
                    RETURN typeName, SIZE(nodes) AS count
                """)
                
                duplicate_count = 0
                for record in remaining_duplicates:
                    duplicate_count += 1
                    print(f"  まだ重複: {record['typeName']} ({record['count']}個)")
                
                if duplicate_count == 0:
                    print("  重複はすべて修正されました")
                else:
                    print(f"  {duplicate_count}個の重複が残っています")
                
                print("\n修正が完了しました")
                return True
                
    except Exception as e:
        print(f"エラー: {e}")
        return False

if __name__ == "__main__":
    success = fix_duplicate_types()
    if not success:
        sys.exit(1)
