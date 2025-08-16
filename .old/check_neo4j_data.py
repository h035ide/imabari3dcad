import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase

# プロジェクトルートをパスに追加
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# .envファイルを読み込み
load_dotenv(dotenv_path=os.path.join(project_root, '.env'))

# 環境変数を取得
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

def check_neo4j_data():
    """Neo4jデータベースの現在の状態を確認します。"""
    print("=== Neo4jデータベース状態確認 ===")
    print(f"接続先: {NEO4J_URI}")
    print(f"データベース: {NEO4J_DATABASE}")
    print()
    
    try:
        with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver:
            with driver.session(database=NEO4J_DATABASE) as session:
                
                # 1. すべてのラベルを取得
                print("1. データベース内のすべてのラベル:")
                result = session.run("CALL db.labels() YIELD label RETURN label ORDER BY label")
                labels = [record["label"] for record in result]
                if labels:
                    for label in labels:
                        print(f"   - {label}")
                else:
                    print("   ラベルが見つかりません")
                print()
                
                # 2. 各ラベルのノード数を取得
                if labels:
                    print("2. 各ラベルのノード数:")
                    for label in labels:
                        result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                        count = result.single()["count"]
                        print(f"   {label}: {count}件")
                    print()
                
                # 3. APIFunctionノードの詳細を確認
                print("3. APIFunctionノードの詳細:")
                result = session.run("MATCH (n:APIFunction) RETURN n LIMIT 5")
                apifunctions = list(result)
                if apifunctions:
                    for i, record in enumerate(apifunctions):
                        node = record["n"]
                        print(f"   ノード {i+1}:")
                        print(f"     ID: {node.element_id}")
                        print(f"     プロパティ: {dict(node)}")
                        print()
                else:
                    print("   APIFunctionノードが見つかりません")
                print()
                
                # 4. 全ノードのプロパティキーを確認（簡易版）
                print("4. 全ノードのプロパティキー（簡易版）:")
                result = session.run("MATCH (n) RETURN labels(n) as labels, keys(n) as properties LIMIT 10")
                schemas = list(result)
                if schemas:
                    for schema in schemas:
                        labels = schema["labels"]
                        properties = schema["properties"]
                        if labels and properties:
                            print(f"   ラベル {labels}: {properties}")
                else:
                    print("   スキーマ情報が取得できませんでした")
                print()
                
                # 5. サンプルデータの確認
                print("5. サンプルデータ（最初の5件）:")
                result = session.run("MATCH (n) RETURN labels(n) as labels, n LIMIT 5")
                samples = list(result)
                if samples:
                    for i, record in enumerate(samples):
                        labels = record["labels"]
                        node = record["n"]
                        print(f"   サンプル {i+1}:")
                        print(f"     ラベル: {labels}")
                        print(f"     プロパティ: {dict(node)}")
                        print()
                else:
                    print("   データが見つかりません")
                
                # 6. データベースの基本情報
                print("6. データベースの基本情報:")
                try:
                    result = session.run("CALL dbms.components() YIELD name, versions, edition")
                    components = list(result)
                    for component in components:
                        print(f"   コンポーネント: {component['name']}")
                        print(f"     バージョン: {component['versions']}")
                        print(f"     エディション: {component['edition']}")
                        print()
                except Exception as e:
                    print(f"   コンポーネント情報の取得に失敗: {e}")
                
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_neo4j_data()
