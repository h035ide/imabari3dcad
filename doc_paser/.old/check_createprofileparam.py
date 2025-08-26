#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CreateProfileParamのパラメータの型情報を確認するスクリプト
"""

import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

def check_createprofileparam():
    """CreateProfileParamのパラメータの型情報を確認"""
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
            # CreateProfileParamのパラメータの型情報を確認
            query = """
            MATCH (od:ObjectDefinition {name: '条材要素のパラメータオブジェクト'})-[:HAS_PROPERTY]->(p:Parameter)
            OPTIONAL MATCH (p)-[:HAS_TYPE]->(t:Type)
            RETURN p.name as param_name, t.name as type_name, p.description as description
            ORDER BY p.name
            """
            
            result = session.run(query)
            print('=== CreateProfileParam パラメータの型情報 ===')
            param_count = 0
            type_count = 0
            
            for record in result:
                param_name = record['param_name']
                type_name = record['type_name']
                description = record['description']
                
                if type_name:
                    print(f'✅ {param_name}: {type_name} - {description}')
                    type_count += 1
                else:
                    print(f'❌ {param_name}: 型情報なし - {description}')
                
                param_count += 1
            
            print(f'\n=== 結果サマリー ===')
            print(f'総パラメータ数: {param_count}')
            print(f'型情報を持つパラメータ数: {type_count}')
            print(f'型情報なしのパラメータ数: {param_count - type_count}')
            
            if type_count == param_count:
                print('🎉 すべてのパラメータが正しく型情報と関連付けられています！')
            else:
                print('⚠️  一部のパラメータに型情報が不足しています。')
                
    finally:
        driver.close()

if __name__ == "__main__":
    check_createprofileparam()
