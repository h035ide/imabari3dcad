#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重複ノードを修正するスクリプト
"""

import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

def fix_duplicate_nodes():
    """重複ノードを修正"""
    load_dotenv()
    
    uri = os.getenv('NEO4J_URI')
    user = os.getenv('NEO4J_USER') or os.getenv('NEO4J_USERNAME')
    password = os.getenv('NEO4J_PASSWORD')
    
    if not all([uri, user, password]):
        print("Error: NEO4J_URI, NEO4J_USER (or NEO4J_USERNAME), and NEO4J_PASSWORD must be set in the .env file.")
        return
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        with driver.session(database='docparser') as session:
            print("=== 重複ノードの修正開始 ===\n")
            
            # 1. 現在の状況を確認
            print("1. 現在の状況確認:")
            query1 = """
            MATCH (n {name: '条材要素のパラメータオブジェクト'})
            RETURN n.name as name, labels(n) as labels, n.category as category
            """
            result1 = session.run(query1)
            nodes = list(result1)
            
            print(f"   '条材要素のパラメータオブジェクト'という名前のノード数: {len(nodes)}")
            for i, node in enumerate(nodes):
                print(f"   ノード {i+1}: {', '.join(node['labels'])} (カテゴリ: {node.get('category', 'None')})")
            print()
            
            if len(nodes) <= 1:
                print("   ✅ 重複ノードは存在しません。修正は不要です。")
                return
            
            # 2. Typeラベルのノードを特定
            print("2. Typeラベルのノードを特定:")
            query2 = """
            MATCH (n:Type {name: '条材要素のパラメータオブジェクト'})
            RETURN n.name as name, id(n) as node_id
            """
            result2 = session.run(query2)
            type_node = result2.single()
            
            if type_node:
                print(f"   Typeノードが見つかりました: ID {type_node['node_id']}")
            else:
                print("   ❌ Typeノードが見つかりません")
                return
            
            # 3. ObjectDefinitionラベルのノードを特定
            print("3. ObjectDefinitionラベルのノードを特定:")
            query3 = """
            MATCH (n:ObjectDefinition {name: '条材要素のパラメータオブジェクト'})
            RETURN n.name as name, id(n) as node_id
            """
            result3 = session.run(query3)
            obj_node = result3.single()
            
            if obj_node:
                print(f"   ObjectDefinitionノードが見つかりました: ID {obj_node['node_id']}")
            else:
                print("   ❌ ObjectDefinitionノードが見つかりません")
                return
            
            # 4. Typeノードの関係性をObjectDefinitionノードに移行
            print("4. 関係性の移行:")
            
            # 4.1 Typeノードに入ってくる関係を確認
            query4 = """
            MATCH (n:Type {name: '条材要素のパラメータオブジェクト'})<-[r]-(other)
            RETURN type(r) as relationship_type, labels(other) as other_labels, other.name as other_name
            """
            result4 = session.run(query4)
            incoming_rels = list(result4)
            
            print(f"   Typeノードに入ってくる関係数: {len(incoming_rels)}")
            for rel in incoming_rels:
                print(f"     {rel['other_labels']} '{rel['other_name']}' -[{rel['relationship_type']}]-> Typeノード")
            
            # 4.2 関係性を移行
            for rel in incoming_rels:
                if rel['relationship_type'] == 'RETURNS':
                    # RETURNS関係を移行
                    query_migrate = """
                    MATCH (f:Function {name: $func_name})-[r:RETURNS]->(old:Type {name: $type_name})
                    MATCH (new:ObjectDefinition {name: $type_name})
                    DELETE r
                    MERGE (f)-[:RETURNS]->(new)
                    """
                    session.run(query_migrate, func_name=rel['other_name'], type_name='条材要素のパラメータオブジェクト')
                    print(f"     ✅ RETURNS関係を移行: {rel['other_name']} -> ObjectDefinition")
                
                elif rel['relationship_type'] == 'HAS_TYPE':
                    # HAS_TYPE関係を移行
                    query_migrate = """
                    MATCH (p:Parameter {name: $param_name})-[r:HAS_TYPE]->(old:Type {name: $type_name})
                    MATCH (new:ObjectDefinition {name: $type_name})
                    DELETE r
                    MERGE (p)-[:HAS_TYPE]->(new)
                    """
                    session.run(query_migrate, param_name=rel['other_name'], type_name='条材要素のパラメータオブジェクト')
                    print(f"     ✅ HAS_TYPE関係を移行: {rel['other_name']} -> ObjectDefinition")
            
            # 5. Typeノードを削除
            print("5. Typeノードの削除:")
            query_delete = """
            MATCH (n:Type {name: '条材要素のパラメータオブジェクト'})
            DETACH DELETE n
            """
            session.run(query_delete)
            print("   ✅ Typeノードを削除しました")
            
            # 6. 修正結果の確認
            print("6. 修正結果の確認:")
            query6 = """
            MATCH (n {name: '条材要素のパラメータオブジェクト'})
            RETURN n.name as name, labels(n) as labels, n.category as category
            """
            result6 = session.run(query6)
            final_nodes = list(result6)
            
            print(f"   修正後のノード数: {len(final_nodes)}")
            for node in final_nodes:
                print(f"   ノード: {', '.join(node['labels'])} (カテゴリ: {node.get('category', 'None')})")
            
            if len(final_nodes) == 1 and 'ObjectDefinition' in final_nodes[0]['labels']:
                print("   🎉 修正が完了しました！")
            else:
                print("   ⚠️  修正に問題があります")
            
    finally:
        driver.close()

if __name__ == "__main__":
    fix_duplicate_nodes()
