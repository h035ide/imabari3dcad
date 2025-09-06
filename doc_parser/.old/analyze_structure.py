#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CreateProfileParamと条材要素のパラメータオブジェクトの関係構造を分析するスクリプト
"""

import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

def analyze_structure():
    """CreateProfileParamの構造を分析"""
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
            print("=== CreateProfileParamの構造分析 ===\n")
            
            # 1. CreateProfileParam関数の基本情報
            print("1. CreateProfileParam関数の基本情報:")
            query1 = """
            MATCH (f:Function {name: 'CreateProfileParam'})
            RETURN f.name as name, f.description as description, f.category as category, f.implementation_status as status
            """
            result1 = session.run(query1)
            func_info = result1.single()
            if func_info:
                print(f"   関数名: {func_info['name']}")
                print(f"   説明: {func_info['description']}")
                print(f"   カテゴリ: {func_info['category']}")
                print(f"   実装状況: {func_info['status']}")
            print()
            
            # 2. 戻り値の関係
            print("2. 戻り値の関係:")
            query2 = """
            MATCH (f:Function {name: 'CreateProfileParam'})-[r:RETURNS]->(return_node)
            RETURN r.type as relationship_type, return_node.name as return_name, labels(return_node) as return_labels
            """
            result2 = session.run(query2)
            for record in result2:
                print(f"   関係タイプ: {record['relationship_type']}")
                print(f"   戻り値名: {record['return_name']}")
                print(f"   戻り値ラベル: {record['return_labels']}")
            print()
            
            # 3. 条材要素のパラメータオブジェクトの詳細
            print("3. 条材要素のパラメータオブジェクトの詳細:")
            query3 = """
            MATCH (od:ObjectDefinition {name: '条材要素のパラメータオブジェクト'})
            RETURN od.name as name, od.description as description, od.category as category
            """
            result3 = session.run(query3)
            obj_info = result3.single()
            if obj_info:
                print(f"   オブジェクト名: {obj_info['name']}")
                print(f"   説明: {obj_info['description']}")
                print(f"   カテゴリ: {obj_info['category']}")
            print()
            
            # 4. プロパティの関係
            print("4. プロパティの関係:")
            query4 = """
            MATCH (od:ObjectDefinition {name: '条材要素のパラメータオブジェクト'})-[r:HAS_PROPERTY]->(p:Parameter)
            RETURN r.type as relationship_type, p.name as param_name, p.description as param_description
            ORDER BY p.name
            LIMIT 10
            """
            result4 = session.run(query4)
            prop_count = 0
            for record in result4:
                print(f"   関係: {record['relationship_type']}")
                print(f"   パラメータ: {record['param_name']}")
                print(f"   説明: {record['param_description']}")
                print()
                prop_count += 1
            
            if prop_count == 0:
                print("   ❌ プロパティが見つかりません")
            print()
            
            # 5. 型情報の関係
            print("5. 型情報の関係:")
            query5 = """
            MATCH (od:ObjectDefinition {name: '条材要素のパラメータオブジェクト'})-[:HAS_PROPERTY]->(p:Parameter)-[r:HAS_TYPE]->(t:Type)
            RETURN p.name as param_name, r.type as relationship_type, t.name as type_name
            ORDER BY p.name
            LIMIT 10
            """
            result5 = session.run(query5)
            type_count = 0
            for record in result5:
                print(f"   パラメータ: {record['param_name']}")
                print(f"   関係: {record['relationship_type']}")
                print(f"   型: {record['type_name']}")
                print()
                type_count += 1
            
            if type_count == 0:
                print("   ❌ 型情報が見つかりません")
            print()
            
            # 6. 全体の関係構造の要約
            print("6. 全体の関係構造の要約:")
            query6 = """
            MATCH (f:Function {name: 'CreateProfileParam'})
            OPTIONAL MATCH (f)-[r1:RETURNS]->(return_node)
            OPTIONAL MATCH (return_node)-[r2:HAS_PROPERTY]->(p:Parameter)
            OPTIONAL MATCH (p)-[r3:HAS_TYPE]->(t:Type)
            RETURN 
                count(DISTINCT f) as function_count,
                count(DISTINCT return_node) as return_count,
                count(DISTINCT p) as param_count,
                count(DISTINCT t) as type_count
            """
            result6 = session.run(query6)
            summary = result6.single()
            if summary:
                print(f"   関数数: {summary['function_count']}")
                print(f"   戻り値数: {summary['return_count']}")
                print(f"   パラメータ数: {summary['param_count']}")
                print(f"   型情報数: {summary['type_count']}")
                
                if summary['param_count'] > 0 and summary['type_count'] > 0:
                    print("   ✅ パラメータと型情報が正しく関連付けられています")
                else:
                    print("   ❌ パラメータと型情報の関連付けに問題があります")
            
    finally:
        driver.close()

if __name__ == "__main__":
    analyze_structure()
