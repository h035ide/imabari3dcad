#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重複ノードの問題を確認するスクリプト
"""

import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

def check_duplicate_nodes():
    """重複ノードの問題を確認"""
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
            print("=== 重複ノードの問題確認 ===\n")
            
            # 1. "条材要素のパラメータオブジェクト"という名前を持つすべてのノードを確認
            print("1. '条材要素のパラメータオブジェクト'という名前を持つノード:")
            query1 = """
            MATCH (n {name: '条材要素のパラメータオブジェクト'})
            RETURN n.name as name, labels(n) as labels, n.category as category, n.description as description
            """
            result1 = session.run(query1)
            nodes = list(result1)
            
            if nodes:
                for i, node in enumerate(nodes):
                    print(f"   ノード {i+1}:")
                    print(f"     名前: {node['name']}")
                    print(f"     ラベル: {node['labels']}")
                    print(f"     カテゴリ: {node.get('category', 'N/A')}")
                    print(f"     説明: {node.get('description', 'N/A')}")
                    print()
            else:
                print("   ❌ 該当するノードが見つかりません")
            
            # 2. 各ノードの関係性を確認
            print("2. 各ノードの関係性:")
            for i, node in enumerate(nodes):
                print(f"   ノード {i+1} ({', '.join(node['labels'])}) の関係性:")
                
                # 入ってくる関係
                query_in = """
                MATCH (n {name: '条材要素のパラメータオブジェクト'})<-[r]-(other)
                WHERE n.name = $node_name
                RETURN type(r) as relationship_type, labels(other) as other_labels, other.name as other_name
                LIMIT 5
                """
                result_in = session.run(query_in, node_name=node['name'])
                incoming = list(result_in)
                
                if incoming:
                    print(f"     入ってくる関係:")
                    for rel in incoming:
                        print(f"       {rel['other_labels']} '{rel['other_name']}' -[{rel['relationship_type']}]-> このノード")
                else:
                    print(f"     入ってくる関係: なし")
                
                # 出ていく関係
                query_out = """
                MATCH (n {name: '条材要素のパラメータオブジェクト'})-[r]->(other)
                WHERE n.name = $node_name
                RETURN type(r) as relationship_type, labels(other) as other_labels, other.name as other_name
                LIMIT 5
                """
                result_out = session.run(query_out, node_name=node['name'])
                outgoing = list(result_out)
                
                if outgoing:
                    print(f"     出ていく関係:")
                    for rel in outgoing:
                        print(f"       このノード -[{rel['relationship_type']}]-> {rel['other_labels']} '{rel['other_name']}'")
                else:
                    print(f"     出ていく関係: なし")
                
                print()
            
            # 3. CreateProfileParam関数との関係を確認
            print("3. CreateProfileParam関数との関係:")
            query3 = """
            MATCH (f:Function {name: 'CreateProfileParam'})-[r:RETURNS]->(return_node)
            RETURN r.type as relationship_type, return_node.name as return_name, labels(return_node) as return_labels
            """
            result3 = session.run(query3)
            returns = list(result3)
            
            if returns:
                for ret in returns:
                    print(f"   CreateProfileParam -[{ret['relationship_type'] or 'RETURNS'}]-> {ret['return_labels']} '{ret['return_name']}'")
            else:
                print("   ❌ CreateProfileParamの戻り値関係が見つかりません")
            
            print()
            
            # 4. 問題の要約
            print("4. 問題の要約:")
            if len(nodes) > 1:
                print(f"   ❌ 問題: 同じ名前のノードが {len(nodes)} 個存在しています")
                print(f"      これらは異なるラベルを持ち、関係性がありません")
                print(f"      正しい構造にするには、重複を解消する必要があります")
            else:
                print(f"   ✅ 問題なし: 重複ノードは存在しません")
            
    finally:
        driver.close()

if __name__ == "__main__":
    check_duplicate_nodes()
