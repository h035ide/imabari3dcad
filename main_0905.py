import sys
import argparse
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class Config:
    """設定クラス"""

    def __init__(self):
        self.project_root = project_root

        # Neo4j設定
        self.neo4j_uri = "neo4j://127.0.0.1:7687"
        self.neo4j_user = "neo4j"
        self.neo4j_password = "password"
        self.neo4j_database = "neo4j"

        # ファイルパス設定
        self.parsed_api_result_def_file = (
            "doc_parser/parsed_api_result_def.json"
        )
        self.parsed_api_result_file = "doc_parser/parsed_api_result.json"

        # Chroma設定
        self.chroma_persist_directory = "chroma_db_store"
        self.chroma_collection_name = "api_documentation"


def run_nollm_doc():
    """No LLM ドキュメント処理を実行"""
    try:
        print("No LLM ドキュメント処理を実行中...")
        # ここに実際の処理を実装
        return True
    except Exception as e:
        print(f"エラー: {e}")
        return False


def run_llm_doc():
    """LLM ドキュメント処理を実行"""
    try:
        from doc_parser.neo4j_importer import import_to_neo4j

        # Configから設定を取得
        config = Config()

        # Neo4jにデータをインポート
        success = import_to_neo4j(
            uri=config.neo4j_uri,
            user=config.neo4j_user,
            password=config.neo4j_password,
            database=config.neo4j_database,
            file_path=config.parsed_api_result_def_file,
            use_def_file=True,
        )

        if success:
            # Neo4jインポート成功後、Chromaにベクトル化
            print("Neo4jインポート完了。Chromaにベクトル化を開始...")
            vectorize_success = run_vectorization()
            return vectorize_success

        return success
    except Exception as e:
        print(f"エラー: {e}")
        return False


def run_vectorization():
    """APIドキュメントをChromaにベクトル化"""
    try:
        from code_generator.db.ingest_to_chroma import (
            fetch_data_from_neo4j,
            ingest_data_to_chroma
        )

        # Configから設定を取得
        config = Config()

        print("Neo4jからAPIデータを取得中...")
        # Functionノードを取得（Neo4jのラベルに合わせて調整）
        records = fetch_data_from_neo4j(
            label="Function",
            db_name=config.neo4j_database,
            allow_missing_description=True
        )

        if not records:
            print("ベクトル化するデータが見つかりませんでした。")
            return False

        print(f"{len(records)}件のAPI関数をベクトル化中...")
        # Chromaにベクトル化して保存
        ingest_data_to_chroma(
            records=records,
            collection_name=config.chroma_collection_name,
            persist_dir=config.chroma_persist_directory
        )

        print("✅ Chromaベクトル化完了")
        return True

    except Exception as e:
        print(f"ベクトル化エラー: {e}")
        return False


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="imabari3dcad メイン")
    parser.add_argument("--function", "-f", help="実行する機能")
    parser.add_argument("--list", "-l", action="store_true", help="機能一覧表示")

    args = parser.parse_args()

    # if args.list:
    #     print("利用可能な機能:")
    #     print("  code_generator  - AIコード生成")
    #     print("  test_runner     - テスト実行")
    #     print("  doc_parser      - ドキュメント解析")
    #     print("  all            - 全機能実行")
    #     return

    print(f"実行中: {args.function}")

    if args.function == "nollm_doc":
        success = run_nollm_doc()
    elif args.function == "llm_doc":
        success = run_llm_doc()
    elif args.function == "vectorize":
        success = run_vectorization()
    else:
        print(f"未知の機能: {args.function}")
        success = False

    if success:
        print("✅ 完了")
    else:
        print("❌ エラー")
        sys.exit(1)


if __name__ == "__main__":
    main()
