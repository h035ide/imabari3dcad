"""
ChromaDBパフォーマンスベンチマークモジュール

このモジュールはChromaDBの挿入、検索、フィルタリング
パフォーマンスを測定し、最適化に必要な情報を提供します。
"""

import time
import statistics
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("警告: numpyが見つかりません。ランダムなテストデータ生成に制限があります。")


@dataclass
class BenchmarkResult:
    """ベンチマーク結果を格納するデータクラス"""
    operation_type: str
    total_time: float
    avg_time_per_item: float
    items_per_second: float
    min_time: float
    max_time: float
    std_dev: float
    memory_usage_mb: Optional[float] = None
    success_rate: float = 1.0
    additional_metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_metrics is None:
            self.additional_metrics = {}


class ChromaDBPerformanceBenchmark:
    """ChromaDBのパフォーマンスベンチマークを実行するクラス"""
    
    def __init__(self, collection):
        """
        ベンチマークの初期化
        
        Args:
            collection: ChromaDBのコレクションオブジェクト
        """
        self.collection = collection
        self.benchmark_results = {}
        self.test_data_cache = {}
        
    def generate_test_embeddings(self, count: int, dimension: int = 384) -> List[List[float]]:
        """テスト用の埋め込みベクトルを生成"""
        cache_key = f"embeddings_{count}_{dimension}"
        
        if cache_key not in self.test_data_cache:
            print(f"テスト用埋め込みベクトル生成中... ({count}個, {dimension}次元)")
            
            if HAS_NUMPY:
                # 正規分布から埋め込みベクトルを生成
                embeddings = np.random.normal(0, 1, (count, dimension)).tolist()
            else:
                # numpy無しでの簡易的な生成
                import random
                embeddings = []
                for _ in range(count):
                    vector = [random.gauss(0, 1) for _ in range(dimension)]
                    embeddings.append(vector)
            
            self.test_data_cache[cache_key] = embeddings
        
        return self.test_data_cache[cache_key]
    
    def generate_test_metadata(self, count: int) -> List[Dict[str, Any]]:
        """テスト用のメタデータを生成"""
        cache_key = f"metadata_{count}"
        
        if cache_key not in self.test_data_cache:
            metadata_list = []
            for i in range(count):
                metadata_list.append({
                    "function_name": f"test_function_{i}",
                    "file_path": f"test_file_{i % 10}.py",
                    "complexity": ["O(1)", "O(n)", "O(n^2)", "O(log n)"][i % 4],
                    "line_count": 10 + (i % 50),
                    "category": ["util", "core", "api", "test"][i % 4],
                    "score": 0.1 + (i % 10) * 0.1
                })
            self.test_data_cache[cache_key] = metadata_list
        
        return self.test_data_cache[cache_key]

    def benchmark_bulk_insert(self, 
                            sizes: List[int] = None, 
                            batch_sizes: List[int] = None,
                            dimension: int = 384) -> Dict[str, BenchmarkResult]:
        """
        バッチ挿入のパフォーマンスを測定
        
        Args:
            sizes: テストするデータサイズのリスト
            batch_sizes: テストするバッチサイズのリスト
            dimension: 埋め込みベクトルの次元数
        
        Returns:
            ベンチマーク結果の辞書
        """
        if sizes is None:
            sizes = [100, 500, 1000]
        if batch_sizes is None:
            batch_sizes = [1, 10, 50, 100]
        
        results = {}
        
        for size in sizes:
            embeddings = self.generate_test_embeddings(size, dimension)
            metadata_list = self.generate_test_metadata(size)
            
            for batch_size in batch_sizes:
                operation_name = f"bulk_insert_{size}_batch_{batch_size}"
                print(f"バッチ挿入ベンチマーク実行中: {operation_name}")
                
                # 測定開始
                start_time = time.time()
                insert_times = []
                successful_inserts = 0
                
                try:
                    for i in range(0, size, batch_size):
                        batch_start = time.time()
                        
                        end_idx = min(i + batch_size, size)
                        batch_embeddings = embeddings[i:end_idx]
                        batch_metadata = metadata_list[i:end_idx]
                        batch_ids = [f"bench_insert_{size}_{i}_{j}" for j in range(len(batch_embeddings))]
                        
                        # ChromaDBに挿入
                        self.collection.add(
                            embeddings=batch_embeddings,
                            metadatas=batch_metadata,
                            ids=batch_ids
                        )
                        
                        batch_time = time.time() - batch_start
                        insert_times.append(batch_time)
                        successful_inserts += len(batch_embeddings)
                    
                    total_time = time.time() - start_time
                    
                    # 結果の計算
                    avg_time = total_time / size
                    items_per_second = size / total_time if total_time > 0 else 0
                    min_time = min(insert_times) if insert_times else 0
                    max_time = max(insert_times) if insert_times else 0
                    std_dev = statistics.stdev(insert_times) if len(insert_times) > 1 else 0
                    success_rate = successful_inserts / size
                    
                    results[operation_name] = BenchmarkResult(
                        operation_type="bulk_insert",
                        total_time=total_time,
                        avg_time_per_item=avg_time,
                        items_per_second=items_per_second,
                        min_time=min_time,
                        max_time=max_time,
                        std_dev=std_dev,
                        success_rate=success_rate,
                        additional_metrics={
                            "data_size": size,
                            "batch_size": batch_size,
                            "dimension": dimension,
                            "successful_inserts": successful_inserts
                        }
                    )
                    
                except Exception as e:
                    print(f"エラーが発生しました: {operation_name} - {str(e)}")
                    results[operation_name] = BenchmarkResult(
                        operation_type="bulk_insert",
                        total_time=0,
                        avg_time_per_item=0,
                        items_per_second=0,
                        min_time=0,
                        max_time=0,
                        std_dev=0,
                        success_rate=0,
                        additional_metrics={"error": str(e)}
                    )
        
        self.benchmark_results.update(results)
        return results

    def benchmark_search_performance(self, 
                                   query_counts: List[int] = None,
                                   top_k_values: List[int] = None,
                                   dimension: int = 384) -> Dict[str, BenchmarkResult]:
        """
        検索パフォーマンスを測定
        
        Args:
            query_counts: テストするクエリ数のリスト
            top_k_values: テストするtop_k値のリスト
            dimension: 埋め込みベクトルの次元数
        
        Returns:
            ベンチマーク結果の辞書
        """
        if query_counts is None:
            query_counts = [10, 50, 100]
        if top_k_values is None:
            top_k_values = [1, 5, 10, 20]
        
        results = {}
        
        for query_count in query_counts:
            query_embeddings = self.generate_test_embeddings(query_count, dimension)
            
            for top_k in top_k_values:
                operation_name = f"search_{query_count}_queries_top_{top_k}"
                print(f"検索ベンチマーク実行中: {operation_name}")
                
                search_times = []
                successful_searches = 0
                total_results = 0
                
                try:
                    start_time = time.time()
                    
                    for query_emb in query_embeddings:
                        search_start = time.time()
                        
                        results_data = self.collection.query(
                            query_embeddings=[query_emb],
                            n_results=top_k
                        )
                        
                        search_time = time.time() - search_start
                        search_times.append(search_time)
                        successful_searches += 1
                        
                        # 結果数をカウント
                        if results_data['ids'] and results_data['ids'][0]:
                            total_results += len(results_data['ids'][0])
                    
                    total_time = time.time() - start_time
                    
                    # 統計の計算
                    avg_time = sum(search_times) / len(search_times) if search_times else 0
                    queries_per_second = query_count / total_time if total_time > 0 else 0
                    min_time = min(search_times) if search_times else 0
                    max_time = max(search_times) if search_times else 0
                    std_dev = statistics.stdev(search_times) if len(search_times) > 1 else 0
                    success_rate = successful_searches / query_count
                    
                    results[operation_name] = BenchmarkResult(
                        operation_type="search",
                        total_time=total_time,
                        avg_time_per_item=avg_time,
                        items_per_second=queries_per_second,
                        min_time=min_time,
                        max_time=max_time,
                        std_dev=std_dev,
                        success_rate=success_rate,
                        additional_metrics={
                            "query_count": query_count,
                            "top_k": top_k,
                            "total_results": total_results,
                            "avg_results_per_query": total_results / query_count if query_count > 0 else 0
                        }
                    )
                    
                except Exception as e:
                    print(f"エラーが発生しました: {operation_name} - {str(e)}")
                    results[operation_name] = BenchmarkResult(
                        operation_type="search",
                        total_time=0,
                        avg_time_per_item=0,
                        items_per_second=0,
                        min_time=0,
                        max_time=0,
                        std_dev=0,
                        success_rate=0,
                        additional_metrics={"error": str(e)}
                    )
        
        self.benchmark_results.update(results)
        return results

    def benchmark_filtering_performance(self, 
                                      filter_combinations: List[Dict[str, Any]] = None,
                                      query_count: int = 50,
                                      dimension: int = 384) -> Dict[str, BenchmarkResult]:
        """
        フィルタリングパフォーマンスを測定
        
        Args:
            filter_combinations: テストするフィルタの組み合わせ
            query_count: クエリ数
            dimension: 埋め込みベクトルの次元数
        
        Returns:
            ベンチマーク結果の辞書
        """
        if filter_combinations is None:
            filter_combinations = [
                {"category": "util"},
                {"complexity": "O(n)"},
                {"category": "core", "complexity": "O(1)"},
                {"line_count": {"$gte": 20}},
                {"score": {"$gte": 0.5}},
                {"category": {"$in": ["util", "core"]}, "score": {"$gte": 0.3}}
            ]
        
        results = {}
        query_embeddings = self.generate_test_embeddings(query_count, dimension)
        
        for i, filters in enumerate(filter_combinations):
            operation_name = f"filter_combo_{i}"
            print(f"フィルタリングベンチマーク実行中: {operation_name}")
            
            filter_times = []
            successful_queries = 0
            total_filtered_results = 0
            
            try:
                start_time = time.time()
                
                for query_emb in query_embeddings:
                    filter_start = time.time()
                    
                    # フィルタ付きで検索
                    results_data = self.collection.query(
                        query_embeddings=[query_emb],
                        n_results=10,
                        where=filters
                    )
                    
                    filter_time = time.time() - filter_start
                    filter_times.append(filter_time)
                    successful_queries += 1
                    
                    # フィルタ後の結果数をカウント
                    if results_data['ids'] and results_data['ids'][0]:
                        total_filtered_results += len(results_data['ids'][0])
                
                total_time = time.time() - start_time
                
                # 統計の計算
                avg_time = sum(filter_times) / len(filter_times) if filter_times else 0
                queries_per_second = query_count / total_time if total_time > 0 else 0
                min_time = min(filter_times) if filter_times else 0
                max_time = max(filter_times) if filter_times else 0
                std_dev = statistics.stdev(filter_times) if len(filter_times) > 1 else 0
                success_rate = successful_queries / query_count
                
                results[operation_name] = BenchmarkResult(
                    operation_type="filtering",
                    total_time=total_time,
                    avg_time_per_item=avg_time,
                    items_per_second=queries_per_second,
                    min_time=min_time,
                    max_time=max_time,
                    std_dev=std_dev,
                    success_rate=success_rate,
                    additional_metrics={
                        "filters": filters,
                        "filter_complexity": len(filters),
                        "total_filtered_results": total_filtered_results,
                        "avg_filtered_results": total_filtered_results / query_count if query_count > 0 else 0
                    }
                )
                
            except Exception as e:
                print(f"エラーが発生しました: {operation_name} - {str(e)}")
                results[operation_name] = BenchmarkResult(
                    operation_type="filtering",
                    total_time=0,
                    avg_time_per_item=0,
                    items_per_second=0,
                    min_time=0,
                    max_time=0,
                    std_dev=0,
                    success_rate=0,
                    additional_metrics={"error": str(e), "filters": filters}
                )
        
        self.benchmark_results.update(results)
        return results

    def run_comprehensive_benchmark(self, 
                                  collection_sizes: List[int] = None,
                                  dimension: int = 384) -> Dict[str, Any]:
        """
        包括的なベンチマークを実行
        
        Args:
            collection_sizes: テストするコレクションサイズ
            dimension: 埋め込みベクトルの次元数
        
        Returns:
            全ベンチマーク結果
        """
        if collection_sizes is None:
            collection_sizes = [100, 500, 1000]
        
        print("=== ChromaDB 包括的パフォーマンスベンチマーク開始 ===")
        
        comprehensive_results = {
            "benchmark_info": {
                "timestamp": time.time(),
                "collection_name": getattr(self.collection, 'name', 'unknown'),
                "dimension": dimension,
                "test_sizes": collection_sizes
            },
            "results": {}
        }
        
        # 1. バッチ挿入ベンチマーク
        print("\n1. バッチ挿入パフォーマンステスト")
        insert_results = self.benchmark_bulk_insert(
            sizes=collection_sizes,
            dimension=dimension
        )
        comprehensive_results["results"]["bulk_insert"] = insert_results
        
        # 2. 検索パフォーマンステスト
        print("\n2. 検索パフォーマンステスト")
        search_results = self.benchmark_search_performance(
            dimension=dimension
        )
        comprehensive_results["results"]["search"] = search_results
        
        # 3. フィルタリングパフォーマンステスト
        print("\n3. フィルタリングパフォーマンステスト")
        filter_results = self.benchmark_filtering_performance(
            dimension=dimension
        )
        comprehensive_results["results"]["filtering"] = filter_results
        
        # 4. 全体統計の計算
        comprehensive_results["summary"] = self._calculate_summary_stats()
        
        print("\n=== ベンチマーク完了 ===")
        return comprehensive_results

    def _calculate_summary_stats(self) -> Dict[str, Any]:
        """全体統計を計算"""
        if not self.benchmark_results:
            return {}
        
        # 操作タイプ別の統計
        operation_stats = {}
        
        for operation_name, result in self.benchmark_results.items():
            op_type = result.operation_type
            
            if op_type not in operation_stats:
                operation_stats[op_type] = {
                    "count": 0,
                    "avg_time": [],
                    "items_per_second": [],
                    "success_rates": []
                }
            
            operation_stats[op_type]["count"] += 1
            operation_stats[op_type]["avg_time"].append(result.avg_time_per_item)
            operation_stats[op_type]["items_per_second"].append(result.items_per_second)
            operation_stats[op_type]["success_rates"].append(result.success_rate)
        
        # 統計の計算
        summary = {}
        for op_type, stats in operation_stats.items():
            summary[op_type] = {
                "test_count": stats["count"],
                "avg_time_mean": statistics.mean(stats["avg_time"]),
                "avg_time_median": statistics.median(stats["avg_time"]),
                "throughput_mean": statistics.mean(stats["items_per_second"]),
                "throughput_max": max(stats["items_per_second"]),
                "success_rate_mean": statistics.mean(stats["success_rates"]),
                "success_rate_min": min(stats["success_rates"])
            }
        
        return summary

    def export_results(self, output_path: str = None) -> str:
        """ベンチマーク結果をファイルにエクスポート"""
        if output_path is None:
            timestamp = int(time.time())
            output_path = f"chromadb_benchmark_results_{timestamp}.json"
        
        # 結果をシリアライズ可能な形式に変換
        export_data = {
            "timestamp": time.time(),
            "collection_info": {
                "name": getattr(self.collection, 'name', 'unknown'),
                "count": self.collection.count() if hasattr(self.collection, 'count') else 0
            },
            "results": {}
        }
        
        for name, result in self.benchmark_results.items():
            export_data["results"][name] = asdict(result)
        
        # ファイルに保存
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"ベンチマーク結果を {output_path} に保存しました")
        return output_path

    def print_summary_report(self):
        """ベンチマーク結果のサマリーレポートを表示"""
        if not self.benchmark_results:
            print("ベンチマーク結果がありません")
            return
        
        print("\n" + "="*60)
        print("ChromaDB パフォーマンスベンチマーク サマリーレポート")
        print("="*60)
        
        # 操作タイプ別のベスト結果
        best_results = {}
        for name, result in self.benchmark_results.items():
            op_type = result.operation_type
            
            if op_type not in best_results or result.items_per_second > best_results[op_type].items_per_second:
                best_results[op_type] = result
        
        for op_type, result in best_results.items():
            print(f"\n【{op_type.upper()}】最高パフォーマンス:")
            print(f"  スループット: {result.items_per_second:.2f} 項目/秒")
            print(f"  平均レスポンス時間: {result.avg_time_per_item*1000:.2f} ms")
            print(f"  成功率: {result.success_rate*100:.1f}%")
            
            if result.additional_metrics:
                print("  詳細:")
                for key, value in result.additional_metrics.items():
                    if key != "error":
                        print(f"    {key}: {value}")
        
        # 推奨設定の表示
        print(f"\n【推奨設定】")
        insert_results = [r for r in self.benchmark_results.values() if r.operation_type == "bulk_insert"]
        if insert_results:
            best_insert = max(insert_results, key=lambda x: x.items_per_second)
            batch_size = best_insert.additional_metrics.get("batch_size", "不明")
            print(f"  推奨バッチサイズ: {batch_size}")
        
        search_results = [r for r in self.benchmark_results.values() if r.operation_type == "search"]
        if search_results:
            best_search = max(search_results, key=lambda x: x.items_per_second)
            top_k = best_search.additional_metrics.get("top_k", "不明")
            print(f"  推奨検索数(top_k): {top_k}")


