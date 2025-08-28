"""
パフォーマンス最適化器 - ChromaDBベクトル検索の最適化

RAG検索システムのパフォーマンスを測定・最適化し、
効率的なコード検索を実現します。
"""

import time
import statistics
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from vector_search import VectorSearchEngine


@dataclass
class BenchmarkResult:
    """ベンチマーク結果を格納するデータクラス"""
    operation_type: str
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    std_dev: float
    items_processed: int
    items_per_second: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PerformanceOptimizer:
    """
    パフォーマンス最適化器
    
    ChromaDBベクトル検索のパフォーマンス測定と最適化を行います。
    """
    
    def __init__(self, vector_engine: VectorSearchEngine):
        """
        最適化器を初期化
        
        Args:
            vector_engine: 最適化対象のベクトル検索エンジン
        """
        self.vector_engine = vector_engine
        self.benchmark_results = {}
        self.optimization_history = []
        
        print("パフォーマンス最適化器が初期化されました")
    
    def benchmark_search_performance(self, 
                                   test_queries: List[str],
                                   top_k_values: List[int] = None) -> Dict[str, BenchmarkResult]:
        """
        検索パフォーマンスをベンチマーク
        
        Args:
            test_queries: テスト用クエリのリスト
            top_k_values: テストするtop_k値のリスト
            
        Returns:
            Dict[str, BenchmarkResult]: ベンチマーク結果
        """
        if top_k_values is None:
            top_k_values = [1, 5, 10, 20]
        
        print(f"検索パフォーマンスベンチマークを実行中...")
        print(f"テストクエリ数: {len(test_queries)}, top_k値: {top_k_values}")
        
        results = {}
        
        for top_k in top_k_values:
            print(f"  top_k={top_k} をテスト中...")
            search_times = []
            
            for query in test_queries:
                start_time = time.time()
                self.vector_engine.search_similar_functions(query, top_k=top_k)
                search_time = time.time() - start_time
                search_times.append(search_time)
            
            # 統計計算
            total_time = sum(search_times)
            avg_time = total_time / len(search_times)
            min_time = min(search_times)
            max_time = max(search_times)
            std_dev = statistics.stdev(search_times) if len(search_times) > 1 else 0
            items_per_second = len(test_queries) / total_time if total_time > 0 else 0
            
            benchmark_result = BenchmarkResult(
                operation_type=f"search_top_{top_k}",
                total_time=total_time,
                avg_time=avg_time,
                min_time=min_time,
                max_time=max_time,
                std_dev=std_dev,
                items_processed=len(test_queries),
                items_per_second=items_per_second
            )
            
            results[f"search_top_{top_k}"] = benchmark_result
            print(f"    平均時間: {avg_time:.4f}秒, QPS: {items_per_second:.2f}")
        
        self.benchmark_results.update(results)
        return results
    
    def benchmark_indexing_performance(self, 
                                     test_data: List[Any],
                                     batch_sizes: List[int] = None) -> Dict[str, BenchmarkResult]:
        """
        インデックス化パフォーマンスをベンチマーク
        
        Args:
            test_data: テスト用データのリスト
            batch_sizes: テストするバッチサイズのリスト
            
        Returns:
            Dict[str, BenchmarkResult]: ベンチマーク結果
        """
        if batch_sizes is None:
            batch_sizes = [1, 10, 50, 100]
        
        print(f"インデックス化パフォーマンスベンチマークを実行中...")
        print(f"テストデータ数: {len(test_data)}, バッチサイズ: {batch_sizes}")
        
        results = {}
        
        for batch_size in batch_sizes:
            print(f"  バッチサイズ={batch_size} をテスト中...")
            
            # テスト用の一時コレクションを作成
            test_collection_name = f"test_batch_{batch_size}_{int(time.time())}"
            
            add_times = []
            total_items = min(len(test_data), 100)  # 最大100アイテムでテスト
            
            for i in range(0, total_items, batch_size):
                batch = test_data[i:i+batch_size]
                
                start_time = time.time()
                for item in batch:
                    self.vector_engine.add_code_info(item)
                add_time = time.time() - start_time
                add_times.append(add_time)
            
            # 統計計算
            total_time = sum(add_times)
            avg_time = total_time / len(add_times) if add_times else 0
            min_time = min(add_times) if add_times else 0
            max_time = max(add_times) if add_times else 0
            std_dev = statistics.stdev(add_times) if len(add_times) > 1 else 0
            items_per_second = total_items / total_time if total_time > 0 else 0
            
            benchmark_result = BenchmarkResult(
                operation_type=f"index_batch_{batch_size}",
                total_time=total_time,
                avg_time=avg_time,
                min_time=min_time,
                max_time=max_time,
                std_dev=std_dev,
                items_processed=total_items,
                items_per_second=items_per_second
            )
            
            results[f"index_batch_{batch_size}"] = benchmark_result
            print(f"    平均時間: {avg_time:.4f}秒, IPS: {items_per_second:.2f}")
        
        self.benchmark_results.update(results)
        return results
    
    def optimize_collection_settings(self) -> Dict[str, Any]:
        """
        コレクション設定を最適化
        
        Returns:
            Dict[str, Any]: 最適化後の設定
        """
        print("コレクション設定を最適化中...")
        
        # 現在のコレクションサイズを取得
        current_stats = self.vector_engine.get_collection_stats()
        collection_size = current_stats.get("total_count", 0)
        
        print(f"現在のコレクションサイズ: {collection_size}")
        
        # サイズに基づいて最適化設定を決定
        if collection_size < 1000:
            # 小規模コレクション
            optimal_settings = {
                "hnsw:construction_ef": 64,
                "hnsw:search_ef": 32,
                "hnsw:m": 16,
                "description": "小規模コレクション最適化設定"
            }
        elif collection_size < 10000:
            # 中規模コレクション
            optimal_settings = {
                "hnsw:construction_ef": 128,
                "hnsw:search_ef": 64,
                "hnsw:m": 32,
                "description": "中規模コレクション最適化設定"
            }
        else:
            # 大規模コレクション
            optimal_settings = {
                "hnsw:construction_ef": 256,
                "hnsw:search_ef": 128,
                "hnsw:m": 64,
                "description": "大規模コレクション最適化設定"
            }
        
        # 最適化履歴に記録
        optimization_record = {
            "timestamp": time.time(),
            "collection_size": collection_size,
            "settings": optimal_settings
        }
        self.optimization_history.append(optimization_record)
        
        print(f"最適化設定: {optimal_settings['description']}")
        return optimal_settings
    
    def analyze_cache_performance(self) -> Dict[str, Any]:
        """
        キャッシュパフォーマンスを分析
        
        Returns:
            Dict[str, Any]: キャッシュパフォーマンス分析結果
        """
        print("キャッシュパフォーマンスを分析中...")
        
        # ベクトルエンジンからパフォーマンス統計を取得
        engine_stats = self.vector_engine.get_collection_stats()
        
        cache_analysis = {
            "cache_size": engine_stats.get("cache_size", 0),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "recommendations": []
        }
        
        # キャッシュサイズに基づく推奨事項
        cache_size = cache_analysis["cache_size"]
        if cache_size > 1000:
            cache_analysis["recommendations"].append("キャッシュサイズが大きいです。定期的なクリアを検討してください。")
        elif cache_size < 10:
            cache_analysis["recommendations"].append("キャッシュ利用率が低いです。クエリの重複性を確認してください。")
        
        return cache_analysis
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """
        総合的なパフォーマンスレポートを生成
        
        Returns:
            Dict[str, Any]: パフォーマンスレポート
        """
        print("パフォーマンスレポートを生成中...")
        
        report = {
            "timestamp": time.time(),
            "collection_stats": self.vector_engine.get_collection_stats(),
            "benchmark_results": {k: v.to_dict() for k, v in self.benchmark_results.items()},
            "cache_analysis": self.analyze_cache_performance(),
            "optimization_history": self.optimization_history,
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], file_path: str = "performance_report.json"):
        """
        パフォーマンスレポートをファイルに保存
        
        Args:
            report: 保存するレポート
            file_path: 保存先ファイルパス
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"パフォーマンスレポートを保存しました: {file_path}")
        except Exception as e:
            print(f"レポート保存エラー: {e}")
    
    def _calculate_cache_hit_rate(self) -> float:
        """キャッシュヒット率を計算"""
        # 簡易的な計算（実際の実装では詳細な統計が必要）
        cache_size = len(self.vector_engine.query_cache)
        total_operations = len(self.vector_engine.performance_metrics)
        
        if total_operations == 0:
            return 0.0
        
        # キャッシュサイズから推定（実際には詳細な追跡が必要）
        estimated_hit_rate = min(cache_size / total_operations, 1.0)
        return estimated_hit_rate
    
    def _generate_recommendations(self) -> List[str]:
        """パフォーマンス改善の推奨事項を生成"""
        recommendations = []
        
        # コレクションサイズチェック
        stats = self.vector_engine.get_collection_stats()
        collection_size = stats.get("total_count", 0)
        
        if collection_size > 10000:
            recommendations.append("大規模コレクションです。検索性能最適化を検討してください。")
        
        # ベンチマーク結果チェック
        if self.benchmark_results:
            search_results = [v for k, v in self.benchmark_results.items() if k.startswith("search_")]
            if search_results:
                avg_search_time = sum(r.avg_time for r in search_results) / len(search_results)
                if avg_search_time > 1.0:
                    recommendations.append("検索時間が長いです。インデックス最適化を検討してください。")
        
        # キャッシュ利用率チェック
        cache_hit_rate = self._calculate_cache_hit_rate()
        if cache_hit_rate < 0.3:
            recommendations.append("キャッシュ利用率が低いです。クエリパターンを見直してください。")
        
        if not recommendations:
            recommendations.append("パフォーマンスは良好です。")
        
        return recommendations


def demo_performance_optimization():
    """パフォーマンス最適化のデモ"""
    print("=== パフォーマンス最適化デモ ===")
    
    # 仮のベクトル検索エンジンを作成（デモ用）
    from vector_search import VectorSearchEngine, create_sample_data
    
    # エンジンの初期化とサンプルデータの追加
    engine = VectorSearchEngine(persist_directory="./demo_vector_store")
    sample_data = create_sample_data()
    
    for code_info in sample_data:
        engine.add_code_info(code_info)
    
    # 最適化器の初期化
    optimizer = PerformanceOptimizer(engine)
    
    # 検索パフォーマンステスト
    test_queries = [
        "ファイルを読む",
        "計算する",
        "データ処理",
        "文字列操作",
        "配列操作"
    ]
    
    print("\n1. 検索パフォーマンステスト")
    search_results = optimizer.benchmark_search_performance(test_queries)
    
    for operation, result in search_results.items():
        print(f"  {operation}: 平均 {result.avg_time:.4f}秒, QPS {result.items_per_second:.2f}")
    
    # 設定最適化
    print("\n2. 設定最適化")
    optimal_settings = optimizer.optimize_collection_settings()
    print(f"  推奨設定: {optimal_settings['description']}")
    
    # キャッシュ分析
    print("\n3. キャッシュ分析")
    cache_analysis = optimizer.analyze_cache_performance()
    print(f"  キャッシュサイズ: {cache_analysis['cache_size']}")
    print(f"  キャッシュヒット率: {cache_analysis['cache_hit_rate']:.2f}")
    
    # 総合レポート
    print("\n4. パフォーマンスレポート生成")
    report = optimizer.generate_performance_report()
    
    print("  推奨事項:")
    for recommendation in report["recommendations"]:
        print(f"    - {recommendation}")
    
    # レポート保存
    optimizer.save_report(report, "demo_performance_report.json")
    
    print("\nパフォーマンス最適化デモ完了!")


if __name__ == "__main__":
    demo_performance_optimization()