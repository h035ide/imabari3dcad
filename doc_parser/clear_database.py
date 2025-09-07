# Neo4jデータベースを完全にクリアするスクリプト
import os
import sys
import argparse
from neo4j import GraphDatabase
from dotenv import load_dotenv


def clear_database(database: str, force: bool = False):
    """指定した Neo4j データベースの全ノード・関係を削除します。

    引数:
        database: クリア対象のデータベース名
        force: True のときのみ実行（安全のためのフラグ）
    """
    load_dotenv()

    # フラグの最終決定（環境変数でも上書き可能）
    env_force = os.getenv("CLEAR_DATABASE", "").lower() in {"1", "true", "yes"}
    should_run = force or env_force
    if not should_run:
        print(
            (
                "安全のため実行をスキップしました。--yes/-y フラグ、または環境変数 "
                "CLEAR_DATABASE=1 を指定してください。"
            )
        )
        return

    NEO4J_URI = os.getenv("NEO4J_URI")
    # NEO4J_USER と NEO4J_USERNAME の両方に対応
    NEO4J_USER = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print(
            (
                "Error: NEO4J_URI, NEO4J_USER (or NEO4J_USERNAME), and "
                "NEO4J_PASSWORD must be set in the .env file."
            )
        )
        return

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        # まずsystemデータベースで対象データベースの存在確認
        with driver.session(database="system") as session:
            print("=== 対象データベースの確認 ===")
            result = session.run("SHOW DATABASES")
            databases = [record["name"] for record in result]

            if database not in databases:
                print(f"データベース '{database}' が存在しません。作成します...")
                session.run(f"CREATE DATABASE {database}")
                print(f"データベース '{database}' を作成しました。")
            else:
                print(f"データベース '{database}' が存在します。")

        # 対象データベースでデータをクリア
        with driver.session(database=database) as session:
            print(f"\n=== データベース '{database}' のクリアを開始 ===")

            # すべての関係を削除
            print("すべての関係を削除中...")
            session.run("MATCH ()-[r]-() DELETE r")
            print("  関係の削除完了")

            # すべてのノードを削除
            print("すべてのノードを削除中...")
            session.run("MATCH (n) DELETE n")
            print("  ノードの削除完了")

            print(f"\n=== データベース '{database}' のクリア完了 ===")

            # 現在の状態を確認
            print("\n=== 現在の状態 ===")
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            node_count = result.single()['node_count']
            print(f"  ノード数: {node_count}")

            result = session.run(
                "MATCH ()-[r]->() RETURN count(r) as rel_count"
            )
            rel_count = result.single()['rel_count']
            print(f"  関係数: {rel_count}")

    finally:
        driver.close()


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Neo4j データベースをクリアするユーティリティ",
    )
    parser.add_argument(
        "--db",
        dest="database",
        default=os.getenv("NEO4J_DATABASE", "docparser"),
        help=(
            "クリア対象のデータベース名（既定: 環境変数 NEO4J_DATABASE または "
            "'docparser'）"
        ),
    )
    parser.add_argument(
        "-y",
        "--yes",
        dest="force",
        action="store_true",
        help="確認なしで実行（非対話/CI 向け）",
    )
    return parser.parse_args()


if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    args = _parse_args()
    clear_database(database=args.database, force=args.force)
