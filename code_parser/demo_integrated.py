"""
統合デモスクリプト - 3つのブランチの機能を統合したデモ

このスクリプトは以下の機能をデモンストレーションします：
1. Tree-sitterによるPythonコード解析
2. ベクトル検索による意味的検索
3. LLMによる高度なコード分析
4. パフォーマンス最適化
"""

import os
import sys
import tempfile
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from simple_utils import FileUtils, ValidationUtils, PerformanceUtils
from simple_config import NEO4J_CONFIG, VECTOR_SEARCH_CONFIG, LLM_CONFIG


def demo_file_utilities():
    """ファイルユーティリティのデモ"""
    print("=== ファイルユーティリティのデモ ===")
    
    # 一時ディレクトリの作成
    temp_dir = tempfile.mkdtemp()
    print(f"一時ディレクトリを作成: {temp_dir}")
    
    # テスト用Pythonファイルの作成
    test_file = os.path.join(temp_dir, "demo_function.py")
    test_code = '''
def calculate_fibonacci(n):
    """フィボナッチ数列のn番目の値を計算"""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def factorial(n):
    """階乗を計算"""
    if n <= 1:
        return 1
    return n * factorial(n-1)

class MathUtils:
    """数学ユーティリティクラス"""
    
    @staticmethod
    def is_prime(n):
        """素数判定"""
        if n < 2:
            return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True
'''
    
    with open(test_file, 'w') as f:
        f.write(test_code)
    
    print(f"テストファイルを作成: {test_file}")
    
    # ファイルユーティリティのテスト
    print("\n1. ファイル存在確認:")
    print(f"   ファイル存在: {ValidationUtils.validate_file_path(test_file)}")
    
    print("\n2. Pythonファイル判定:")
    print(f"   Pythonファイル: {FileUtils.is_python_file(test_file)}")
    print(f"   テキストファイル: {FileUtils.is_python_file('test.txt')}")
    
    print("\n3. ファイルハッシュ取得:")
    file_hash = FileUtils.get_file_hash(test_file)
    print(f"   ファイルハッシュ: {file_hash[:16]}...")
    
    print("\n4. Pythonファイル検索:")
    python_files = FileUtils.find_python_files(temp_dir, recursive=False)
    print(f"   見つかったPythonファイル: {len(python_files)}個")
    for file_path in python_files:
        print(f"     - {os.path.basename(file_path)}")
    
    # クリーンアップ
    import shutil
    shutil.rmtree(temp_dir)
    print(f"\n一時ディレクトリを削除: {temp_dir}")


def demo_validation_utilities():
    """バリデーションユーティリティのデモ"""
    print("\n=== バリデーションユーティリティのデモ ===")
    
    print("1. Neo4j設定のバリデーション:")
    valid_configs = [
        ("neo4j://localhost:7687", "neo4j", "password"),
        ("bolt://localhost:7687", "neo4j", "password"),
        ("neo4j+s://localhost:7687", "neo4j", "password")
    ]
    
    for uri, user, password in valid_configs:
        is_valid = ValidationUtils.validate_neo4j_config(uri, user, password)
        print(f"   {uri}: {'✅ 有効' if is_valid else '❌ 無効'}")
    
    print("\n2. Pythonコードのバリデーション:")
    test_codes = [
        ("print('hello')", "有効なコード"),
        ("def test(): pass", "有効な関数定義"),
        ("print('hello'", "構文エラー"),
        ("", "空のコード"),
        ("   ", "空白のみ")
    ]
    
    for code, description in test_codes:
        is_valid = ValidationUtils.validate_python_code(code)
        status = "✅ 有効" if is_valid else "❌ 無効"
        print(f"   {description}: {status}")


