import os
import sys
import argparse
import logging
from dotenv import load_dotenv

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_project_root():
    """プロジェクトのルートパスをsys.pathに追加します。"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        logging.info(f"プロジェクトルートをPythonパスに追加しました: {project_root}")
    return project_root

# プロジェクトルートを設定してからインポート
setup_project_root()

# 相対インポートを絶対インポートに変更
from core.api_parser import ApiParser
from core.code_parser import CodeParser
from core.neo4j_uploader import Neo4jUploader

def main():
    """
    データベース統合プロセスのメインエントリーポイント。
    API仕様とPythonコードを解析し、Neo4jデータベースに格納して両者をリンクします。
    """
    load_dotenv()

    parser = argparse.ArgumentParser(description="API仕様書とPythonコードを解析し、Neo4jに統合します。")
    parser.add_argument("--code-file", required=True, help="解析対象のPythonソースファイルへのパス。")
    parser.add_argument("--api-doc", required=True, help="API関数仕様が書かれたテキストファイルへのパス。")
    parser.add_argument("--api-args", required=True, help="API引数仕様が書かれたテキストファイルへのパス。")
    parser.add_argument("--db-name", default="unifieddb", help="使用するNeo4jデータベース名。")
    parser.add_argument("--clear-db", action="store_true", help="実行前にデータベースをクリアします。")
    parser.add_argument("--no-llm", action="store_true", help="LLMによる分析を無効にします。")

    args = parser.parse_args()

    logging.info("データベース統合プロセスを開始します。")
    logging.info(f"  - Pythonソースファイル: {args.code_file}")
    logging.info(f"  - APIドキュメント: {args.api_doc}, {args.api_args}")
    logging.info(f"  - Neo4jデータベース: {args.db_name}")

    try:
        # 1. Neo4jの接続情報を取得
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_user = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
        neo4j_password = os.getenv("NEO4J_PASSWORD")

        if not all([neo4j_uri, neo4j_user, neo4j_password]):
            raise ValueError("Neo4jの接続情報 (.envファイル) が不足しています。")

        # --- リファクタリングしたモジュールを呼び出す ---

        # 2. 各モジュールのインスタンス化
        uploader = Neo4jUploader(neo4j_uri, neo4j_user, neo4j_password, args.db_name)
        api_parser = ApiParser()
        code_parser = CodeParser(enable_llm=not args.no_llm)

        # 3. (オプション) データベースのクリア
        if args.clear_db:
            uploader.clear_database()

        # 4. API仕様の解析とインポート
        logging.info("API仕様の解析とインポートを開始します...")
        api_data = api_parser.parse(args.api_doc, args.api_args)
        uploader.upload_api_data(api_data)

        # 5. Pythonコードの解析とインポート
        logging.info("Pythonコードの解析とインポートを開始します...")
        nodes, relations = code_parser.parse_file(args.code_file)
        uploader.upload_code_data(nodes, relations)

        # 6. グラフのリンク
        logging.info("API仕様とコード実装のリンクを作成します...")
        uploader.link_graphs()

        # 7. 接続を閉じる
        uploader.close()

        logging.info("データベース統合プロセスが正常に完了しました。")

    except Exception as e:
        logging.error(f"エラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
