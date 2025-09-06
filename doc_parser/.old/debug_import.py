#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Neo4jインポート処理のデバッグスクリプト
"""

import json
import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

def debug_import():
    """インポート処理のデバッグ"""
    load_dotenv()
    
    # 1. JSONデータの確認
    print("=== JSONデータの確認 ===")
    
    # parsed_api_result_def.jsonを読み込み
    json_file = 'parsed_api_result_def.json'
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ {json_file} を読み込みました")
    except Exception as e:
        print(f"❌ {json_file} の読み込みに失敗: {e}")
        return
    
    # CreateProfileParamの情報を確認
    api_entries = data.get('api_entries', [])
    createprofileparam_func = None
    createprofileparam_obj = None
    
    for entry in api_entries:
        if entry.get('name') == 'CreateProfileParam':
            createprofileparam_func = entry
        elif entry.get('name') == '条材要素のパラメータオブジェクト':
            createprofileparam_obj = entry
    
    print(f"\n1. CreateProfileParam関数:")
    if createprofileparam_func:
        print(f"   エントリータイプ: {createprofileparam_func.get('entry_type')}")
        print(f"   説明: {createprofileparam_func.get('description')}")
        print(f"   カテゴリ: {createprofileparam_func.get('category')}")
        print(f"   パラメータ数: {len(createprofileparam_func.get('params', []))}")
        print(f"   戻り値: {createprofileparam_func.get('returns')}")
    else:
        print("   ❌ 見つかりません")
    
    print(f"\n2. 条材要素のパラメータオブジェクト:")
    if createprofileparam_obj:
        print(f"   エントリータイプ: {createprofileparam_obj.get('entry_type')}")
        print(f"   説明: {createprofileparam_obj.get('description')}")
        print(f"   カテゴリ: {createprofileparam_obj.get('category')}")
        print(f"   プロパティ数: {len(createprofileparam_obj.get('properties', []))}")
        
        # プロパティの詳細を表示
        properties = createprofileparam_obj.get('properties', [])
        if properties:
            print(f"   最初の5つのプロパティ:")
            for i, prop in enumerate(properties[:5]):
                print(f"     {i+1}. {prop.get('name')}: {prop.get('type')} - {prop.get('description')}")
        else:
            print("   ❌ プロパティが定義されていません")
    else:
        print("   ❌ 見つかりません")
    
    # 2. Neo4jデータベースの確認
    print(f"\n=== Neo4jデータベースの確認 ===")
    
    uri = os.getenv('NEO4J_URI')
    user = os.getenv('NEO4J_USER') or os.getenv('NEO4J_USERNAME')
    password = os.getenv('NEO4J_PASSWORD')
    
    if not all([uri, user, password]):
        print("❌ Neo4jの接続情報が不足しています")
        return
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        with driver.session(database='docparser') as session:
            # CreateProfileParam関数の確認
            print(f"\n1. CreateProfileParam関数の確認:")
            query1 = """
            MATCH (f:Function {name: 'CreateProfileParam'})
            RETURN f.name as name, f.description as description, f.category as category
            """
            result1 = session.run(query1)
            func_record = result1.single()
            if func_record:
                print(f"   ✅ 関数が存在します: {func_record['name']}")
                print(f"   説明: {func_record['description']}")
                print(f"   カテゴリ: {func_record['category']}")
            else:
                print("   ❌ 関数が見つかりません")
            
            # 条材要素のパラメータオブジェクトの確認
            print(f"\n2. 条材要素のパラメータオブジェクトの確認:")
            query2 = """
            MATCH (od:ObjectDefinition {name: '条材要素のパラメータオブジェクト'})
            RETURN od.name as name, od.description as description, od.category as category
            """
            result2 = session.run(query2)
            obj_record = result2.single()
            if obj_record:
                print(f"   ✅ オブジェクトが存在します: {obj_record['name']}")
                print(f"   説明: {obj_record['description']}")
                print(f"   カテゴリ: {obj_record['category']}")
            else:
                print("   ❌ オブジェクトが見つかりません")
            
            # プロパティの確認
            print(f"\n3. プロパティの確認:")
            query3 = """
            MATCH (od:ObjectDefinition {name: '条材要素のパラメータオブジェクト'})-[:HAS_PROPERTY]->(p:Parameter)
            RETURN count(p) as prop_count
            """
            result3 = session.run(query3)
            prop_count_record = result3.single()
            if prop_count_record:
                prop_count = prop_count_record['prop_count']
                print(f"   プロパティ数: {prop_count}")
                
                if prop_count > 0:
                    # プロパティの詳細を表示
                    query4 = """
                    MATCH (od:ObjectDefinition {name: '条材要素のパラメータオブジェクト'})-[:HAS_PROPERTY]->(p:Parameter)
                    RETURN p.name as name, p.description as description
                    ORDER BY p.name
                    LIMIT 5
                    """
                    result4 = session.run(query4)
                    print(f"   最初の5つのプロパティ:")
                    for record in result4:
                        print(f"     - {record['name']}: {record['description']}")
                else:
                    print("   ❌ プロパティが作成されていません")
            else:
                print("   ❌ プロパティの確認に失敗しました")
            
            # 型情報の確認
            print(f"\n4. 型情報の確認:")
            query5 = """
            MATCH (od:ObjectDefinition {name: '条材要素のパラメータオブジェクト'})-[:HAS_PROPERTY]->(p:Parameter)-[:HAS_TYPE]->(t:Type)
            RETURN count(p) as type_count
            """
            result5 = session.run(query5)
            type_count_record = result5.single()
            if type_count_record:
                type_count = type_count_record['type_count']
                print(f"   型情報を持つパラメータ数: {type_count}")
            else:
                print("   ❌ 型情報の確認に失敗しました")
                
    finally:
        driver.close()

if __name__ == "__main__":
    debug_import()
