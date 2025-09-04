"""
統合パフォーマンスシステム - メインエントリーポイント

既存のperformance_optimizerと新しいパフォーマンス機能を統合し、
包括的なパフォーマンス分析・監視・最適化システムを提供します。
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from .monitor import ChromaDBPerformanceMonitor
    from .benchmark import ChromaDBPerformanceBenchmark
    from .optimizer import ChromaDBOptimizer
    from .analyzer import PerformanceAnalyzer
    from .management import PerformanceManager
    from .legacy_optimizer import PerformanceOptimizer
except ImportError as e:
    logger.error(f"パフォーマンスモジュールのインポートエラー: {e}")
    sys.exit(1)


class IntegratedPerformanceSystem:
    """統合パフォーマンスシステム"""
    
    def __init__(self, collection=None, vector_engine=None):
        """
        統合パフォーマンスシステムを初期化
        
        Args:
            collection: ChromaDBコレクション
            vector_engine: ベクトル検索エンジン
        """
        self.collection = collection
        self.vector_engine = vector_engine
        
        # 各コンポーネントを初期化
        self.monitor = ChromaDBPerformanceMonitor(collection) if collection else None
        self.benchmark = ChromaDBPerformanceBenchmark(collection) if collection else None
        self.optimizer = ChromaDBOptimizer(collection) if collection else None
        self.analyzer = PerformanceAnalyzer()
        self.legacy_optimizer = PerformanceOptimizer(vector_engine) if vector_engine else None
        
        # 統合管理
        self.manager = PerformanceManager(collection) if collection else None
        
        logger.info("統合パフォーマンスシステムが初期化されました")
    
    def run_comprehensive_analysis(self, code: str = None, queries: list = None) -> Dict[str, Any]:
        """
        包括的なパフォーマンス分析を実行
        
        Args:
            code: 分析対象のコード
            queries: ベンチマーク用クエリ
            
        Returns:
            Dict[str, Any]: 分析結果
        """
        results = {}
        
        # 1. コードパフォーマンス分析
        if code:
            logger.info("コードパフォーマンス分析を実行中...")
            try:
                code_metrics = self.analyzer.analyze_code(code)
                results['code_analysis'] = code_metrics
                logger.info("コード分析完了")
            except Exception as e:
                logger.error(f"コード分析エラー: {e}")
                results['code_analysis'] = {'error': str(e)}
        
        # 2. ChromaDBベンチマーク
        if self.benchmark and queries:
            logger.info("ChromaDBベンチマークを実行中...")
            try:
                benchmark_results = self.benchmark.run_comprehensive_benchmark()
                results['chromadb_benchmark'] = benchmark_results
                logger.info("ベンチマーク完了")
            except Exception as e:
                logger.error(f"ベンチマークエラー: {e}")
                results['chromadb_benchmark'] = {'error': str(e)}
        
        # 3. ベクトル検索パフォーマンス（既存機能）
        if self.legacy_optimizer and queries:
            logger.info("ベクトル検索パフォーマンス分析を実行中...")
            try:
                search_results = self.legacy_optimizer.benchmark_search_performance(queries)
                results['vector_search_benchmark'] = search_results
                logger.info("ベクトル検索分析完了")
            except Exception as e:
                logger.error(f"ベクトル検索分析エラー: {e}")
                results['vector_search_benchmark'] = {'error': str(e)}
        
        # 4. 最適化推奨事項
        if self.optimizer:
            logger.info("最適化推奨事項を生成中...")
            try:
                optimization_recommendations = self.optimizer.get_optimization_recommendations()
                results['optimization_recommendations'] = optimization_recommendations
                logger.info("最適化推奨事項生成完了")
            except Exception as e:
                logger.error(f"最適化推奨事項生成エラー: {e}")
                results['optimization_recommendations'] = {'error': str(e)}
        
        return results
    
    def start_monitoring(self, alert_callback=None):
        """パフォーマンス監視を開始"""
        if self.monitor:
            logger.info("パフォーマンス監視を開始します...")
            self.monitor.start_continuous_monitoring()
            if alert_callback:
                self.monitor.set_alert_callback(alert_callback)
            logger.info("パフォーマンス監視が開始されました")
        else:
            logger.warning("ChromaDBコレクションが設定されていないため、監視を開始できません")
    
    def stop_monitoring(self):
        """パフォーマンス監視を停止"""
        if self.monitor:
            logger.info("パフォーマンス監視を停止します...")
            self.monitor.stop_monitoring()
            logger.info("パフォーマンス監視が停止されました")
    
    def generate_report(self, output_path: str = None) -> str:
        """
        包括的なパフォーマンスレポートを生成
        
        Args:
            output_path: 出力ファイルパス（省略時は標準出力）
            
        Returns:
            str: レポート内容
        """
        if self.manager:
            logger.info("包括的レポートを生成中...")
            try:
                report = self.manager.generate_comprehensive_report()
                
                if output_path:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(report)
                    logger.info(f"レポートを保存しました: {output_path}")
                else:
                    print("\n" + "="*50)
                    print("パフォーマンスレポート")
                    print("="*50)
                    print(report)
                
                return report
            except Exception as e:
                logger.error(f"レポート生成エラー: {e}")
                return f"レポート生成エラー: {e}"
        else:
            logger.warning("パフォーマンスマネージャーが利用できません")
            return "パフォーマンスマネージャーが利用できません"


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="統合パフォーマンスシステム")
    parser.add_argument("--code", help="分析対象のコードファイル")
    parser.add_argument("--queries", nargs="+", help="ベンチマーク用クエリ")
    parser.add_argument("--monitor", action="store_true", help="パフォーマンス監視を開始")
    parser.add_argument("--report", help="レポート出力ファイルパス")
    parser.add_argument("--collection", help="ChromaDBコレクションパス")
    
    args = parser.parse_args()
    
    # システムを初期化
    system = IntegratedPerformanceSystem()
    
    # コード分析
    if args.code:
        with open(args.code, 'r', encoding='utf-8') as f:
            code = f.read()
        results = system.run_comprehensive_analysis(code=code, queries=args.queries)
        print("分析結果:", results)
    
    # 監視開始
    if args.monitor:
        system.start_monitoring()
        try:
            input("監視を停止するにはEnterキーを押してください...")
        except KeyboardInterrupt:
            pass
        finally:
            system.stop_monitoring()
    
    # レポート生成
    if args.report:
        system.generate_report(args.report)


if __name__ == "__main__":
    main()
