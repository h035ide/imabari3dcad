import json
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
load_dotenv()

# --- 1. Neo4jへの接続情報 ---
NEO4J_URI = os.environ.get("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "your_password") # ご自身のパスワードに変更してください

# --- 2. LLMでリッチ化されたJSONファイルの読み込み ---
input_filename = 'api_functions_data_enriched.json'
try:
    with open(input_filename, 'r', encoding='utf-8') as f:
        functions_data = json.load(f)
except FileNotFoundError:
    print(f"エラー: {input_filename} が見つかりません。")
    exit()


# --- 3. Neo4jへのデータ登録ロジック (改善版) ---
def upload_function_to_neo4j(tx, func_data):
    """
    一つの関数データをNeo4jに登録するためのトランザクション処理
    """
    # 【改善点②】Functionノードのプロパティをクリーンなデータで作成
    tx.run("""
        MERGE (f:Function {name: $func_name})
        SET f.description = $description
        """,
        func_name=func_data["name"],
        description=func_data.get("description", "") # 説明文をセット
    )

    # 返り値のTypeノードと、Functionとのリレーションシップを作成
    if func_data.get("returns") and func_data["returns"].get("type_name"):
        tx.run("""
            MATCH (f:Function {name: $func_name})
            MERGE (t:Type {name: $type_name})
            MERGE (f)-[:RETURNS]->(t)
            """,
            func_name=func_data["name"],
            type_name=func_data["returns"]["type_name"] # 返り値の型名を正しく使用
        )

    # 【改善点①】引数モデルを :Argument に統一
    # :Parameter ノードの作成ロジックは含めず、:Argument のみを使用
    for param in func_data.get("params", []):
        # Argumentノードを作成。LLMで付加した情報もプロパティに含める
        tx.run("""
            MERGE (a:Argument {name: $param_name})
            SET
                a.description = $desc,
                a.summary = $summary,
                a.constraints = $constraints
            """,
            param_name=param["name"],
            desc=param.get("description_raw", ""),
            summary=param.get("summary_llm", ""),
            constraints=param.get("constraints_llm", [])
        )

        # Typeノードを作成
        tx.run("MERGE (t:Type {name: $type_name})", type_name=param["type_name"])

        # Function と Argument のリレーションシップを作成
        tx.run("""
            MATCH (f:Function {name: $func_name})
            MATCH (a:Argument {name: $param_name})
            MERGE (f)-[:HAS_ARGUMENT]->(a)
            """,
            func_name=func_data["name"],
            param_name=param["name"]
        )

        # Argument と Type のリレーションシップを作成
        tx.run("""
            MATCH (a:Argument {name: $param_name})
            MATCH (t:Type {name: $type_name})
            MERGE (a)-[:HAS_TYPE]->(t)
            """,
            param_name=param["name"],
            type_name=param["type_name"]
        )

# --- 4. メイン処理の実行 ---
print("Neo4jへのデータ登録を開始します...")
try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session(database="neo4j") as session:
        # 全ての関数データをループして登録処理を実行
        for i, func in enumerate(functions_data):
            print(f"[{i+1}/{len(functions_data)}] Registering function: {func['name']}")
            session.execute_write(upload_function_to_neo4j, func)
    print("\n--- 処理完了 ---")
    print("すべてのデータがNeo4jに登録されました。")
finally:
    if 'driver' in locals() and driver:
        driver.close()