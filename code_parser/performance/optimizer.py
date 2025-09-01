"""
ChromaDB最適化モジュール

このモジュールはChromaDBのパフォーマンス最適化を行います。
コレクション設定の最適化、インデックス作成、バッチ操作の改善などを提供します。
"""

import time
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class OptimizationRecommendation:
    """最適化推奨事項"""
    category: str  # 最適化カテゴリ
    description: str  # 説明
    priority: str  # 優先度（High, Medium, Low）
    expected_improvement: str  # 期待される改善
    implementation_steps: List[str]  # 実装手順
    estimated_effort: str  # 推定工数


class ChromaDBOptimizer:
    """ChromaDBの最適化を行うクラス"""
    
    def __init__(self, collection=None):
        """
        最適化器の初期化
        
        Args:
            collection: ChromaDBのコレクションオブジェクト
        """
        self.collection = collection
        self.optimization_history = []
        
        # HNSWパラメータの推奨設定
        self.hnsw_recommendations = {
            "small": {  # < 1,000 items
                "construction_ef": 64,
                "search_ef": 32,
                "m": 16,
                "description": "小規模コレクション向け設定"
            },
            "medium": {  # 1,000 - 10,000 items
                "construction_ef": 128,
                "search_ef": 64,
                "m": 32,
                "description": "中規模コレクション向け設定"
            },
            "large": {  # > 10,000 items
                "construction_ef": 256,
                "search_ef": 128,
                "m": 64,
                "description": "大規模コレクション向け設定"
            }
        }
        
        # バッチサイズの推奨設定
        self.batch_size_recommendations = {
            "memory_limited": {
                "insert": 50,
                "search": 10,
                "description": "メモリ制限がある環境向け"
            },
            "balanced": {
                "insert": 100,
                "search": 20,
                "description": "バランス重視"
            },
            "performance": {
                "insert": 500,
                "search": 50,
                "description": "パフォーマンス重視"
            }
        }

    def analyze_collection_characteristics(self) -> Dict[str, Any]:
        """コレクションの特性を分析"""
        if not self.collection:
            return {"error": "コレクションが設定されていません"}
        
        try:
            # 基本情報の取得
            collection_size = self.collection.count()
            
            # サンプルデータの取得（最初の10件）
            sample_data = self.collection.peek(limit=10)
            
            characteristics = {
                "collection_size": collection_size,
                "size_category": self._categorize_size(collection_size),
                "sample_metadata_keys": [],
                "embedding_dimension": None,
                "metadata_complexity": 0
            }
            
            # メタデータの分析
            if sample_data.get('metadatas'):
                metadata_sample = sample_data['metadatas']
                if metadata_sample:
                    # メタデータキーの収集
                    all_keys = set()
                    for metadata in metadata_sample:
                        if isinstance(metadata, dict):
                            all_keys.update(metadata.keys())
                    
                    characteristics["sample_metadata_keys"] = list(all_keys)
                    characteristics["metadata_complexity"] = len(all_keys)
            
            # 埋め込み次元の取得
            if sample_data.get('embeddings') and sample_data['embeddings']:
                characteristics["embedding_dimension"] = len(sample_data['embeddings'][0])
            
            return characteristics
            
        except Exception as e:
            return {"error": f"コレクション分析エラー: {str(e)}"}

    def get_optimization_recommendations(self, 
                                       performance_data: Dict[str, Any] = None) -> List[OptimizationRecommendation]:
        """最適化推奨事項を生成"""
        recommendations = []
        
        # コレクション特性の分析
        characteristics = self.analyze_collection_characteristics()
        
        if "error" in characteristics:
            return [OptimizationRecommendation(
                category="Error",
                description=characteristics["error"],
                priority="High",
                expected_improvement="N/A",
                implementation_steps=["エラーを解決してください"],
                estimated_effort="不明"
            )]
        
        # 1. HNSWパラメータの最適化
        hnsw_rec = self._recommend_hnsw_parameters(characteristics)
        if hnsw_rec:
            recommendations.append(hnsw_rec)
        
        # 2. バッチサイズの最適化
        batch_rec = self._recommend_batch_sizes(characteristics, performance_data)
        if batch_rec:
            recommendations.append(batch_rec)
        
        # 3. メタデータインデックスの最適化
        metadata_rec = self._recommend_metadata_optimization(characteristics)
        if metadata_rec:
            recommendations.append(metadata_rec)
        
        # 4. コレクション分割の提案
        partition_rec = self._recommend_collection_partitioning(characteristics)
        if partition_rec:
            recommendations.append(partition_rec)
        
        # 5. メモリ使用量の最適化
        memory_rec = self._recommend_memory_optimization(characteristics)
        if memory_rec:
            recommendations.append(memory_rec)
        
        return recommendations

    def _categorize_size(self, size: int) -> str:
        """コレクションサイズをカテゴリ分け"""
        if size < 1000:
            return "small"
        elif size < 10000:
            return "medium"
        else:
            return "large"

    def _recommend_hnsw_parameters(self, characteristics: Dict[str, Any]) -> Optional[OptimizationRecommendation]:
        """HNSWパラメータの推奨事項を生成"""
        size_category = characteristics.get("size_category", "medium")
        recommended_params = self.hnsw_recommendations[size_category]
        
        return OptimizationRecommendation(
            category="HNSW Parameters",
            description=f"コレクションサイズ({characteristics.get('collection_size', 0)})に最適化されたHNSWパラメータ",
            priority="High",
            expected_improvement="検索速度10-30%向上",
            implementation_steps=[
                "新しいコレクションを作成時に以下のメタデータを設定:",
                f"  hnsw:construction_ef: {recommended_params['construction_ef']}",
                f"  hnsw:search_ef: {recommended_params['search_ef']}",
                f"  hnsw:m: {recommended_params['m']}",
                "既存データを新しいコレクションに移行"
            ],
            estimated_effort="中程度（1-2時間）"
        )

    def _recommend_batch_sizes(self, 
                             characteristics: Dict[str, Any], 
                             performance_data: Dict[str, Any] = None) -> Optional[OptimizationRecommendation]:
        """バッチサイズの推奨事項を生成"""
        collection_size = characteristics.get("collection_size", 0)
        
        # パフォーマンスデータがある場合はそれを参考に
        if performance_data:
            # パフォーマンスデータから最適なバッチサイズを推定
            recommended_batch = self._analyze_optimal_batch_size(performance_data)
        else:
            # デフォルトの推奨値
            if collection_size < 1000:
                recommended_batch = self.batch_size_recommendations["memory_limited"]
            elif collection_size < 10000:
                recommended_batch = self.batch_size_recommendations["balanced"]
            else:
                recommended_batch = self.batch_size_recommendations["performance"]
        
        return OptimizationRecommendation(
            category="Batch Size",
            description="挿入・検索操作のバッチサイズ最適化",
            priority="Medium",
            expected_improvement="スループット20-40%向上",
            implementation_steps=[
                f"挿入バッチサイズを {recommended_batch['insert']} に設定",
                f"検索バッチサイズを {recommended_batch['search']} に設定",
                "メモリ使用量を監視しながら調整"
            ],
            estimated_effort="低（30分）"
        )

    def _recommend_metadata_optimization(self, characteristics: Dict[str, Any]) -> Optional[OptimizationRecommendation]:
        """メタデータの最適化推奨事項を生成"""
        metadata_keys = characteristics.get("sample_metadata_keys", [])
        complexity = characteristics.get("metadata_complexity", 0)
        
        if complexity > 10:
            return OptimizationRecommendation(
                category="Metadata",
                description="メタデータ構造の最適化",
                priority="Medium",
                expected_improvement="フィルタリング速度向上",
                implementation_steps=[
                    "頻繁に使用するフィルタキーを特定",
                    "不要なメタデータフィールドを削除",
                    "数値データは適切な型で保存",
                    "カテゴリデータは列挙型を使用"
                ],
                estimated_effort="中程度（2-3時間）"
            )
        
        return None

    def _recommend_collection_partitioning(self, characteristics: Dict[str, Any]) -> Optional[OptimizationRecommendation]:
        """コレクション分割の推奨事項を生成"""
        collection_size = characteristics.get("collection_size", 0)
        
        if collection_size > 50000:
            return OptimizationRecommendation(
                category="Collection Partitioning",
                description="大規模コレクションの分割",
                priority="High",
                expected_improvement="検索速度大幅向上、メモリ使用量削減",
                implementation_steps=[
                    "データの特性に基づく分割戦略を策定",
                    "機能別、カテゴリ別にコレクションを分割",
                    "分割されたコレクション間の検索ロジックを実装",
                    "段階的な移行計画を実行"
                ],
                estimated_effort="高（1-2日）"
            )
        
        return None

    def _recommend_memory_optimization(self, characteristics: Dict[str, Any]) -> Optional[OptimizationRecommendation]:
        """メモリ使用量の最適化推奨事項を生成"""
        embedding_dim = characteristics.get("embedding_dimension")
        collection_size = characteristics.get("collection_size", 0)
        
        # 推定メモリ使用量（MB）
        if embedding_dim:
            estimated_memory = (collection_size * embedding_dim * 4) / (1024 * 1024)  # float32前提
            
            if estimated_memory > 1024:  # 1GB以上
                return OptimizationRecommendation(
                    category="Memory",
                    description=f"メモリ使用量最適化（推定: {estimated_memory:.1f}MB）",
                    priority="Medium",
                    expected_improvement="メモリ使用量20-40%削減",
                    implementation_steps=[
                        "埋め込み次元数の見直し（PCAやtSNEで次元削減）",
                        "分散ストレージの検討",
                        "キャッシュ戦略の実装",
                        "不要なメタデータの削除"
                    ],
                    estimated_effort="高（3-5時間）"
                )
        
        return None

    def _analyze_optimal_batch_size(self, performance_data: Dict[str, Any]) -> Dict[str, int]:
        """パフォーマンスデータから最適なバッチサイズを分析"""
        # パフォーマンスデータの分析ロジック
        # 実際の実装では、スループットが最大になるバッチサイズを特定
        return self.batch_size_recommendations["balanced"]

    def create_optimized_collection_config(self, 
                                         collection_name: str,
                                         characteristics: Dict[str, Any] = None) -> Dict[str, Any]:
        """最適化されたコレクション設定を生成"""
        if characteristics is None:
            characteristics = self.analyze_collection_characteristics()
        
        size_category = characteristics.get("size_category", "medium")
        hnsw_params = self.hnsw_recommendations[size_category]
        embedding_dim = characteristics.get("embedding_dimension", 384)
        
        config = {
            "name": collection_name,
            "metadata": {
                "hnsw:space": "cosine",
                "hnsw:construction_ef": hnsw_params["construction_ef"],
                "hnsw:search_ef": hnsw_params["search_ef"],
                "hnsw:m": hnsw_params["m"],
                "dimension": embedding_dim
            },
            "description": f"最適化設定: {hnsw_params['description']}"
        }
        
        return config

    def apply_batch_optimization(self, 
                               insert_batch_size: int = None,
                               search_batch_size: int = None) -> Dict[str, Any]:
        """バッチ処理の最適化を適用"""
        characteristics = self.analyze_collection_characteristics()
        
        if insert_batch_size is None or search_batch_size is None:
            size_category = characteristics.get("size_category", "medium")
            if size_category == "small":
                default_config = self.batch_size_recommendations["memory_limited"]
            elif size_category == "medium":
                default_config = self.batch_size_recommendations["balanced"]
            else:
                default_config = self.batch_size_recommendations["performance"]
            
            insert_batch_size = insert_batch_size or default_config["insert"]
            search_batch_size = search_batch_size or default_config["search"]
        
        optimization_config = {
            "insert_batch_size": insert_batch_size,
            "search_batch_size": search_batch_size,
            "collection_size": characteristics.get("collection_size", 0),
            "optimization_timestamp": time.time()
        }
        
        self.optimization_history.append(optimization_config)
        
        return optimization_config

    def generate_optimization_report(self, 
                                   recommendations: List[OptimizationRecommendation] = None) -> str:
        """最適化レポートを生成"""
        if recommendations is None:
            recommendations = self.get_optimization_recommendations()
        
        report_lines = [
            "# ChromaDB 最適化レポート",
            "",
            f"生成日時: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        # コレクション情報
        characteristics = self.analyze_collection_characteristics()
        if "error" not in characteristics:
            report_lines.extend([
                "## コレクション情報",
                f"- コレクションサイズ: {characteristics.get('collection_size', 0):,} 項目",
                f"- サイズカテゴリ: {characteristics.get('size_category', '不明')}",
                f"- 埋め込み次元: {characteristics.get('embedding_dimension', '不明')}",
                f"- メタデータフィールド数: {characteristics.get('metadata_complexity', 0)}",
                ""
            ])
        
        # 推奨事項
        if recommendations:
            report_lines.extend([
                "## 最適化推奨事項",
                ""
            ])
            
            # 優先度順にソート
            priority_order = {"High": 1, "Medium": 2, "Low": 3}
            sorted_recommendations = sorted(
                recommendations, 
                key=lambda x: priority_order.get(x.priority, 4)
            )
            
            for i, rec in enumerate(sorted_recommendations, 1):
                report_lines.extend([
                    f"### {i}. {rec.category} 【{rec.priority}】",
                    f"**説明**: {rec.description}",
                    f"**期待される改善**: {rec.expected_improvement}",
                    f"**推定工数**: {rec.estimated_effort}",
                    "",
                    "**実装手順**:",
                ])
                
                for step in rec.implementation_steps:
                    report_lines.append(f"- {step}")
                
                report_lines.append("")
        
        # 最適化履歴
        if self.optimization_history:
            report_lines.extend([
                "## 最適化履歴",
                ""
            ])
            
            for i, config in enumerate(self.optimization_history, 1):
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S', 
                                        time.localtime(config.get('optimization_timestamp', 0)))
                report_lines.extend([
                    f"### 最適化 {i} ({timestamp})",
                    f"- 挿入バッチサイズ: {config.get('insert_batch_size', '不明')}",
                    f"- 検索バッチサイズ: {config.get('search_batch_size', '不明')}",
                    f"- 対象コレクションサイズ: {config.get('collection_size', '不明')}",
                    ""
                ])
        
        return "\n".join(report_lines)

    def export_optimization_config(self, output_path: str = None) -> str:
        """最適化設定をJSONファイルにエクスポート"""
        if output_path is None:
            timestamp = int(time.time())
            output_path = f"chromadb_optimization_config_{timestamp}.json"
        
        characteristics = self.analyze_collection_characteristics()
        recommendations = self.get_optimization_recommendations()
        
        config_data = {
            "timestamp": time.time(),
            "collection_characteristics": characteristics,
            "recommendations": [
                {
                    "category": rec.category,
                    "description": rec.description,
                    "priority": rec.priority,
                    "expected_improvement": rec.expected_improvement,
                    "implementation_steps": rec.implementation_steps,
                    "estimated_effort": rec.estimated_effort
                }
                for rec in recommendations
            ],
            "optimization_history": self.optimization_history,
            "optimized_collection_config": self.create_optimized_collection_config("optimized_collection", characteristics)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        print(f"最適化設定を {output_path} に保存しました")
        return output_path


# 使用例のデモ関数
def demo_optimizer():
    """最適化機能のデモ"""
    print("ChromaDB最適化機能のデモ")
    print("注意: 実際の最適化には ChromaDB コレクションが必要です")
    
    # モックコレクション（デモ用）
    class MockCollection:
        def __init__(self, size=5000):
            self.name = "demo_collection"
            self._size = size
        
        def count(self):
            return self._size
        
        def peek(self, limit=10):
            return {
                'ids': [f'id_{i}' for i in range(limit)],
                'embeddings': [[0.1] * 384 for _ in range(limit)],
                'metadatas': [
                    {
                        'function_name': f'func_{i}',
                        'complexity': 'O(n)',
                        'category': 'util',
                        'score': 0.8
                    } for i in range(limit)
                ]
            }
    
    # デモ実行
    mock_collection = MockCollection()
    optimizer = ChromaDBOptimizer(mock_collection)
    
    print("\n1. コレクション特性分析")
    characteristics = optimizer.analyze_collection_characteristics()
    print(f"コレクションサイズ: {characteristics.get('collection_size', 0)}")
    print(f"カテゴリ: {characteristics.get('size_category', '不明')}")
    
    print("\n2. 最適化推奨事項生成")
    recommendations = optimizer.get_optimization_recommendations()
    print(f"推奨事項数: {len(recommendations)}")
    
    for rec in recommendations[:2]:  # 最初の2つを表示
        print(f"- {rec.category}: {rec.description}")
    
    print("\n3. 最適化レポート生成")
    report = optimizer.generate_optimization_report(recommendations)
    print("レポートが生成されました（詳細は実際の実行時に表示）")
    
    print("\n4. 設定エクスポート")
    config_path = optimizer.export_optimization_config()
    print(f"設定ファイル: {config_path}")


if __name__ == "__main__":
    demo_optimizer()