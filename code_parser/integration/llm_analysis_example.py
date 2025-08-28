"""
LLM分析機能の使用例

このファイルは、高度なLLM分析機能の使用方法を示します。
"""

import json
from pathlib import Path
from llm_analysis_utils import LLMAnalysisManager
from analysis_schemas import SyntaxNode


def example_function_analysis():
    """関数分析の使用例"""
    print("=== 関数分析の例 ===")
    
    # 分析マネージャーの初期化
    manager = LLMAnalysisManager()
    
    # サンプル関数コード
    sample_function = """
def calculate_fibonacci(n: int) -> int:
    '''
    フィボナッチ数列のn番目の値を計算する
    
    Args:
        n: 計算する位置（0以上の整数）
        
    Returns:
        int: フィボナッチ数列のn番目の値
        
    Raises:
        ValueError: nが負の数の場合
    '''
    if n < 0:
        raise ValueError("nは0以上の整数である必要があります")
    
    if n <= 1:
        return n
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    
    return b
"""
    
    # 関数分析の実行
    result = manager.analyze_code_snippet(sample_function, "function")
    
    if "error" not in result:
        analysis = result["analysis"]
        print(f"目的: {analysis['purpose']}")
        print(f"使用例: {analysis['usage_examples']}")
        print(f"エラーハンドリング: {analysis['error_handling']}")
    else:
        print(f"分析エラー: {result['error']}")


def example_class_analysis():
    """クラス分析の使用例"""
    print("\n=== クラス分析の例 ===")
    
    manager = LLMAnalysisManager()
    
    # サンプルクラスコード
    sample_class = """
class DataProcessor:
    '''
    データ処理を行うクラス
    
    ファイルからデータを読み込み、変換、保存を行う
    '''
    
    def __init__(self, input_format: str = "csv"):
        self.input_format = input_format
        self.processed_data = []
    
    def load_data(self, file_path: str) -> bool:
        '''データを読み込む'''
        try:
            # データ読み込み処理
            return True
        except Exception as e:
            print(f"データ読み込みエラー: {e}")
            return False
    
    def process_data(self, transformation_rules: dict) -> None:
        '''データを変換する'''
        # データ変換処理
        pass
    
    def save_data(self, output_path: str) -> bool:
        '''データを保存する'''
        try:
            # データ保存処理
            return True
        except Exception as e:
            print(f"データ保存エラー: {e}")
            return False
"""
    
    # クラス分析の実行
    result = manager.analyze_code_snippet(sample_class, "class")
    
    if "error" not in result:
        analysis = result["analysis"]
        print(f"目的: {analysis['purpose']}")
        print(f"設計パターン: {analysis['design_pattern']}")
        print(f"使用場面: {analysis['usage_scenarios']}")
    else:
        print(f"分析エラー: {result['error']}")


def example_file_analysis():
    """ファイル全体の分析例"""
    print("\n=== ファイル分析の例 ===")
    
    manager = LLMAnalysisManager()
    
    # 現在のファイルを分析（例として）
    current_file = __file__
    
    try:
        result = manager.analyze_python_file(current_file)
        
        if "error" not in result:
            print(f"分析対象ファイル: {result['file_path']}")
            print(f"関数数: {len(result['functions'])}")
            print(f"クラス数: {len(result['classes'])}")
            
            # 最初の関数の分析結果を表示
            if result['functions']:
                first_func = result['functions'][0]
                print(f"\n最初の関数: {first_func['name']}")
                print(f"  目的: {first_func['analysis']['purpose']}")
        else:
            print(f"ファイル分析エラー: {result['error']}")
            
    except Exception as e:
        print(f"例外が発生しました: {e}")


def example_error_analysis():
    """エラーパターン分析の例"""
    print("\n=== エラーパターン分析の例 ===")
    
    manager = LLMAnalysisManager()
    
    # エラーを含むサンプルコード
    problematic_code = """
def risky_function(data):
    # 危険なコード例
    result = data / 0  # ZeroDivisionError
    file_content = open("nonexistent.txt").read()  # FileNotFoundError
    return result[1000]  # IndexError
"""
    
    # エラーパターン分析
    result = manager.analyze_code_snippet(problematic_code, "snippet")
    
    if "error_analysis" in result:
        error_analysis = result["error_analysis"]
        print("発見された例外:")
        for exception in error_analysis.get("exceptions", []):
            print(f"  - {exception}")
        
        print("\n原因:")
        for cause in error_analysis.get("causes", []):
            print(f"  - {cause}")
        
        print("\n解決方法:")
        for solution in error_analysis.get("solutions", []):
            print(f"  - {solution}")


def example_cache_usage():
    """キャッシュ機能の使用例"""
    print("\n=== キャッシュ機能の例 ===")
    
    manager = LLMAnalysisManager()
    
    sample_code = "def simple_func(): pass"
    
    # 初回分析
    print("初回分析実行...")
    result1 = manager.analyze_code_snippet(sample_code)
    
    # 同じコードの再分析（キャッシュから取得）
    print("同じコードの再分析...")
    result2 = manager.analyze_code_snippet(sample_code)
    
    # キャッシュ統計
    cache_stats = manager.get_cache_stats()
    print(f"キャッシュサイズ: {cache_stats['cache_size']}")
    print(f"メモリ使用量概算: {cache_stats['memory_usage_estimate']:.2f} KB")
    
    # キャッシュクリア
    manager.clear_cache()
    print("キャッシュをクリアしました")


def main():
    """メイン実行関数"""
    print("高度なLLM分析機能のデモンストレーション")
    print("=" * 50)
    
    try:
        # 各種分析例の実行
        example_function_analysis()
        example_class_analysis()
        example_file_analysis()
        example_error_analysis()
        example_cache_usage()
        
        print("\n" + "=" * 50)
        print("デモンストレーション完了")
        
    except Exception as e:
        print(f"デモ実行中にエラーが発生しました: {e}")
        print("LangChainライブラリがインストールされていない可能性があります")
        print("pip install langchain-openai langchain-core でインストールしてください")


if __name__ == "__main__":
    main()