import os
import sys
import argparse
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# Tree-sitter Neo4jビルダーのインポート
from code_parser.treesitter_neo4j_advanced import TreeSitterNeo4jAdvancedBuilder

def main():
    """
    Pythonコードファイルを解析し、その構文構造をNeo4jデータベースに格納します。
    """
    parser = argparse.ArgumentParser(description="Pythonコードを解析してNeo4jに格納します。")
    parser.add_argument(
        "file_path",
        nargs='?',
        default="evoship/create_test.py",
        help="解析対象のPythonファイルへのパス (デフォルト: evoship/create_test.py)"
    )
    parser.add_argument("--db-name", default="treesitter", help="使用するNeo4jデータベース名")
    parser.add_argument("--no-llm", action="store_true", help="LLMによる分析を無効にする")
    args = parser.parse_args()

    # プロジェクトルートの取得（uv run での実行を前提）
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # ファイルパスを絶対パスに変換
    if not os.path.isabs(args.file_path):
        args.file_path = os.path.join(project_root, args.file_path)

    print(f"プロジェクトルートパス: {project_root}")
    print(f"解析対象ファイル（絶対パス）: {args.file_path}")

    # Neo4j接続情報
    neo4j_uri = os.getenv("NEO4J_URI")
    # 環境変数は NEO4J_USER と NEO4J_USERNAME の両方に対応
    neo4j_user = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER")
    neo4j_password = os.getenv("NEO4J_PASSWORD")

    if not all([neo4j_uri, neo4j_user, neo4j_password]):
        print("エラー: Neo4jの接続情報 (NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD) が.envファイルに設定されていないか、.envファイルが見つかりません。")
        return

    # Tree-sitter Neo4jビルダーの作成
    builder = TreeSitterNeo4jAdvancedBuilder(
        neo4j_uri,
        neo4j_user,
        neo4j_password,
        database_name=args.db_name,
        enable_llm=not args.no_llm
    )

    # ファイル解析
    if not os.path.exists(args.file_path):
        print(f"エラー: 指定されたファイルが見つかりません: {args.file_path}")
        return

    try:
        builder.analyze_file(args.file_path)

        # Neo4jへの格納
        builder.store_to_neo4j()

        print("処理が正常に完了しました。")
    except Exception as e:
        print(f"処理中にエラーが発生しました: {e}")

if __name__ == "__main__":
    main()
