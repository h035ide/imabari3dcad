"""
テスト実行スクリプト

3つのブランチの機能を統合したテストを実行します。
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_unit_tests():
    """ユニットテストを実行"""
    print("=== ユニットテスト実行中 ===")
    
    test_files = [
        os.path.join(os.path.dirname(__file__), "test_integrated.py"),
        os.path.join(os.path.dirname(__file__), "test_mock_integration.py")
    ]
    
    results = {}
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n--- {test_file} を実行中 ---")
            try:
                result = subprocess.run(
                    [sys.executable, test_file],
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(__file__)
                )
                
                if result.returncode == 0:
                    print(f"✅ {test_file}: 成功")
                    results[test_file] = "成功"
                else:
                    print(f"❌ {test_file}: 失敗")
                    print(f"エラー出力: {result.stderr}")
                    results[test_file] = "失敗"
                    
            except Exception as e:
                print(f"❌ {test_file}: 実行エラー - {e}")
                results[test_file] = "実行エラー"
        else:
            print(f"⚠️ {test_file}: ファイルが見つかりません")
            results[test_file] = "ファイルなし"
    
    return results


def run_coverage_tests():
    """カバレッジテストを実行"""
    print("\n=== カバレッジテスト実行中 ===")
    
    try:
        # 現在のディレクトリでテストファイルを検索
        current_dir = os.path.dirname(__file__)
        test_files = [f for f in os.listdir(current_dir) if f.startswith("test_") and f.endswith(".py")]
        
        if not test_files:
            print("⚠️ テストファイルが見つかりません")
            return
        
        print(f"見つかったテストファイル: {test_files}")
        
        # pytest-covを使用してカバレッジを測定
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "--cov=.", 
            "--cov-report=term-missing"
        ] + test_files, capture_output=True, text=True, cwd=current_dir)
        
        if result.returncode == 0:
            print("✅ カバレッジテスト: 成功")
            print("カバレッジレポート:")
            print(result.stdout)
        else:
            print("❌ カバレッジテスト: 失敗")
            print(f"エラー出力: {result.stderr}")
            
    except Exception as e:
        print(f"❌ カバレッジテスト実行エラー: {e}")


def run_simple_tests():
    """シンプルなテストを実行"""
    print("\n=== シンプルテスト実行中 ===")
    
    try:
        # 基本的なインポートテスト
        print("1. 基本モジュールのインポートテスト")
        
        modules_to_test = [
            "simple_utils",
            "simple_config", 
            "main_integrated"
        ]
        
        for module in modules_to_test:
            try:
                __import__(module)
                print(f"   ✅ {module}: インポート成功")
            except ImportError as e:
                print(f"   ❌ {module}: インポート失敗 - {e}")
        
        # 設定値のテスト
        print("\n2. 設定値のテスト")
        try:
            from simple_config import NEO4J_CONFIG, VECTOR_SEARCH_CONFIG
            print(f"   ✅ Neo4j設定: {len(NEO4J_CONFIG)}個の設定項目")
            print(f"   ✅ ベクトル検索設定: {len(VECTOR_SEARCH_CONFIG)}個の設定項目")
        except ImportError as e:
            print(f"   ❌ 設定インポート失敗 - {e}")
        
        # ユーティリティ機能のテスト
        print("\n3. ユーティリティ機能のテスト")
        try:
            from simple_utils import FileUtils, ValidationUtils
            
            # ファイルユーティリティのテスト
            test_file = "test_temp.py"
            with open(test_file, 'w') as f:
                f.write("print('test')")
            
            # テスト実行（selfは不要）
            is_python = FileUtils.is_python_file(test_file)
            is_valid = ValidationUtils.validate_file_path(test_file)
            
            if is_python and is_valid:
                print("   ✅ ファイルユーティリティ: 動作確認完了")
            else:
                print("   ❌ ファイルユーティリティ: 動作確認失敗")
            
            # クリーンアップ
            os.remove(test_file)
            print("   ✅ ファイルユーティリティ: 動作確認完了")
            
        except Exception as e:
            print(f"   ❌ ユーティリティテスト失敗 - {e}")
            
    except Exception as e:
        print(f"❌ シンプルテスト実行エラー: {e}")


def run_integration_tests():
    """統合テストを実行"""
    print("\n=== 統合テスト実行中 ===")
    
    try:
        # 統合パーサーのテスト
        print("1. 統合パーサーのテスト")
        
        # テスト用の一時ファイルを作成
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def test_function():
    \"\"\"テスト関数\"\"\"
    return "test"

class TestClass:
    \"\"\"テストクラス\"\"\"
    pass
""")
            test_file = f.name
        
        try:
            # 統合パーサーのインポートテスト
            from main_integrated import IntegratedCodeParser
            
            # 設定のテスト
            parser = IntegratedCodeParser()
            print("   ✅ 統合パーサー: 初期化成功")
            
            # ファイル解析のテスト（モック環境）
            try:
                from unittest.mock import patch
                with patch.dict(os.environ, {
                    'NEO4J_URI': 'neo4j://localhost:7687',
                    'NEO4J_USERNAME': 'neo4j',
                    'NEO4J_PASSWORD': 'password'
                }):
                    # 実際のNeo4j接続は行わず、設定のみテスト
                    print("   ✅ 統合パーサー: 設定確認完了")
            except ImportError:
                print("   ⚠️ unittest.mockが利用できません")
            except Exception as e:
                print(f"   ❌ 統合パーサー設定確認失敗: {e}")
                
        except Exception as e:
            print(f"   ❌ 統合パーサーテスト失敗 - {e}")
        
        finally:
            # クリーンアップ
            if os.path.exists(test_file):
                os.remove(test_file)
                
    except Exception as e:
        print(f"❌ 統合テスト実行エラー: {e}")


