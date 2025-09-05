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
        print("LLM ドキュメント処理を実行中...")
        # ここに実際の処理を実装
        return True
    except Exception as e:
        print(f"エラー: {e}")
        return False


# def run_code_generator():
#     """AIコード生成アシスタントを実行"""
#     try:
#         from code_generator.main import main as code_gen_main
#         code_gen_main()
#         return True
#     except Exception as e:
#         print(f"エラー: {e}")
#         return False


# def run_test_runner():
#     """統合テストを実行"""
#     try:
#         from code_parser.run_tests import main as test_main
#         test_main()
#         return True
#     except Exception as e:
#         print(f"エラー: {e}")
#         return False


# def run_doc_parser():
#     """APIドキュメント解析を実行"""
#     try:
#         from doc_paser.doc_paser import main as doc_parser_main
#         doc_parser_main()
#         return True
#     except Exception as e:
#         print(f"エラー: {e}")
#         return False



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
    
    config = Config()
    
    if args.function == "nollm_doc":
        success = run_nollm_doc()
    elif args.function == "llm_doc":
        success = run_llm_doc()
    
    if success:
        print("✅ 完了")
    else:
        print("❌ エラー")
        sys.exit(1)


if __name__ == "__main__":
    main()
