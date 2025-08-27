# パフォーマンス分析・最適化システム

このディレクトリには、Pythonコードのパフォーマンス分析とChromaDBの最適化に関する機能が含まれています。

## 概要

独自APIを活用したPythonコード生成を目指すシステムにおいて、パフォーマンスの分析・監視・最適化を行うための包括的なツールセットです。

## 主要コンポーネント

### 1. `performance_analyzer.py`
Pythonコードの静的解析によるパフォーマンス特性の分析

**主な機能:**
- 時間計算量・空間計算量の自動推定
- ボトルネックの検出
- 最適化提案の生成
- パフォーマンススコアの算出

**使用例:**
```python
from performance_analyzer import PerformanceAnalyzer

analyzer = PerformanceAnalyzer()
metrics = analyzer.analyze_code(your_code)
print(f"パフォーマンススコア: {metrics.performance_score}")
print(f"時間計算量: {metrics.time_complexity}")
```

### 2. `chromadb_benchmark.py`
ChromaDBのパフォーマンスベンチマーク

**主な機能:**
- バッチ挿入性能の測定
- 検索性能の測定
- フィルタリング性能の測定
- 包括的なベンチマークレポート生成

**使用例:**
```python
from chromadb_benchmark import ChromaDBPerformanceBenchmark

benchmark = ChromaDBPerformanceBenchmark(your_collection)
results = benchmark.run_comprehensive_benchmark()
benchmark.print_summary_report()
```

### 3. `chromadb_optimizer.py`
ChromaDBの最適化推奨事項の生成

**主な機能:**
- HNSWパラメータの最適化提案
- バッチサイズの推奨
- メタデータ構造の最適化
- 最適化レポートの生成

**使用例:**
```python
from chromadb_optimizer import ChromaDBOptimizer

optimizer = ChromaDBOptimizer(your_collection)
recommendations = optimizer.get_optimization_recommendations()
report = optimizer.generate_optimization_report()
```

### 4. `performance_monitor.py`
リアルタイムパフォーマンス監視とアラート

**主な機能:**
- リアルタイム統計情報の収集
- アラートルールの管理
- トレンド分析
- 継続的な監視

**使用例:**
```python
from performance_monitor import ChromaDBPerformanceMonitor

monitor = ChromaDBPerformanceMonitor(your_collection)
monitor.start_continuous_monitoring()

# パフォーマンス記録
monitor.record_performance("search", response_time=0.5, success=True)
```

### 5. `performance_management.py`
統合的なパフォーマンス管理

**主な機能:**
- 全機能の統合的な利用
- ダッシュボード情報の提供
- 包括的なレポート生成
- 簡単なインターフェース

**使用例:**
```python
from performance_management import PerformanceManager

manager = PerformanceManager(your_collection)

# コード分析
code_results = manager.analyze_code_performance(your_code)

# ベンチマーク実行
benchmark_results = manager.run_comprehensive_benchmark()

# 最適化
optimization_results = manager.optimize_performance()

# 監視開始
monitor_info = manager.start_monitoring(continuous=True)

# レポート生成
report_path = manager.generate_comprehensive_report()
```

## クイックスタート

### 1. 基本的な使用方法

```python
# 統合管理クラスの使用（推奨）
from performance_management import PerformanceManager

# 初期化（ChromaDBコレクションがある場合）
manager = PerformanceManager(collection=your_collection)

# または初期化（コードのみ分析する場合）
manager = PerformanceManager()

# コード分析
sample_code = """
def your_function(data):
    result = []
    for item in data:
        if condition(item):
            result.append(process(item))
    return result
"""

analysis_results = manager.analyze_code_performance(sample_code)
```

### 2. ファイル分析

```python
# Pythonファイルの分析
file_results = manager.analyze_code_performance(
    "path/to/your/file.py", 
    is_file=True
)
```

### 3. ChromaDBのベンチマークと最適化

```python
# ChromaDBコレクションが設定されている場合のみ
if manager.collection:
    # ベンチマーク実行
    benchmark_results = manager.run_comprehensive_benchmark()
    
    # 最適化推奨事項取得
    optimization_results = manager.optimize_performance()
    
    # 監視開始
    manager.start_monitoring(continuous=True)
```