# 使用例のデモ関数
def demo_benchmark():
    """ベンチマークのデモ（実際のChromaDBコレクション無しで実行）"""
    print("ChromaDBベンチマークのデモ")
    print("注意: 実際のベンチマークには ChromaDB コレクションが必要です")
    
    # モックコレクション（デモ用）
    class MockCollection:
        def __init__(self):
            self.name = "demo_collection"
            self._count = 0
        
        def add(self, embeddings, metadatas, ids):
            self._count += len(embeddings)
            time.sleep(0.001)  # 挿入時間をシミュレート
        
        def query(self, query_embeddings, n_results, where=None):
            time.sleep(0.01)  # 検索時間をシミュレート
            return {
                'ids': [['result1', 'result2']],
                'distances': [[0.1, 0.2]],
                'metadatas': [[{'test': 'data'}, {'test': 'data2'}]]
            }
        
        def count(self):
            return self._count
    
    # デモ実行
    mock_collection = MockCollection()
    benchmark = ChromaDBPerformanceBenchmark(mock_collection)
    
    print("小規模ベンチマーク実行中...")
    results = benchmark.run_comprehensive_benchmark(
        collection_sizes=[10, 50],  # 小さいサイズでデモ
        dimension=128
    )
    
    benchmark.print_summary_report()


if __name__ == "__main__":
    demo_benchmark()