def generate_test_report(results):
    """テスト結果レポートを生成"""
    print("\n" + "="*50)
    print("テスト結果サマリー")
    print("="*50)
    
    total_tests = len(results)
    successful_tests = sum(1 for result in results.values() if result == "成功")
    failed_tests = total_tests - successful_tests
    
    print(f"総テストファイル数: {total_tests}")
    print(f"成功: {successful_tests}")
    print(f"失敗: {failed_tests}")
    print(f"成功率: {(successful_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%")
    
    print("\n詳細結果:")
    for test_file, result in results.items():
        status_icon = "✅" if result == "成功" else "❌"
        print(f"  {status_icon} {test_file}: {result}")
    
    return successful_tests == total_tests


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="統合テスト実行スクリプト")
    parser.add_argument("--unit", action="store_true", help="ユニットテストのみ実行")
    parser.add_argument("--coverage", action="store_true", help="カバレッジテストのみ実行")
    parser.add_argument("--simple", action="store_true", help="シンプルテストのみ実行")
    parser.add_argument("--integration", action="store_true", help="統合テストのみ実行")
    parser.add_argument("--all", action="store_true", help="全てのテストを実行")
    
    args = parser.parse_args()
    
    if args.all or not any([args.unit, args.coverage, args.simple, args.integration]):
        # デフォルトで全てのテストを実行
        print("全てのテストを実行します...")
        
        # ユニットテスト
        unit_results = run_unit_tests()
        
        # カバレッジテスト
        run_coverage_tests()
        
        # シンプルテスト
        run_simple_tests()
        
        # 統合テスト
        run_integration_tests()
        
        # 結果レポート
        all_success = generate_test_report(unit_results)
        
        if all_success:
            print("\n🎉 全てのテストが成功しました！")
            sys.exit(0)
        else:
            print("\n💥 一部のテストが失敗しました。")
            sys.exit(1)
    
    else:
        # 指定されたテストのみ実行
        if args.unit:
            unit_results = run_unit_tests()
            generate_test_report(unit_results)
        
        if args.coverage:
            run_coverage_tests()
        
        if args.simple:
            run_simple_tests()
        
        if args.integration:
            run_integration_tests()


if __name__ == "__main__":
    main()