### 4. レポート生成

```python
# 包括的なレポート生成
report_path = manager.generate_comprehensive_report()
print(f"レポートが生成されました: {report_path}")
```

## 設定

### デフォルト設定
```python
default_config = {
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
```

### カスタム設定
```python
custom_config = {
    "benchmark": {
        "collection_sizes": [50, 200],  # 小規模テスト
        "dimension": 256
    },
    "monitoring": {
        "monitoring_interval": 30  # 30秒間隔
    }
}

manager = PerformanceManager(collection, config=custom_config)
```

## 出力ファイル

各機能は以下のファイルを生成します：

- **ベンチマークレポート**: `chromadb_benchmark_results_{timestamp}.json`
- **最適化設定**: `chromadb_optimization_config_{timestamp}.json`
- **監視レポート**: `performance_monitoring_report_{timestamp}.json`
- **包括レポート**: `comprehensive_report_{timestamp}.json`

## パフォーマンス指標

### コード分析
- **パフォーマンススコア**: 0.0-1.0（1.0が最良）
- **時間計算量**: O(1), O(n), O(n²), etc.
- **空間計算量**: メモリ使用量の推定
- **ボトルネック数**: 検出されたパフォーマンス問題の数

### ChromaDB
- **スループット**: 項目/秒 または クエリ/秒
- **レスポンス時間**: 平均・最小・最大・標準偏差
- **成功率**: 操作の成功率（%）
- **メモリ使用量**: 推定メモリ使用量

## アラート

### デフォルトアラートルール
- **高レスポンス時間**: 1秒超過で警告
- **極めて高いレスポンス時間**: 3秒超過でクリティカル
- **低成功率**: 95%未満で警告
- **極めて低い成功率**: 80%未満でクリティカル

### カスタムアラート
```python
from performance_monitor import AlertRule

custom_rule = AlertRule(
    name="カスタムアラート",
    condition="avg_response_time > threshold",
    threshold_value=0.5,
    evaluation_window=60,
    severity="Warning"
)

monitor.add_alert_rule(custom_rule)
```

## 最適化推奨事項

システムが自動的に生成する最適化提案：

1. **HNSWパラメータ最適化**
2. **バッチサイズ調整**
3. **メタデータ構造改善**
4. **コレクション分割**
5. **メモリ使用量削減**

## トラブルシューティング

### よくある問題

1. **ChromaDBコレクションが設定されていない**
   - エラー: "コレクションが設定されていません"
   - 解決策: PerformanceManagerの初期化時にコレクションを渡す

2. **メモリ不足エラー**
   - 症状: 大規模ベンチマーク時のクラッシュ
   - 解決策: collection_sizesとbatch_sizesを小さくする

3. **アラートが発生しない**
   - 確認事項: アラートルールが有効か、閾値が適切か
   - 解決策: monitor.alert_rules の内容を確認

### デバッグ情報の取得

```python
# ダッシュボード情報で現在の状況を確認
dashboard = manager.get_performance_dashboard()
print(json.dumps(dashboard, indent=2, ensure_ascii=False))

# 監視統計の詳細確認
if manager.monitor:
    stats = manager.monitor.get_current_statistics()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
```

## 依存関係

- `numpy`: 数値計算
- `statistics`: 統計計算
- `chromadb`: ベクトルデータベース（ChromaDB機能使用時）
- `pathlib`: ファイルパス操作
- `threading`: 継続監視機能
- `logging`: ログ出力

## 参考資料

- [RAG_IMPROVEMENT_PLAN.md](./RAG_IMPROVEMENT_PLAN.md): 詳細な改善計画
- [treesitter_neo4j_advanced.py](./treesitter_neo4j_advanced.py): コード解析の基盤
- [README_TreeSitter_Neo4j.md](./README_TreeSitter_Neo4j.md): 構文解析に関する情報

---

**注意**: このシステムは独自APIを活用したPythonコード生成システムの一部として設計されています。RAGシステムの性能向上とコード生成品質の改善を目的としています。