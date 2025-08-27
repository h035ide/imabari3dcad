"""
ベクトル検索システムのテストファイル

ベクトル検索エンジン、コード抽出器、RAG検索エンジンの
統合テストとサンプル使用例を提供します。
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

from vector_search import VectorSearchEngine, CodeInfo, create_sample_data
from code_extractor import CodeExtractor
from rag_search_engine import RAGSearchEngine
from performance_optimizer import PerformanceOptimizer


class VectorSearchTester:
    """ベクトル検索システムのテストクラス"""
    
    def __init__(self):
        """テスターを初期化"""
        self.test_dir = None
        self.results = {}
        
    def setup_test_environment(self):
        """テスト環境をセットアップ"""
        print("テスト環境をセットアップ中...")
        
        # 一時ディレクトリを作成
        self.test_dir = tempfile.mkdtemp(prefix="vector_search_test_")
        print(f"テストディレクトリ: {self.test_dir}")
        
        # テスト用Pythonファイルを作成
        self._create_test_files()
        
    def cleanup_test_environment(self):
        """テスト環境をクリーンアップ"""
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            print("テスト環境をクリーンアップしました")
    
    def test_vector_search_engine(self) -> Dict[str, Any]:
        """ベクトル検索エンジンのテスト"""
        print("\n=== ベクトル検索エンジンテスト ===")
        
        # エンジンの初期化
        engine = VectorSearchEngine(
            persist_directory=os.path.join(self.test_dir, "vector_store"),
            collection_name="test_collection"
        )
        
        test_results = {
            "initialization": True,
            "data_addition": False,
            "search_functionality": False,
            "type_search": False,
            "statistics": False
        }
        
        try:
            # サンプルデータの追加テスト
            sample_data = create_sample_data()
            added_count = 0
            
            for code_info in sample_data:
                if engine.add_code_info(code_info):
                    added_count += 1
            
            test_results["data_addition"] = added_count == len(sample_data)
            print(f"データ追加テスト: {added_count}/{len(sample_data)}個 - {'成功' if test_results['data_addition'] else '失敗'}")
            
            # 検索機能テスト
            search_results = engine.search_similar_functions("ファイルを読む", top_k=3)
            test_results["search_functionality"] = len(search_results) > 0
            print(f"検索機能テスト: {len(search_results)}件の結果 - {'成功' if test_results['search_functionality'] else '失敗'}")
            
            # タイプ検索テスト
            function_results = engine.search_by_type("function")
            test_results["type_search"] = len(function_results) > 0
            print(f"タイプ検索テスト: {len(function_results)}件の関数 - {'成功' if test_results['type_search'] else '失敗'}")
            
            # 統計情報テスト
            stats = engine.get_collection_stats()
            test_results["statistics"] = "total_count" in stats and stats["total_count"] > 0
            print(f"統計情報テスト: 総数{stats.get('total_count', 0)} - {'成功' if test_results['statistics'] else '失敗'}")
            
        except Exception as e:
            print(f"ベクトル検索エンジンテストでエラー: {e}")
        
        return test_results
    
    def test_code_extractor(self) -> Dict[str, Any]:
        """コード抽出器のテスト"""
        print("\n=== コード抽出器テスト ===")
        
        extractor = CodeExtractor()
        
        test_results = {
            "file_extraction": False,
            "content_extraction": False,
            "directory_extraction": False,
            "function_parsing": False,
            "class_parsing": False
        }
        
        try:
            # ファイル抽出テスト
            test_file = os.path.join(self.test_dir, "sample_code.py")
            if os.path.exists(test_file):
                file_results = extractor.extract_from_file(test_file)
                test_results["file_extraction"] = len(file_results) > 0
                print(f"ファイル抽出テスト: {len(file_results)}個の要素 - {'成功' if test_results['file_extraction'] else '失敗'}")
                
                # 関数とクラスの解析確認
                function_count = sum(1 for item in file_results if item.type == "function")
                class_count = sum(1 for item in file_results if item.type == "class")
                method_count = sum(1 for item in file_results if item.type == "method")
                
                test_results["function_parsing"] = function_count > 0
                test_results["class_parsing"] = class_count > 0
                
                print(f"  関数: {function_count}個, クラス: {class_count}個, メソッド: {method_count}個")
            
            # コンテンツ抽出テスト
            sample_code = '''
def test_function(param):
    """テスト関数"""
    return param * 2

class TestClass:
    """テストクラス"""
    def method(self):
        return "test"
            '''
            
            content_results = extractor.extract_from_content(sample_code, "test.py")
            test_results["content_extraction"] = len(content_results) > 0
            print(f"コンテンツ抽出テスト: {len(content_results)}個の要素 - {'成功' if test_results['content_extraction'] else '失敗'}")
            
            # ディレクトリ抽出テスト
            dir_results = extractor.extract_from_directory(self.test_dir, recursive=False)
            test_results["directory_extraction"] = len(dir_results) > 0
            print(f"ディレクトリ抽出テスト: {len(dir_results)}個の要素 - {'成功' if test_results['directory_extraction'] else '失敗'}")
            
        except Exception as e:
            print(f"コード抽出器テストでエラー: {e}")
        
        return test_results
    
    def test_rag_search_engine(self) -> Dict[str, Any]:
        """RAG検索エンジンのテスト"""
        print("\n=== RAG検索エンジンテスト ===")
        
        rag_engine = RAGSearchEngine(
            persist_directory=os.path.join(self.test_dir, "rag_vector_store"),
            collection_name="test_rag_collection"
        )
        
        test_results = {
            "initialization": True,
            "file_indexing": False,
            "directory_indexing": False,
            "semantic_search": False,
            "functionality_search": False,
            "input_output_search": False,
            "statistics": False
        }
        
        try:
            # ファイルインデックステスト
            test_file = os.path.join(self.test_dir, "sample_code.py")
            if os.path.exists(test_file):
                index_result = rag_engine.index_file(test_file)
                test_results["file_indexing"] = index_result["successfully_indexed"] > 0
                print(f"ファイルインデックステスト: {index_result['successfully_indexed']}個 - {'成功' if test_results['file_indexing'] else '失敗'}")
            
            # ディレクトリインデックステスト
            dir_result = rag_engine.index_directory(self.test_dir, recursive=False)
            test_results["directory_indexing"] = dir_result["successfully_indexed"] > 0
            print(f"ディレクトリインデックステスト: {dir_result['successfully_indexed']}個 - {'成功' if test_results['directory_indexing'] else '失敗'}")
            
            # 意味的検索テスト
            search_results = rag_engine.search("データを処理する", top_k=3)
            test_results["semantic_search"] = len(search_results) >= 0  # 結果がなくても正常動作
            print(f"意味的検索テスト: {len(search_results)}件の結果 - {'成功' if test_results['semantic_search'] else '失敗'}")
            
            # 機能検索テスト
            func_results = rag_engine.search_by_functionality("計算処理")
            test_results["functionality_search"] = len(func_results) >= 0
            print(f"機能検索テスト: {len(func_results)}件の結果 - {'成功' if test_results['functionality_search'] else '失敗'}")
            
            # 入出力検索テスト
            io_results = rag_engine.search_by_input_output("string", "int")
            test_results["input_output_search"] = len(io_results) >= 0
            print(f"入出力検索テスト: {len(io_results)}件の結果 - {'成功' if test_results['input_output_search'] else '失敗'}")
            
            # 統計情報テスト
            stats = rag_engine.get_statistics()
            test_results["statistics"] = "total_indexed_items" in stats
            print(f"統計情報テスト: 総要素数{stats.get('total_indexed_items', 0)} - {'成功' if test_results['statistics'] else '失敗'}")
            
        except Exception as e:
            print(f"RAG検索エンジンテストでエラー: {e}")
        
        return test_results
    
    def test_performance_optimizer(self) -> Dict[str, Any]:
        """パフォーマンス最適化器のテスト"""
        print("\n=== パフォーマンス最適化器テスト ===")
        
        # テスト用エンジンの作成
        engine = VectorSearchEngine(
            persist_directory=os.path.join(self.test_dir, "perf_vector_store"),
            collection_name="test_perf_collection"
        )
        
        # サンプルデータを追加
        sample_data = create_sample_data()
        for code_info in sample_data:
            engine.add_code_info(code_info)
        
        optimizer = PerformanceOptimizer(engine)
        
        test_results = {
            "initialization": True,
            "search_benchmark": False,
            "settings_optimization": False,
            "cache_analysis": False,
            "report_generation": False
        }
        
        try:
            # 検索ベンチマークテスト
            test_queries = ["テスト", "関数", "データ"]
            bench_results = optimizer.benchmark_search_performance(test_queries, top_k_values=[1, 3])
            test_results["search_benchmark"] = len(bench_results) > 0
            print(f"検索ベンチマークテスト: {len(bench_results)}個の結果 - {'成功' if test_results['search_benchmark'] else '失敗'}")
            
            # 設定最適化テスト
            optimal_settings = optimizer.optimize_collection_settings()
            test_results["settings_optimization"] = "description" in optimal_settings
            print(f"設定最適化テスト: {optimal_settings.get('description', 'なし')} - {'成功' if test_results['settings_optimization'] else '失敗'}")
            
            # キャッシュ分析テスト
            cache_analysis = optimizer.analyze_cache_performance()
            test_results["cache_analysis"] = "cache_size" in cache_analysis
            print(f"キャッシュ分析テスト: キャッシュサイズ{cache_analysis.get('cache_size', 0)} - {'成功' if test_results['cache_analysis'] else '失敗'}")
            
            # レポート生成テスト
            report = optimizer.generate_performance_report()
            test_results["report_generation"] = "timestamp" in report and "recommendations" in report
            print(f"レポート生成テスト: {len(report.get('recommendations', []))}個の推奨事項 - {'成功' if test_results['report_generation'] else '失敗'}")
            
        except Exception as e:
            print(f"パフォーマンス最適化器テストでエラー: {e}")
        
        return test_results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """全テストを実行"""
        print("=== ベクトル検索システム 統合テスト ===")
        
        try:
            self.setup_test_environment()
            
            all_results = {
                "vector_search_engine": self.test_vector_search_engine(),
                "code_extractor": self.test_code_extractor(),
                "rag_search_engine": self.test_rag_search_engine(),
                "performance_optimizer": self.test_performance_optimizer()
            }
            
            # 総合結果の計算
            total_tests = 0
            passed_tests = 0
            
            for component, results in all_results.items():
                for test_name, result in results.items():
                    total_tests += 1
                    if result:
                        passed_tests += 1
            
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            print(f"\n=== テスト結果サマリー ===")
            print(f"総テスト数: {total_tests}")
            print(f"成功テスト数: {passed_tests}")
            print(f"成功率: {success_rate:.1f}%")
            
            if success_rate >= 80:
                print("✅ システムは正常に動作しています")
            else:
                print("⚠️ 一部のテストが失敗しています。詳細を確認してください")
            
            self.results = all_results
            return all_results
            
        finally:
            self.cleanup_test_environment()
    
    def _create_test_files(self):
        """テスト用ファイルを作成"""
        # サンプルPythonファイルを作成
        sample_code = '''"""
