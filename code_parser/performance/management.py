"""
パフォーマンス管理統合モジュール

このモジュールは、パフォーマンス分析、ChromaDBベンチマーク、
最適化、監視機能を統合的に提供します。
"""

import time
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    from .performance_analyzer import PerformanceAnalyzer, PerformanceMetrics
    from .chromadb_benchmark import ChromaDBPerformanceBenchmark, BenchmarkResult
    from .chromadb_optimizer import ChromaDBOptimizer, OptimizationRecommendation
    from .performance_monitor import ChromaDBPerformanceMonitor, Alert
except ImportError:
    # 直接実行時の対応
    from performance_analyzer import PerformanceAnalyzer, PerformanceMetrics
    from chromadb_benchmark import ChromaDBPerformanceBenchmark, BenchmarkResult
    from chromadb_optimizer import ChromaDBOptimizer, OptimizationRecommendation
    from performance_monitor import ChromaDBPerformanceMonitor, Alert


class PerformanceManager:
    """パフォーマンス管理の統合クラス"""
    
    def __init__(self, collection=None, config: Dict[str, Any] = None):
        """
        パフォーマンス管理の初期化
        
        Args:
            collection: ChromaDBのコレクションオブジェクト
            config: 設定辞書
        """
        self.collection = collection
        self.config = config or self._get_default_config()
        
        # 各コンポーネントの初期化
        self.code_analyzer = PerformanceAnalyzer()
        self.benchmark = ChromaDBPerformanceBenchmark(collection) if collection else None
        self.optimizer = ChromaDBOptimizer(collection) if collection else None
        self.monitor = ChromaDBPerformanceMonitor(
            collection, 
            alert_callback=self._handle_alert
        ) if collection else None
        
        # 結果保存用
        self.analysis_results = {}
        self.performance_reports = []

    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定を取得"""
        return {
            "benchmark": {
                "collection_sizes": [100, 500, 1000],
                "batch_sizes": [10, 50, 100],
                "top_k_values": [1, 5, 10, 20],
                "dimension": 384
            },
            "monitoring": {
                "history_size": 1000,
                "alert_enabled": True,
                "continuous_monitoring": False,
                "monitoring_interval": 60
            },
            "analysis": {
                "include_file_analysis": True,
                "generate_reports": True,
                "export_results": True
            }
        }

    def analyze_code_performance(self, 
                               code_or_file: str, 
                               is_file: bool = False) -> Dict[str, PerformanceMetrics]:
        """
        コードのパフォーマンス分析
        
        Args:
            code_or_file: コード文字列またはファイルパス
            is_file: ファイルパスかどうか
        
        Returns:
            分析結果の辞書
        """
        print("コードパフォーマンス分析を開始...")
        
        if is_file:
            results = self.code_analyzer.analyze_file(code_or_file)
            analysis_type = f"file:{Path(code_or_file).name}"
        else:
            metrics = self.code_analyzer.analyze_code(code_or_file, "provided_code")
            results = {"provided_code": metrics}
            analysis_type = "code_snippet"
        
        # 結果を保存
        self.analysis_results[analysis_type] = {
            "timestamp": time.time(),
            "results": results,
            "summary": self._summarize_code_analysis(results)
        }
        
        print(f"分析完了: {len(results)}個の要素を分析")
        return results

    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """包括的なベンチマークを実行"""
        if not self.benchmark:
            return {"error": "ベンチマーク機能が利用できません（コレクションが未設定）"}
        
        print("包括的ベンチマークを開始...")
        
        config = self.config["benchmark"]
        results = self.benchmark.run_comprehensive_benchmark(
            collection_sizes=config["collection_sizes"],
            dimension=config["dimension"]
        )
        
        # 結果を保存
        benchmark_summary = {
            "timestamp": time.time(),
            "results": results,
            "recommendations": self._generate_benchmark_recommendations(results)
        }
        
        self.performance_reports.append({
            "type": "benchmark",
            "data": benchmark_summary
        })
        
        print("ベンチマーク完了")
        return benchmark_summary

    def optimize_performance(self) -> Dict[str, Any]:
        """パフォーマンス最適化を実行"""
        if not self.optimizer:
            return {"error": "最適化機能が利用できません（コレクションが未設定）"}
        
        print("パフォーマンス最適化分析を開始...")
        
        # 最適化推奨事項の取得
        recommendations = self.optimizer.get_optimization_recommendations()
        
        # 最適化設定の生成
        optimized_config = self.optimizer.create_optimized_collection_config(
            "optimized_collection"
        )
        
        # バッチ最適化の適用
        batch_config = self.optimizer.apply_batch_optimization()
        
        optimization_results = {
            "timestamp": time.time(),
            "recommendations": recommendations,
            "optimized_config": optimized_config,
            "batch_config": batch_config,
            "optimization_report": self.optimizer.generate_optimization_report(recommendations)
        }
        
        self.performance_reports.append({
            "type": "optimization",
            "data": optimization_results
        })
        
        print(f"最適化分析完了: {len(recommendations)}個の推奨事項")
        return optimization_results

    def start_monitoring(self, continuous: bool = None) -> Dict[str, Any]:
        """パフォーマンス監視を開始"""
        if not self.monitor:
            return {"error": "監視機能が利用できません（コレクションが未設定）"}
        
        if continuous is None:
            continuous = self.config["monitoring"]["continuous_monitoring"]
        
        if continuous:
            interval = self.config["monitoring"]["monitoring_interval"]
            self.monitor.start_continuous_monitoring(interval)
            print(f"継続監視を開始（間隔: {interval}秒）")
        
        # 初期統計の取得
        initial_stats = self.monitor.get_current_statistics()
        
        monitoring_info = {
            "timestamp": time.time(),
            "continuous_monitoring": continuous,
            "initial_statistics": initial_stats,
            "alert_rules": list(self.monitor.alert_rules.keys())
        }
        
        return monitoring_info

    def stop_monitoring(self):
        """パフォーマンス監視を停止"""
        if self.monitor:
            self.monitor.stop_continuous_monitoring()
            print("監視を停止しました")

    def get_performance_dashboard(self) -> Dict[str, Any]:
        """パフォーマンスダッシュボード情報を取得"""
        dashboard = {
            "timestamp": time.time(),
            "system_status": "稼働中"
        }
        
        # コード分析結果のサマリー
        if self.analysis_results:
            latest_analysis = max(
                self.analysis_results.values(),
                key=lambda x: x["timestamp"]
            )
            dashboard["code_analysis"] = latest_analysis["summary"]
        
        # 監視統計
        if self.monitor:
            try:
                current_stats = self.monitor.get_current_statistics()
                recent_alerts = self.monitor.get_alert_history(hours=24)
                trend_analysis = self.monitor.analyze_trends()
                
                dashboard["monitoring"] = {
                    "current_stats": current_stats,
                    "alert_count_24h": len(recent_alerts),
                    "trends": trend_analysis.get("trends", {}),
                    "recommendations": trend_analysis.get("recommendation", [])
                }
            except Exception as e:
                dashboard["monitoring"] = {"error": str(e)}
        
        # 最適化状況
        if self.optimizer:
            try:
                characteristics = self.optimizer.analyze_collection_characteristics()
                dashboard["collection_info"] = characteristics
            except Exception as e:
                dashboard["collection_info"] = {"error": str(e)}
        
        return dashboard

    def generate_comprehensive_report(self, output_dir: str = None) -> str:
        """包括的なパフォーマンスレポートを生成"""
        if output_dir is None:
            output_dir = "performance_reports"
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = int(time.time())
        
        # 各種レポートの生成
        reports = {}
        
        # 1. コード分析レポート
        if self.analysis_results:
            code_report_path = output_path / f"code_analysis_{timestamp}.json"
            with open(code_report_path, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_results, f, indent=2, ensure_ascii=False, default=str)
            reports["code_analysis"] = str(code_report_path)
        
        # 2. ベンチマークレポート
        if self.benchmark:
            benchmark_report_path = output_path / f"benchmark_{timestamp}.json"
            self.benchmark.export_results(str(benchmark_report_path))
            reports["benchmark"] = str(benchmark_report_path)
        
        # 3. 最適化レポート
        if self.optimizer:
            optimization_report_path = output_path / f"optimization_{timestamp}.json"
            self.optimizer.export_optimization_config(str(optimization_report_path))
            reports["optimization"] = str(optimization_report_path)
        
        # 4. 監視レポート
        if self.monitor:
            monitoring_report_path = output_path / f"monitoring_{timestamp}.json"
            self.monitor.export_monitoring_report(str(monitoring_report_path))
            reports["monitoring"] = str(monitoring_report_path)
        
        # 5. 統合レポート
        comprehensive_report = {
            "generation_timestamp": time.time(),
            "report_files": reports,
            "dashboard": self.get_performance_dashboard(),
            "summary": self._generate_executive_summary()
        }
        
        comprehensive_report_path = output_path / f"comprehensive_report_{timestamp}.json"
        with open(comprehensive_report_path, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"包括的レポートを生成: {comprehensive_report_path}")
        return str(comprehensive_report_path)

    def _summarize_code_analysis(self, results: Dict[str, PerformanceMetrics]) -> Dict[str, Any]:
        """コード分析結果のサマリーを生成"""
        if not results:
            return {}
        
        scores = [metrics.performance_score for metrics in results.values()]
        complexities = [metrics.time_complexity for metrics in results.values()]
        bottlenecks = [len(metrics.bottlenecks) for metrics in results.values()]
        
        return {
            "total_analyzed": len(results),
            "average_score": sum(scores) / len(scores),
            "common_complexities": list(set(complexities)),
            "total_bottlenecks": sum(bottlenecks),
            "needs_optimization": sum(1 for score in scores if score < 0.7)
        }

    def _generate_benchmark_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """ベンチマーク結果に基づく推奨事項を生成"""
        recommendations = []
        
        if "results" in results:
            # 挿入パフォーマンスの分析
            insert_results = results["results"].get("bulk_insert", {})
            if insert_results:
                best_insert = max(
                    insert_results.values(),
                    key=lambda x: x.items_per_second if hasattr(x, 'items_per_second') else 0
                )
                if hasattr(best_insert, 'additional_metrics'):
                    batch_size = best_insert.additional_metrics.get("batch_size", 100)
                    recommendations.append(f"推奨バッチサイズ: {batch_size} (最高スループット: {best_insert.items_per_second:.1f} items/sec)")
            
            # 検索パフォーマンスの分析
            search_results = results["results"].get("search", {})
            if search_results:
                best_search = max(
                    search_results.values(),
                    key=lambda x: x.items_per_second if hasattr(x, 'items_per_second') else 0
                )
                if hasattr(best_search, 'additional_metrics'):
                    top_k = best_search.additional_metrics.get("top_k", 10)
                    recommendations.append(f"推奨検索数(top_k): {top_k} (最高スループット: {best_search.items_per_second:.1f} queries/sec)")
        
        if not recommendations:
            recommendations.append("ベンチマーク結果に基づく具体的な推奨事項はありません")
        
        return recommendations

    def _generate_executive_summary(self) -> Dict[str, Any]:
        """エグゼクティブサマリーを生成"""
        summary = {
            "timestamp": time.time(),
            "overall_status": "正常",
            "key_findings": [],
            "action_items": [],
            "performance_score": 0.8
        }
        
        # コード分析からのキーファインディング
        if self.analysis_results:
            for analysis_type, data in self.analysis_results.items():
                analysis_summary = data.get("summary", {})
                needs_optimization = analysis_summary.get("needs_optimization", 0)
                total_analyzed = analysis_summary.get("total_analyzed", 1)
                
                if needs_optimization / total_analyzed > 0.3:
                    summary["key_findings"].append(f"{analysis_type}: 30%以上の関数で最適化が必要")
                    summary["action_items"].append("コード最適化の計画策定")
        
        # 監視からのキーファインディング
        if self.monitor:
            recent_alerts = self.monitor.get_alert_history(hours=24)
            critical_alerts = [a for a in recent_alerts if a.severity == "Critical"]
            
            if critical_alerts:
                summary["key_findings"].append(f"24時間以内にクリティカルアラート{len(critical_alerts)}件")
                summary["action_items"].append("クリティカルアラートの原因調査と対策")
                summary["overall_status"] = "要注意"
        
        if not summary["key_findings"]:
            summary["key_findings"].append("パフォーマンスは良好な状態を維持")
        
        if not summary["action_items"]:
            summary["action_items"].append("継続的な監視を維持")
        
        return summary

    def _handle_alert(self, alert: Alert):
        """アラートハンドリング"""
        print(f"🚨 アラート: {alert.message}")
        
        # クリティカルアラートの場合は追加アクション
        if alert.severity == "Critical":
            print("クリティカルアラートが発生しました。緊急対応が必要です。")


# 使用例のデモ関数
def demo_performance_management():
    """パフォーマンス管理のデモ"""
    print("=== パフォーマンス管理統合デモ ===")
    
    # サンプルコード
    sample_code = """
def inefficient_search(data, target):
    result = []
    for i in range(len(data)):
        for j in range(len(data)):
            if data[i] == target:
                result.append(i)
    return result
    """
    
    # パフォーマンス管理の初期化
    manager = PerformanceManager()
    
    print("\n1. コード分析")
    code_results = manager.analyze_code_performance(sample_code)
    for func_name, metrics in code_results.items():
        print(f"  {func_name}: スコア {metrics.performance_score:.2f}, 複雑度 {metrics.time_complexity}")
    
    print("\n2. ダッシュボード")
    dashboard = manager.get_performance_dashboard()
    print(f"  システム状態: {dashboard['system_status']}")
    if "code_analysis" in dashboard:
        print(f"  分析済み関数: {dashboard['code_analysis']['total_analyzed']}")
    
    print("\n3. レポート生成")
    report_path = manager.generate_comprehensive_report()
    print(f"  レポート保存先: {report_path}")
    
    print("\nデモ完了")


if __name__ == "__main__":
    demo_performance_management()