def demo_performance_utilities():
    """パフォーマンスユーティリティのデモ"""
    print("\n=== パフォーマンスユーティリティのデモ ===")
    
    print("1. 時間測定デコレータ:")
    
    @PerformanceUtils.measure_time
    def demo_function():
        """デモ用の関数"""
        import time
        time.sleep(0.1)  # 100ms待機
        return "完了"
    
    result = demo_function()
    print(f"   関数実行結果: {result}")
    
    print("\n2. 関数ベンチマーク:")
    
    def benchmark_target():
        """ベンチマーク対象の関数"""
        import time
        time.sleep(0.01)  # 10ms待機
    
    benchmark_results = PerformanceUtils.benchmark_function(
        benchmark_target, iterations=5
    )
    
    print("   ベンチマーク結果:")
    for key, value in benchmark_results.items():
        if isinstance(value, float):
            print(f"     {key}: {value:.4f}秒")
        else:
            print(f"     {key}: {value}")


def demo_configuration():
    """設定のデモ"""
    print("\n=== 設定のデモ ===")
    
    print("1. Neo4j設定:")
    for key, value in NEO4J_CONFIG.items():
        if key == "password":
            display_value = "*" * len(str(value)) if value else "未設定"
        else:
            display_value = value
        print(f"   {key}: {display_value}")
    
    print("\n2. ベクトル検索設定:")
    for key, value in VECTOR_SEARCH_CONFIG.items():
        print(f"   {key}: {value}")
    
    print("\n3. LLM設定:")
    for key, value in LLM_CONFIG.items():
        if key == "api_key":
            display_value = "*" * 20 if value else "未設定"
        else:
            display_value = value
        print(f"   {key}: {display_value}")


def demo_integration():
    """統合機能のデモ"""
    print("\n=== 統合機能のデモ ===")
    
    print("1. 統合パーサーのインポートテスト:")
    try:
        from main_integrated import IntegratedCodeParser
        print("   ✅ 統合パーサーのインポート成功")
        
        # 環境変数の設定（テスト用）
        test_env = {
            'NEO4J_URI': 'neo4j://localhost:7687',
            'NEO4J_USERNAME': 'neo4j',
            'NEO4J_PASSWORD': 'password'
        }
        
        # 統合パーサーの初期化テスト
        with patch.dict(os.environ, test_env):
            parser = IntegratedCodeParser()
            print("   ✅ 統合パーサーの初期化成功")
            
    except ImportError as e:
        print(f"   ❌ 統合パーサーのインポート失敗: {e}")
    except Exception as e:
        print(f"   ❌ 統合パーサーの初期化失敗: {e}")
    
    print("\n2. ベクトル検索エンジンのインポートテスト:")
    try:
        from vector_search import VectorSearchEngine
        print("   ✅ ベクトル検索エンジンのインポート成功")
    except ImportError as e:
        print(f"   ❌ ベクトル検索エンジンのインポート失敗: {e}")
    
    print("\n3. LLM分析器のインポートテスト:")
    try:
        from enhanced_llm_analyzer import EnhancedLLMAnalyzer
        print("   ✅ LLM分析器のインポート成功")
    except ImportError as e:
        print(f"   ❌ LLM分析器のインポート失敗: {e}")


def main():
    """メイン関数"""
    print("統合コードパーサーのデモを開始します...")
    print("=" * 60)
    
    try:
        # 各機能のデモを実行
        demo_file_utilities()
        demo_validation_utilities()
        demo_performance_utilities()
        demo_configuration()
        demo_integration()
        
        print("\n" + "=" * 60)
        print("🎉 デモが正常に完了しました！")
        print("\n次のステップ:")
        print("1. 実際のPythonファイルで解析を試す")
        print("2. Neo4jデータベースに接続してテスト")
        print("3. ベクトル検索でコードを検索")
        print("4. LLM分析でコードの詳細分析")
        
    except Exception as e:
        print(f"\n❌ デモ実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # unittest.mockのpatchをインポート
    try:
        from unittest.mock import patch
    except ImportError:
        print("unittest.mockが利用できません。Python 3.3以降が必要です。")
        sys.exit(1)
    
    main()
