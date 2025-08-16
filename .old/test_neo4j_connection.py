#!/usr/bin/env python3
"""
Neo4j接続とAPOCプラグインの確認用テストスクリプト
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

def test_neo4j_connection():
    """Neo4jの接続とAPOCプラグインの確認"""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    db_name = os.getenv("NEO4J_DATABASE")
    
    print(f"接続情報:")
    print(f"  URI: {uri}")
    print(f"  User: {user}")
    print(f"  Database: {db_name}")
    
    if not all([uri, user, password, db_name]):
        print("❌ 環境変数が不足しています")
        return False
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # 接続テスト
        with driver.session(database=db_name) as session:
            # 基本的な接続テスト
            result = session.run("RETURN 1 as test")
            record = result.single()
            print(f"✅ 接続成功: {record['test']}")
            
            # 利用可能なプロシージャを確認
            try:
                result = session.run("CALL dbms.procedures() YIELD name RETURN name LIMIT 10")
                procedures = [record["name"] for record in result]
                print(f"📋 利用可能なプロシージャ (最初の10件):")
                for proc in procedures:
                    print(f"  - {proc}")
                
                # APOCプラグインの確認
                apoc_procedures = [p for p in procedures if p.startswith("apoc.")]
                if apoc_procedures:
                    print(f"✅ APOCプラグインが利用可能です ({len(apoc_procedures)}件)")
                else:
                    print("❌ APOCプラグインが見つかりません")
                    
            except Exception as e:
                print(f"⚠️ プロシージャ一覧の取得に失敗: {e}")
            
            # データベースの基本情報
            try:
                result = session.run("CALL db.info() YIELD name, version, edition")
                info = result.single()
                if info:
                    print(f"📊 データベース情報:")
                    print(f"  - 名前: {info['name']}")
                    print(f"  - バージョン: {info['version']}")
                    print(f"  - エディション: {info['edition']}")
            except Exception as e:
                print(f"⚠️ データベース情報の取得に失敗: {e}")
                
        driver.close()
        return True
        
    except Exception as e:
        print(f"❌ 接続エラー: {e}")
        return False

if __name__ == "__main__":
    print("=== Neo4j接続テスト ===")
    success = test_neo4j_connection()
    if success:
        print("\n✅ テスト完了")
    else:
        print("\n❌ テスト失敗")
