# 統合パフォーマンスシステム

## 概要

このフォルダには、既存の`performance_optimizer.py`と新しいパフォーマンス機能を統合した包括的なパフォーマンス分析・監視・最適化システムが含まれています。

## 統合されたコンポーネント

### 1. **既存機能（Legacy）**
- `legacy_optimizer.py` - 元の`performance_optimizer.py`
  - ベクトル検索のパフォーマンス測定
  - 検索時間の統計分析
  - 既存のコードとの互換性を保持

### 2. **新機能（Enhanced）**
- `monitor.py` - リアルタイムパフォーマンス監視
- `benchmark.py` - ChromaDBベンチマーク
- `optimizer.py` - ChromaDB最適化推奨
- `analyzer.py` - コードパフォーマンス分析
- `management.py` - 統合管理インターフェース

### 3. **統合インターフェース**
- `main.py` - メインエントリーポイント
  - 全機能への統一されたアクセス
  - 包括的なパフォーマンス分析
  - リアルタイム監視制御

## 使用方法

### 基本的な使用

```python
from performance.main import IntegratedPerformanceSystem

# システムを初期化
system = IntegratedPerformanceSystem()

# 包括的な分析を実行
results = system.run_comprehensive_analysis(
    code="your_code_here",
    queries=["query1", "query2", "query3"]
)

# パフォーマンス監視を開始
system.start_monitoring()

# レポートを生成
report = system.generate_report("performance_report.txt")
```

### コマンドラインからの使用

```bash
# コード分析
python performance/main.py --code your_file.py --queries "query1" "query2"

# パフォーマンス監視
python performance/main.py --monitor

# レポート生成
python performance/main.py --report report.txt
```

## 機能の詳細

### パフォーマンス監視
- リアルタイム統計情報の収集
- アラートルールの管理
- トレンド分析と予測
- 継続的な監視とログ記録

### ChromaDB最適化
- HNSWパラメータの最適化提案
- バッチサイズの推奨
- メタデータ構造の最適化
- パフォーマンスボトルネックの特定

### コード分析
- 静的解析によるパフォーマンス特性の分析
- 時間計算量・空間計算量の自動推定
- ボトルネックの検出と最適化提案
- パフォーマンススコアの算出

### ベンチマーク
- 包括的なパフォーマンス測定
- バッチ挿入性能の測定
- 検索性能の測定
- フィルタリング性能の測定

## 設定とカスタマイズ

### アラートルールの設定
```python
from performance.monitor import ChromaDBPerformanceMonitor

monitor = ChromaDBPerformanceMonitor(collection)

# カスタムアラートルールを追加
monitor.add_alert_rule(
    name="high_response_time",
    condition="avg_response_time > 1.0",
    threshold_value=1.0,
    evaluation_window=60,
    severity="Warning"
)
```

### 最適化パラメータの調整
```python
from performance.optimizer import ChromaDBOptimizer

optimizer = ChromaDBOptimizer(collection)

# 最適化設定をカスタマイズ
optimizer.set_optimization_parameters(
    target_accuracy=0.95,
    max_memory_usage="2GB",
    preferred_speed_over_accuracy=False
)
```

## 統合の利点

### 1. **機能の重複排除**
- 既存の`performance_optimizer.py`と新しい機能の統合
- 重複する機能の整理と最適化

### 2. **統一されたインターフェース**
- 全パフォーマンス機能への単一のアクセスポイント
- 一貫したAPI設計と使用方法

### 3. **包括的な分析**
- コード、データベース、検索の全側面のパフォーマンス分析
- 統合されたレポートと推奨事項

### 4. **拡張性**
- 新しいパフォーマンス機能の簡単な追加
- モジュラー設計による保守性の向上

## 移行ガイド

### 既存コードからの移行

**Before (旧方式):**
```python
from integration.performance_optimizer import PerformanceOptimizer

optimizer = PerformanceOptimizer(vector_engine)
results = optimizer.benchmark_search_performance(queries)
```

**After (新方式):**
```python
from performance.main import IntegratedPerformanceSystem

system = IntegratedPerformanceSystem(vector_engine=vector_engine)
results = system.run_comprehensive_analysis(queries=queries)
```

### 互換性の保持
- 既存の`PerformanceOptimizer`クラスは`legacy_optimizer.py`として保持
- 既存のコードは変更なしで動作
- 段階的な移行が可能

## 今後の改善計画

### 短期（1-2週間）
- [ ] パフォーマンスダッシュボードの実装
- [ ] 自動最適化機能の強化
- [ ] より詳細なベンチマークメトリクス

### 中期（1-2ヶ月）
- [ ] 機械学習によるパフォーマンス予測
- [ ] 分散処理対応
- [ ] クラウドネイティブ機能

### 長期（3-6ヶ月）
- [ ] リアルタイム最適化エンジン
- [ ] 予測的メンテナンス
- [ ] 自動スケーリング機能

## まとめ

統合パフォーマンスシステムにより、以下の改善が実現されました：

1. **機能の統合**: 既存と新機能の最適な組み合わせ
2. **使いやすさ**: 統一されたインターフェース
3. **拡張性**: モジュラー設計による将来の拡張
4. **保守性**: 重複排除と整理された構造

これにより、パフォーマンス分析・監視・最適化の全機能を効率的に活用できるようになりました。
