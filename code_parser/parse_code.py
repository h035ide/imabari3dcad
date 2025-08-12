import os
import sys
import argparse
from dotenv import load_dotenv

# プロジェクトのルートをsys.pathに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# project_rootが正しく設定された後にインポートする
# Note: This will only work if the script is run from the project root directory.
# We might need to adjust this later if we run it from code_parser/
from treesitter_neo4j_advanced import TreeSitterNeo4jAdvancedBuilder

# .envファイルを読み込む
load_dotenv()

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

    print(f"プロジェクトルートパス: {project_root}")
    print(f"Pythonパスに追加されました: {project_root in sys.path}")
    print(f"解析対象ファイル: {args.file_path}")

    # Neo4j接続情報
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USERNAME")
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
