import os
import sys
import argparse
import logging
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_code_generator():
    """AIコード生成アシスタントを実行"""
    try:
        logger.info("AIコード生成アシスタントを起動中...")
        from code_generator.main import main as code_gen_main
        code_gen_main()
    except ImportError as e:
        logger.error(f"コード生成機能のインポートに失敗: {e}")
        return False
    except Exception as e:
        logger.error(f"コード生成機能の実行中にエラー: {e}")
        return False
    return True


def run_test_runner():
    """統合テストを実行"""
    try:
        logger.info("統合テストを実行中...")
        from code_parser.run_tests import main as test_main
        test_main()
    except ImportError as e:
        logger.error(f"テスト実行機能のインポートに失敗: {e}")
        return False
    except Exception as e:
        logger.error(f"テスト実行中にエラー: {e}")
        return False
    return True


def run_doc_parser():
    """APIドキュメント解析を実行"""
    try:
        logger.info("APIドキュメント解析を実行中...")
        from doc_paser.doc_paser import main as doc_parser_main
        doc_parser_main()
    except ImportError as e:
        logger.error(f"ドキュメント解析機能のインポートに失敗: {e}")
        return False
    except Exception as e:
        logger.error(f"ドキュメント解析中にエラー: {e}")
        return False
    return True


def run_all_functions():
    """全ての機能を順次実行"""
    logger.info("全ての機能を順次実行します...")
    
    functions = [
        ("コード生成アシスタント", run_code_generator),
        ("統合テスト実行", run_test_runner),
        ("APIドキュメント解析", run_doc_parser)
    ]
    
    results = {}
    
    for name, func in functions:
        logger.info(f"\n{'='*50}")
        logger.info(f"実行中: {name}")
        logger.info(f"{'='*50}")
        
        try:
            success = func()
            results[name] = "成功" if success else "失敗"
        except Exception as e:
            logger.error(f"{name}の実行中に予期しないエラー: {e}")
            results[name] = "エラー"
    
    # 結果サマリー
    logger.info(f"\n{'='*50}")
    logger.info("実行結果サマリー")
    logger.info(f"{'='*50}")
    
    for name, result in results.items():
        status_icon = "✅" if result == "成功" else "❌"
        logger.info(f"{status_icon} {name}: {result}")
    
    successful_count = sum(1 for result in results.values() if result == "成功")
    total_count = len(results)
    
    logger.info(f"\n成功率: {successful_count}/{total_count} ({(successful_count/total_count)*100:.1f}%)")
    
    return successful_count == total_count


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="imabari3dcad プロジェクトのメインエントリーポイント",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # AIコード生成アシスタントを実行
  python main_0905.py --function code_generator
  
  # 統合テストを実行
  python main_0905.py --function test_runner
  
  # APIドキュメント解析を実行
  python main_0905.py --function doc_parser
  
  # 全ての機能を順次実行
  python main_0905.py --function all
  
  # 利用可能な機能を表示
  python main_0905.py --list-functions
        """
    )
    
    parser.add_argument(
        "--function", "-f",
        choices=["code_generator", "test_runner", "doc_parser", "all"],
        help="実行する機能を選択"
    )
    
    parser.add_argument(
        "--list-functions", "-l",
        action="store_true",
        help="利用可能な機能の一覧を表示"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="詳細なログを出力"
    )
    
    args = parser.parse_args()
    
    # ログレベルを設定
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 利用可能な機能を表示
    if args.list_functions:
        print("利用可能な機能:")
        print("  code_generator  - AIコード生成アシスタント")
        print("  test_runner     - 統合テスト実行")
        print("  doc_parser      - APIドキュメント解析")
        print("  all            - 全ての機能を順次実行")
        return
    
    # 機能が指定されていない場合はヘルプを表示
    if not args.function:
        parser.print_help()
        return
    
    logger.info(f"プロジェクトルート: {project_root}")
    logger.info(f"選択された機能: {args.function}")
    
    try:
        if args.function == "code_generator":
            success = run_code_generator()
        elif args.function == "test_runner":
            success = run_test_runner()
        elif args.function == "doc_parser":
            success = run_doc_parser()
        elif args.function == "all":
            success = run_all_functions()
        else:
            logger.error(f"未対応の機能: {args.function}")
            sys.exit(1)
        
        if success:
            logger.info("✅ 実行が正常に完了しました")
            sys.exit(0)
        else:
            logger.error("❌ 実行中にエラーが発生しました")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("ユーザーによって中断されました")
        sys.exit(1)
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