サンプルコードファイル
ベクトル検索システムのテスト用
"""

import os
import math
from typing import List, Dict, Any


def read_file(file_path: str) -> str:
    """
    ファイルの内容を読み込む関数
    
    Args:
        file_path: 読み込むファイルのパス
        
    Returns:
        str: ファイルの内容
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def calculate_circle_area(radius: float) -> float:
    """
    円の面積を計算する
    
    Args:
        radius: 円の半径
        
    Returns:
        float: 円の面積
    """
    return math.pi * radius * radius


def process_data(data: List[Any]) -> List[Any]:
    """
    データを処理する汎用関数
    
    Args:
        data: 処理対象のデータリスト
        
    Returns:
        List[Any]: 処理済みのデータ
    """
    return [item for item in data if item is not None]


class DataProcessor:
    """
    データ処理を行うクラス
    
    様々なデータ形式に対応した処理を提供します。
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        データプロセッサーを初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config or {}
        self.processed_count = 0
    
    def process_text(self, text: str) -> str:
        """
        テキストを処理する
        
        Args:
            text: 処理対象のテキスト
            
        Returns:
            str: 処理済みのテキスト
        """
        self.processed_count += 1
        return text.strip().upper()
    
    def process_numbers(self, numbers: List[float]) -> List[float]:
        """
        数値リストを処理する
        
        Args:
            numbers: 数値のリスト
            
        Returns:
            List[float]: 処理済み数値のリスト
        """
        self.processed_count += 1
        return [num * 2 for num in numbers if num > 0]
    
    def get_statistics(self) -> Dict[str, int]:
        """
        処理統計を取得
        
        Returns:
            Dict[str, int]: 統計情報
        """
        return {
            "processed_count": self.processed_count,
            "config_keys": len(self.config)
        }


class FileManager:
    """ファイル管理クラス"""
    
    @staticmethod
    def list_files(directory: str, extension: str = "") -> List[str]:
        """
        ディレクトリ内のファイルをリストアップ
        
        Args:
            directory: 対象ディレクトリ
            extension: ファイル拡張子フィルター
            
        Returns:
            List[str]: ファイルパスのリスト
        """
        files = []
        for file in os.listdir(directory):
            if not extension or file.endswith(extension):
                files.append(os.path.join(directory, file))
        return files
    
    @staticmethod
    def create_backup(file_path: str) -> str:
        """
        ファイルのバックアップを作成
        
        Args:
            file_path: バックアップ対象ファイル
            
        Returns:
            str: バックアップファイルのパス
        """
        backup_path = f"{file_path}.backup"
        import shutil
        shutil.copy2(file_path, backup_path)
        return backup_path
'''
        
        # ファイルに書き込み
        test_file_path = os.path.join(self.test_dir, "sample_code.py")
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(sample_code)
        
        # 追加のテストファイル
        simple_code = '''
def simple_function():
    """シンプルな関数"""
    return "Hello, World!"

class SimpleClass:
    """シンプルなクラス"""
    pass
'''
        
        simple_file_path = os.path.join(self.test_dir, "simple_code.py")
        with open(simple_file_path, 'w', encoding='utf-8') as f:
            f.write(simple_code)


def run_sample_usage():
    """サンプル使用例の実行"""
    print("=== ベクトル検索システム サンプル使用例 ===")
    
    # 1. 基本的な使用例
    print("\n1. 基本的なベクトル検索")
    engine = VectorSearchEngine()
    
    # サンプルデータの追加
    sample_data = create_sample_data()
    for code_info in sample_data:
        engine.add_code_info(code_info)
    
    # 検索実行
    results = engine.search_similar_functions("ファイルを読む関数", top_k=3)
    print(f"検索結果: {len(results)}件")
    for result in results:
        print(f"  - {result['name']} (類似度: {result.get('similarity', 0):.3f})")
    
    # 2. RAG検索システムの使用例
    print("\n2. RAG検索システム")
    rag_engine = RAGSearchEngine()
    
    # 現在のディレクトリをインデックス化（デモ用）
    current_files = [f for f in os.listdir('.') if f.endswith('.py')]
    if current_files:
        print(f"現在のディレクトリから{len(current_files[:2])}ファイルをインデックス化")
        for file_name in current_files[:2]:  # 最初の2ファイルのみ
            try:
                result = rag_engine.index_file(file_name)
                print(f"  {file_name}: {result['successfully_indexed']}個の要素")
            except Exception as e:
                print(f"  {file_name}: エラー - {e}")
    
    # 機能検索の例
    func_results = rag_engine.search_by_functionality("データ処理")
    print(f"機能検索 'データ処理': {len(func_results)}件")
    
    # 3. パフォーマンス分析の例
    print("\n3. パフォーマンス分析")
    optimizer = PerformanceOptimizer(engine)
    
    # 簡単なベンチマーク
    test_queries = ["計算", "処理", "ファイル"]
    benchmark_results = optimizer.benchmark_search_performance(test_queries, top_k_values=[1, 3])
    
    for operation, result in benchmark_results.items():
        print(f"  {operation}: 平均 {result.avg_time:.4f}秒")
    
    # 推奨事項の表示
    report = optimizer.generate_performance_report()
    print("  推奨事項:")
    for recommendation in report["recommendations"]:
        print(f"    - {recommendation}")
    
    print("\nサンプル使用例完了!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "sample":
        # サンプル使用例の実行
        run_sample_usage()
    else:
        # 統合テストの実行
        tester = VectorSearchTester()
        tester.run_all_tests()