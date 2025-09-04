"""
パフォーマンス監視・アラートモジュール

このモジュールはChromaDBのパフォーマンスを継続的に監視し、
問題を早期発見するためのアラート機能を提供します。
"""

import time
import json
import statistics
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from collections import deque
from pathlib import Path
import threading
import logging


@dataclass
class PerformanceSnapshot:
    """パフォーマンススナップショット"""
    timestamp: float
    operation_type: str  # 'search', 'insert', 'filter'
    response_time: float  # 秒
    collection_size: int
    success: bool
    additional_metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_metrics is None:
            self.additional_metrics = {}


@dataclass
class AlertRule:
    """アラートルール"""
    name: str
    condition: str  # 条件式（例: "avg_response_time > 1.0"）
    threshold_value: float
    evaluation_window: int  # 評価ウィンドウ（秒）
    severity: str  # 'Critical', 'Warning', 'Info'
    enabled: bool = True
    cooldown_period: int = 300  # クールダウン期間（秒）


@dataclass
class Alert:
    """アラート"""
    rule_name: str
    message: str
    severity: str
    timestamp: float
    current_value: float
    threshold_value: float
    additional_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}


class ChromaDBPerformanceMonitor:
    """ChromaDBのパフォーマンス監視とアラート管理クラス"""
    
    def __init__(self, 
                 collection=None,
                 history_size: int = 1000,
                 alert_callback: Optional[Callable[[Alert], None]] = None):
        """
        パフォーマンス監視の初期化
        
        Args:
            collection: ChromaDBのコレクションオブジェクト
            history_size: 保持する履歴データの最大数
            alert_callback: アラート発生時のコールバック関数
        """
        self.collection = collection
        self.history_size = history_size
        self.alert_callback = alert_callback or self._default_alert_callback
        
        # パフォーマンス履歴（固定サイズキュー）
        self.performance_history = deque(maxlen=history_size)
        
        # アラートルール
        self.alert_rules = {}
        self._setup_default_alert_rules()
        
        # アラート履歴とクールダウン管理
        self.alert_history = deque(maxlen=100)
        self.last_alert_times = {}
        
        # 統計情報
        self.statistics_cache = {}
        self.cache_expiry = 0
        self.cache_duration = 60  # 1分間キャッシュ
        
        # ロギング設定
        self.logger = logging.getLogger(__name__)
        
        # 監視状態
        self.monitoring_active = False
        self.monitoring_thread = None

    def _setup_default_alert_rules(self):
        """デフォルトのアラートルールを設定"""
        default_rules = [
            AlertRule(
                name="高レスポンス時間",
                condition="avg_response_time > threshold",
                threshold_value=1.0,
                evaluation_window=300,
                severity="Warning"
            ),
            AlertRule(
                name="極めて高いレスポンス時間",
                condition="avg_response_time > threshold",
                threshold_value=3.0,
                evaluation_window=60,
                severity="Critical"
            ),
            AlertRule(
                name="低成功率",
                condition="success_rate < threshold",
                threshold_value=0.95,
                evaluation_window=300,
                severity="Warning"
            ),
            AlertRule(
                name="極めて低い成功率",
                condition="success_rate < threshold",
                threshold_value=0.80,
                evaluation_window=60,
                severity="Critical"
            ),
            AlertRule(
                name="検索パフォーマンス劣化",
                condition="search_avg_time > threshold",
                threshold_value=0.5,
                evaluation_window=600,
                severity="Warning"
            ),
            AlertRule(
                name="挿入パフォーマンス劣化",
                condition="insert_avg_time > threshold",
                threshold_value=2.0,
                evaluation_window=600,
                severity="Warning"
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.name] = rule

    def record_performance(self, 
                         operation_type: str,
                         response_time: float,
                         success: bool = True,
                         additional_metrics: Dict[str, Any] = None):
        """パフォーマンスデータを記録"""
        try:
            collection_size = self.collection.count() if self.collection else 0
        except:
            collection_size = 0
        
        snapshot = PerformanceSnapshot(
            timestamp=time.time(),
            operation_type=operation_type,
            response_time=response_time,
            collection_size=collection_size,
            success=success,
            additional_metrics=additional_metrics or {}
        )
        
        self.performance_history.append(snapshot)
        
        # キャッシュをクリア（新しいデータが追加されたため）
        self._clear_statistics_cache()
        
        # アラートチェック
        self._check_alerts()

    def get_current_statistics(self, time_window: int = 300) -> Dict[str, Any]:
        """現在の統計情報を取得"""
        current_time = time.time()
        
        # キャッシュチェック
        if (current_time < self.cache_expiry and 
            f"stats_{time_window}" in self.statistics_cache):
            return self.statistics_cache[f"stats_{time_window}"]
        
        # 指定時間窓内のデータを取得
        cutoff_time = current_time - time_window
        recent_data = [
            snapshot for snapshot in self.performance_history
            if snapshot.timestamp >= cutoff_time
        ]
        
        if not recent_data:
            return {"error": "データが不足しています"}
        
        # 統計計算
        stats = self._calculate_statistics(recent_data)
        
        # キャッシュに保存
        self.statistics_cache[f"stats_{time_window}"] = stats
        self.cache_expiry = current_time + self.cache_duration
        
        return stats

    def _calculate_statistics(self, data: List[PerformanceSnapshot]) -> Dict[str, Any]:
        """統計情報を計算"""
        if not data:
            return {}
        
        # 基本統計
        response_times = [d.response_time for d in data]
        successes = [d.success for d in data]
        
        stats = {
            "data_points": len(data),
            "time_range": {
                "start": min(d.timestamp for d in data),
                "end": max(d.timestamp for d in data)
            },
            "response_time": {
                "avg": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "min": min(response_times),
                "max": max(response_times),
                "std_dev": statistics.stdev(response_times) if len(response_times) > 1 else 0
            },
            "success_rate": sum(successes) / len(successes),
            "operations_per_second": len(data) / (max(d.timestamp for d in data) - min(d.timestamp for d in data))
        }
        
        # 操作タイプ別統計
        operation_stats = {}
        for op_type in set(d.operation_type for d in data):
            op_data = [d for d in data if d.operation_type == op_type]
            if op_data:
                op_times = [d.response_time for d in op_data]
                op_successes = [d.success for d in op_data]
                
                operation_stats[op_type] = {
                    "count": len(op_data),
                    "avg_time": statistics.mean(op_times),
                    "success_rate": sum(op_successes) / len(op_successes)
                }
        
        stats["by_operation"] = operation_stats
        
        return stats

    def add_alert_rule(self, rule: AlertRule):
        """アラートルールを追加"""
        self.alert_rules[rule.name] = rule
        self.logger.info(f"アラートルール追加: {rule.name}")

    def remove_alert_rule(self, rule_name: str):
        """アラートルールを削除"""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            self.logger.info(f"アラートルール削除: {rule_name}")

    def _check_alerts(self):
        """アラート条件をチェック"""
        current_time = time.time()
        
        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            # クールダウンチェック
            if rule_name in self.last_alert_times:
                if current_time - self.last_alert_times[rule_name] < rule.cooldown_period:
                    continue
            
            # アラート条件評価
            if self._evaluate_alert_condition(rule):
                alert = self._create_alert(rule)
                self._trigger_alert(alert)
                self.last_alert_times[rule_name] = current_time

    def _evaluate_alert_condition(self, rule: AlertRule) -> bool:
        """アラート条件を評価"""
        try:
            stats = self.get_current_statistics(rule.evaluation_window)
            
            if "error" in stats:
                return False
            
            # 条件に応じた評価
            if "avg_response_time" in rule.condition:
                current_value = stats["response_time"]["avg"]
                return current_value > rule.threshold_value
            
            elif "success_rate" in rule.condition:
                current_value = stats["success_rate"]
                return current_value < rule.threshold_value
            
            elif "search_avg_time" in rule.condition:
                search_stats = stats["by_operation"].get("search", {})
                if search_stats:
                    current_value = search_stats["avg_time"]
                    return current_value > rule.threshold_value
            
            elif "insert_avg_time" in rule.condition:
                insert_stats = stats["by_operation"].get("insert", {})
                if insert_stats:
                    current_value = insert_stats["avg_time"]
                    return current_value > rule.threshold_value
            
            return False
            
        except Exception as e:
            self.logger.error(f"アラート条件評価エラー: {str(e)}")
            return False

    def _create_alert(self, rule: AlertRule) -> Alert:
        """アラートを作成"""
        stats = self.get_current_statistics(rule.evaluation_window)
        
        # 現在値を取得
        current_value = 0.0
        if "avg_response_time" in rule.condition:
            current_value = stats["response_time"]["avg"]
        elif "success_rate" in rule.condition:
            current_value = stats["success_rate"]
        elif "search_avg_time" in rule.condition:
            search_stats = stats["by_operation"].get("search", {})
            current_value = search_stats.get("avg_time", 0.0)
        elif "insert_avg_time" in rule.condition:
            insert_stats = stats["by_operation"].get("insert", {})
            current_value = insert_stats.get("avg_time", 0.0)
        
        message = f"{rule.name}: 現在値 {current_value:.3f}, 閾値 {rule.threshold_value}"
        
        return Alert(
            rule_name=rule.name,
            message=message,
            severity=rule.severity,
            timestamp=time.time(),
            current_value=current_value,
            threshold_value=rule.threshold_value,
            additional_data={"stats": stats}
        )

    def _trigger_alert(self, alert: Alert):
        """アラートを発火"""
        self.alert_history.append(alert)
        self.logger.warning(f"アラート発生: {alert.message}")
        
        try:
            self.alert_callback(alert)
        except Exception as e:
            self.logger.error(f"アラートコールバックエラー: {str(e)}")

    def _default_alert_callback(self, alert: Alert):
        """デフォルトのアラートコールバック"""
        severity_symbol = {
            "Critical": "🚨",
            "Warning": "⚠️", 
            "Info": "ℹ️"
        }.get(alert.severity, "📢")
        
        print(f"{severity_symbol} {alert.severity}: {alert.message}")

    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """アラート履歴を取得"""
        cutoff_time = time.time() - (hours * 3600)
        return [
            alert for alert in self.alert_history
            if alert.timestamp >= cutoff_time
        ]

    def analyze_trends(self, time_window: int = 3600) -> Dict[str, Any]:
        """パフォーマンストレンドを分析"""
        current_time = time.time()
        
        # 現在と過去の統計を比較
        current_stats = self.get_current_statistics(time_window // 2)
        past_cutoff = current_time - time_window
        mid_cutoff = current_time - (time_window // 2)
        
        past_data = [
            snapshot for snapshot in self.performance_history
            if past_cutoff <= snapshot.timestamp < mid_cutoff
        ]
        
        if not past_data or "error" in current_stats:
            return {"error": "トレンド分析に十分なデータがありません"}
        
        past_stats = self._calculate_statistics(past_data)
        
        # トレンド計算
        trends = {}
        
        # レスポンス時間のトレンド
        current_avg = current_stats["response_time"]["avg"]
        past_avg = past_stats["response_time"]["avg"]
        time_trend = "改善" if current_avg < past_avg else "悪化"
        time_change_pct = ((current_avg - past_avg) / past_avg) * 100
        
        trends["response_time"] = {
            "direction": time_trend,
            "change_percent": time_change_pct,
            "current": current_avg,
            "past": past_avg
        }
        
        # 成功率のトレンド
        current_success = current_stats["success_rate"]
        past_success = past_stats["success_rate"]
        success_trend = "改善" if current_success > past_success else "悪化"
        success_change_pct = ((current_success - past_success) / past_success) * 100
        
        trends["success_rate"] = {
            "direction": success_trend,
            "change_percent": success_change_pct,
            "current": current_success,
            "past": past_success
        }
        
        # スループットのトレンド
        current_throughput = current_stats["operations_per_second"]
        past_throughput = past_stats["operations_per_second"]
        throughput_trend = "改善" if current_throughput > past_throughput else "悪化"
        throughput_change_pct = ((current_throughput - past_throughput) / past_throughput) * 100
        
        trends["throughput"] = {
            "direction": throughput_trend,
            "change_percent": throughput_change_pct,
            "current": current_throughput,
            "past": past_throughput
        }
        
        return {
            "analysis_window": time_window,
            "trends": trends,
            "recommendation": self._generate_trend_recommendations(trends)
        }

    def _generate_trend_recommendations(self, trends: Dict[str, Any]) -> List[str]:
        """トレンド分析に基づく推奨事項を生成"""
        recommendations = []
        
        # レスポンス時間の悪化
        if trends["response_time"]["direction"] == "悪化":
            if abs(trends["response_time"]["change_percent"]) > 20:
                recommendations.append("レスポンス時間が大幅に悪化しています。インデックスの最適化を検討してください。")
            else:
                recommendations.append("レスポンス時間が悪化傾向にあります。システム負荷を確認してください。")
        
        # 成功率の悪化
        if trends["success_rate"]["direction"] == "悪化":
            recommendations.append("成功率が低下しています。エラーログを確認し、障害の原因を特定してください。")
        
        # スループットの悪化
        if trends["throughput"]["direction"] == "悪化":
            if abs(trends["throughput"]["change_percent"]) > 30:
                recommendations.append("スループットが大幅に低下しています。システムリソースの増強を検討してください。")
        
        if not recommendations:
            recommendations.append("パフォーマンスは安定しています。")
        
        return recommendations

    def _clear_statistics_cache(self):
        """統計キャッシュをクリア"""
        self.statistics_cache.clear()
        self.cache_expiry = 0

    def export_monitoring_report(self, output_path: str = None) -> str:
        """監視レポートをエクスポート"""
        if output_path is None:
            timestamp = int(time.time())
            output_path = f"performance_monitoring_report_{timestamp}.json"
        
        # レポートデータの準備
        report_data = {
            "timestamp": time.time(),
            "collection_info": {
                "name": getattr(self.collection, 'name', 'unknown'),
                "size": self.collection.count() if self.collection else 0
            },
            "current_statistics": self.get_current_statistics(),
            "trend_analysis": self.analyze_trends(),
            "alert_rules": {name: asdict(rule) for name, rule in self.alert_rules.items()},
            "recent_alerts": [asdict(alert) for alert in self.get_alert_history()],
            "performance_summary": {
                "total_data_points": len(self.performance_history),
                "monitoring_duration_hours": (
                    (max(d.timestamp for d in self.performance_history) - 
                     min(d.timestamp for d in self.performance_history)) / 3600
                ) if self.performance_history else 0
            }
        }
        
        # ファイルに保存
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"監視レポートを {output_path} に保存しました")
        return output_path

    def start_continuous_monitoring(self, interval: int = 60):
        """継続的な監視を開始"""
        if self.monitoring_active:
            print("監視は既に開始されています")
            return
        
        self.monitoring_active = True
        
        def monitoring_loop():
            while self.monitoring_active:
                try:
                    # 定期的な統計更新とアラートチェック
                    self.get_current_statistics()
                    time.sleep(interval)
                except Exception as e:
                    self.logger.error(f"監視ループエラー: {str(e)}")
                    time.sleep(10)
        
        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        print(f"継続監視を開始しました（間隔: {interval}秒）")

    def stop_continuous_monitoring(self):
        """継続的な監視を停止"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        print("継続監視を停止しました")


# 使用例のデモ関数
def demo_monitor():
    """パフォーマンス監視のデモ"""
    print("ChromaDBパフォーマンス監視のデモ")
    
    # モックコレクション（デモ用）
    class MockCollection:
        def __init__(self):
            self.name = "demo_collection"
            self._count = 1000
        
        def count(self):
            return self._count
    
    # デモ実行
    mock_collection = MockCollection()
    monitor = ChromaDBPerformanceMonitor(mock_collection)
    
    print("\n1. パフォーマンスデータの記録")
    # サンプルデータの記録
    import random
    for i in range(20):
        response_time = random.uniform(0.1, 2.0)
        success = random.random() > 0.05  # 95%成功率
        operation = random.choice(["search", "insert", "filter"])
        
        monitor.record_performance(operation, response_time, success)
    
    print(f"記録されたデータポイント: {len(monitor.performance_history)}")
    
    print("\n2. 統計情報の取得")
    stats = monitor.get_current_statistics()
    print(f"平均レスポンス時間: {stats['response_time']['avg']:.3f}秒")
    print(f"成功率: {stats['success_rate']*100:.1f}%")
    
    print("\n3. アラートルールのテスト")
    # 高レスポンス時間をシミュレート
    monitor.record_performance("search", 5.0, True)  # 閾値超過
    
    print("\n4. アラート履歴")
    alerts = monitor.get_alert_history()
    print(f"アラート数: {len(alerts)}")
    
    for alert in alerts[-3:]:  # 最新3件
        print(f"- {alert.severity}: {alert.message}")
    
    print("\n5. トレンド分析")
    trends = monitor.analyze_trends()
    if "error" not in trends:
        for metric, trend_data in trends["trends"].items():
            print(f"{metric}: {trend_data['direction']} ({trend_data['change_percent']:+.1f}%)")
    
    print("\n6. レポートエクスポート")
    report_path = monitor.export_monitoring_report()
    print(f"レポート生成: {report_path}")


if __name__ == "__main__":
    demo_monitor()