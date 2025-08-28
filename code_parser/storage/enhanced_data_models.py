"""
Enhanced Data Models for RAG-Optimized Code Parser

このモジュールは、RAG（Retrieval-Augmented Generation）システムに最適化された
拡張データモデルを提供します。従来の構文解析に加えて、意味的な関係、
機能的な類似性、使用例、エラーハンドリング情報等をサポートします。
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
import json
from datetime import datetime


class EnhancedNodeType(Enum):
    """拡張ノードタイプ - RAG生成に必要な意味的情報を含む"""
    
    # 既存のノードタイプ（基本構文要素）
    MODULE = "Module"
    CLASS = "Class"
    FUNCTION = "Function"
    VARIABLE = "Variable"
    PARAMETER = "Parameter"
    IMPORT = "Import"
    COMMENT = "Comment"
    CALL = "Call"
    ASSIGNMENT = "Assignment"
    ATTRIBUTE = "Attribute"
    STRING = "String"
    NUMBER = "Number"
    BOOLEAN = "Boolean"
    OPERATOR = "Operator"
    DECORATOR = "Decorator"
    ANNOTATION = "Annotation"
    EXCEPTION = "Exception"
    LOOP = "Loop"
    CONDITION = "Condition"
    
    # 新規追加 - RAG特化ノードタイプ
    FUNCTION_DOC = "FunctionDoc"          # 関数の詳細ドキュメント
    USAGE_EXAMPLE = "UsageExample"        # 使用例・サンプルコード
    ERROR_HANDLING = "ErrorHandling"      # エラーハンドリング情報
    PERFORMANCE_INFO = "PerformanceInfo"  # パフォーマンス特性情報
    INPUT_OUTPUT = "InputOutput"          # 入出力仕様
    DEPENDENCY = "Dependency"             # 依存関係情報
    ALTERNATIVE = "Alternative"           # 代替実装・代替手法
    TEST_CASE = "TestCase"                # テストケース
    DOCUMENTATION = "Documentation"       # 一般的なドキュメント
    CONFIGURATION = "Configuration"       # 設定・構成情報
    SECURITY_INFO = "SecurityInfo"        # セキュリティ関連情報
    VERSION_INFO = "VersionInfo"          # バージョン・互換性情報
    API_SPEC = "ApiSpec"                  # API仕様
    BEST_PRACTICE = "BestPractice"        # ベストプラクティス
    WARNING = "Warning"                   # 警告・注意事項
    FAQ = "FAQ"                          # よくある質問と回答


class EnhancedRelationType(Enum):
    """拡張リレーションタイプ - 意味的・機能的関係を表現"""
    
    # 既存のリレーションタイプ（構文的関係）
    CONTAINS = "CONTAINS"
    CALLS = "CALLS"
    USES = "USES"
    IMPORTS = "IMPORTS"
    HAS_PARAMETER = "HAS_PARAMETER"
    RETURNS = "RETURNS"
    ASSIGNS = "ASSIGNS"
    HAS_ATTRIBUTE = "HAS_ATTRIBUTE"
    REFERENCES = "REFERENCES"
    DECLARES = "DECLARES"
    INHERITS = "INHERITS"
    IMPLEMENTS = "IMPLEMENTS"
    DECORATES = "DECORATES"
    THROWS = "THROWS"
    HANDLES = "HANDLES"
    ITERATES = "ITERATES"
    CONDITIONAL = "CONDITIONAL"
    
    # 新規追加 - 意味的・機能的関係
    SIMILAR_FUNCTION = "SIMILAR_FUNCTION"     # 類似機能・類似処理
    COMPATIBLE_INPUT = "COMPATIBLE_INPUT"     # 入力互換性
    COMPATIBLE_OUTPUT = "COMPATIBLE_OUTPUT"   # 出力互換性
    USES_PATTERN = "USES_PATTERN"            # 使用パターン・実装パターン
    ERROR_RELATED = "ERROR_RELATED"          # エラー関連（エラー原因、対処法等）
    PERFORMANCE_RELATED = "PERFORMANCE_RELATED"  # パフォーマンス関連
    ALTERNATIVE_TO = "ALTERNATIVE_TO"        # 代替関係
    TESTED_BY = "TESTED_BY"                  # テスト対象関係
    DOCUMENTS = "DOCUMENTS"                  # ドキュメント対象関係
    DEPENDS_ON = "DEPENDS_ON"                # 依存関係
    EXTENDS = "EXTENDS"                      # 拡張関係
    MIGRATES_TO = "MIGRATES_TO"              # 移行先関係
    SECURITY_RELATED = "SECURITY_RELATED"    # セキュリティ関連
    REPLACES = "REPLACES"                    # 置換関係
    VALIDATES = "VALIDATES"                  # 検証関係
    OPTIMIZES = "OPTIMIZES"                  # 最適化関係
    CONFIGURES = "CONFIGURES"                # 設定関係
    REQUIRES = "REQUIRES"                    # 必要条件関係
    PROVIDES = "PROVIDES"                    # 提供関係
    TRANSFORMS = "TRANSFORMS"                # 変換関係


@dataclass
class FunctionAnalysis:
    """関数の詳細分析結果"""
    purpose: str                           # 関数の目的・役割
    input_spec: Dict[str, Any]            # 入力仕様（型、制約、説明等）
    output_spec: Dict[str, Any]           # 出力仕様（型、説明、条件等）
    usage_examples: List[str]             # 使用例コード
    error_handling: List[str]             # エラーハンドリング情報
    performance: Dict[str, Any]           # パフォーマンス特性
    limitations: List[str]                # 制限事項・注意点
    alternatives: List[str]               # 代替案・代替関数
    related_functions: List[str]          # 関連関数
    security_considerations: List[str]    # セキュリティ上の考慮事項
    test_cases: List[str]                 # テストケースの提案
    complexity_metrics: Dict[str, Any]    # 複雑性メトリクス
    dependencies: List[str]               # 依存関係
    version_compatibility: Dict[str, Any] # バージョン互換性情報
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'purpose': self.purpose,
            'input_spec': self.input_spec,
            'output_spec': self.output_spec,
            'usage_examples': self.usage_examples,
            'error_handling': self.error_handling,
            'performance': self.performance,
            'limitations': self.limitations,
            'alternatives': self.alternatives,
            'related_functions': self.related_functions,
            'security_considerations': self.security_considerations,
            'test_cases': self.test_cases,
            'complexity_metrics': self.complexity_metrics,
            'dependencies': self.dependencies,
            'version_compatibility': self.version_compatibility
        }


@dataclass
class ClassAnalysis:
    """クラスの詳細分析結果"""
    purpose: str                          # クラスの目的・責任範囲
    design_pattern: str                   # 設計パターン
    inheritance: List[str]                # 継承関係
    methods: List[Dict[str, Any]]         # メソッド一覧と詳細
    instance_variables: List[Dict[str, Any]]  # インスタンス変数
    usage_scenarios: List[str]            # 使用場面・シナリオ
    performance: Dict[str, Any]           # パフォーマンス特性
    thread_safety: str                    # スレッドセーフティ
    security_considerations: List[str]    # セキュリティ上の考慮事項
    test_strategy: str                    # テスト戦略
    instantiation_patterns: List[str]     # インスタンス化パターン
    lifecycle_info: Dict[str, Any]        # ライフサイクル情報
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'purpose': self.purpose,
            'design_pattern': self.design_pattern,
            'inheritance': self.inheritance,
            'methods': self.methods,
            'instance_variables': self.instance_variables,
            'usage_scenarios': self.usage_scenarios,
            'performance': self.performance,
            'thread_safety': self.thread_safety,
            'security_considerations': self.security_considerations,
            'test_strategy': self.test_strategy,
            'instantiation_patterns': self.instantiation_patterns,
            'lifecycle_info': self.lifecycle_info
        }


@dataclass
class ErrorAnalysis:
    """エラーハンドリングの詳細分析結果"""
    exceptions: List[Dict[str, Any]]      # 例外の種類と詳細
    causes: List[str]                     # 発生原因
    solutions: List[Dict[str, Any]]       # 解決方法とコード例
    prevention: List[str]                 # 予防策
    logging_recommendations: List[str]    # ログ出力の推奨事項
    user_messages: List[str]              # ユーザーへのエラーメッセージ
    recovery_strategies: List[str]        # 回復戦略
    monitoring_points: List[str]          # 監視ポイント
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'exceptions': self.exceptions,
            'causes': self.causes,
            'solutions': self.solutions,
            'prevention': self.prevention,
            'logging_recommendations': self.logging_recommendations,
            'user_messages': self.user_messages,
            'recovery_strategies': self.recovery_strategies,
            'monitoring_points': self.monitoring_points
        }


@dataclass
class PerformanceInfo:
    """パフォーマンス情報"""
    time_complexity: str                  # 時間計算量
    space_complexity: str                 # 空間計算量
    bottlenecks: List[str]               # ボトルネック
    optimization_suggestions: List[str]  # 最適化提案
    benchmark_data: Dict[str, Any]       # ベンチマークデータ
    scaling_characteristics: str         # スケーリング特性
    memory_usage_pattern: str            # メモリ使用パターン
    cpu_usage_pattern: str               # CPU使用パターン
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'time_complexity': self.time_complexity,
            'space_complexity': self.space_complexity,
            'bottlenecks': self.bottlenecks,
            'optimization_suggestions': self.optimization_suggestions,
            'benchmark_data': self.benchmark_data,
            'scaling_characteristics': self.scaling_characteristics,
            'memory_usage_pattern': self.memory_usage_pattern,
            'cpu_usage_pattern': self.cpu_usage_pattern
        }


@dataclass
class EnhancedSyntaxNode:
    """拡張構文ノード - RAG最適化済み"""
    node_id: str
    node_type: Union[EnhancedNodeType, str]  # 後方互換性のためUnion
    name: str
    text: str
    start_byte: int
    end_byte: int
    line_start: int
    line_end: int
    properties: Dict[str, Any]
    parent_id: Optional[str] = None
    complexity_score: float = 0.0
    
    # RAG特化フィールド
    function_analysis: Optional[FunctionAnalysis] = None
    class_analysis: Optional[ClassAnalysis] = None
    error_analysis: Optional[ErrorAnalysis] = None
    performance_info: Optional[PerformanceInfo] = None
    
    # メタデータ
    embeddings: Optional[List[float]] = None          # ベクトル埋め込み
    semantic_tags: List[str] = field(default_factory=list)  # 意味的タグ
    quality_score: float = 0.0                       # 品質スコア
    usage_frequency: int = 0                         # 使用頻度
    last_updated: Optional[datetime] = None          # 最終更新日時
    source_confidence: float = 1.0                   # ソース信頼度
    
    # LLM分析結果（拡張）
    llm_insights: Optional[Dict[str, Any]] = None
    llm_confidence: float = 0.0                      # LLM分析の信頼度
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換（Neo4j保存用）"""
        result = {
            'node_id': self.node_id,
            'node_type': self.node_type.value if isinstance(self.node_type, EnhancedNodeType) else self.node_type,
            'name': self.name,
            'text': self.text,
            'start_byte': self.start_byte,
            'end_byte': self.end_byte,
            'line_start': self.line_start,
            'line_end': self.line_end,
            'properties': json.dumps(self.properties) if self.properties else '{}',
            'parent_id': self.parent_id,
            'complexity_score': self.complexity_score,
            'semantic_tags': json.dumps(self.semantic_tags),
            'quality_score': self.quality_score,
            'usage_frequency': self.usage_frequency,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'source_confidence': self.source_confidence,
            'llm_confidence': self.llm_confidence
        }
        
        # 分析結果の追加
        if self.function_analysis:
            result['function_analysis'] = json.dumps(self.function_analysis.to_dict())
        if self.class_analysis:
            result['class_analysis'] = json.dumps(self.class_analysis.to_dict())
        if self.error_analysis:
            result['error_analysis'] = json.dumps(self.error_analysis.to_dict())
        if self.performance_info:
            result['performance_info'] = json.dumps(self.performance_info.to_dict())
        if self.llm_insights:
            result['llm_insights'] = json.dumps(self.llm_insights)
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedSyntaxNode':
        """辞書から復元"""
        # JSON文字列のパース
        properties = json.loads(data.get('properties', '{}'))
        semantic_tags = json.loads(data.get('semantic_tags', '[]'))
        
        # 分析結果の復元
        function_analysis = None
        if data.get('function_analysis'):
            fa_data = json.loads(data['function_analysis'])
            function_analysis = FunctionAnalysis(**fa_data)
        
        class_analysis = None
        if data.get('class_analysis'):
            ca_data = json.loads(data['class_analysis'])
            class_analysis = ClassAnalysis(**ca_data)
        
        error_analysis = None
        if data.get('error_analysis'):
            ea_data = json.loads(data['error_analysis'])
            error_analysis = ErrorAnalysis(**ea_data)
        
        performance_info = None
        if data.get('performance_info'):
            pi_data = json.loads(data['performance_info'])
            performance_info = PerformanceInfo(**pi_data)
        
        llm_insights = None
        if data.get('llm_insights'):
            llm_insights = json.loads(data['llm_insights'])
        
        # 日時の復元
        last_updated = None
        if data.get('last_updated'):
            last_updated = datetime.fromisoformat(data['last_updated'])
        
        return cls(
            node_id=data['node_id'],
            node_type=EnhancedNodeType(data['node_type']),
            name=data['name'],
            text=data['text'],
            start_byte=data['start_byte'],
            end_byte=data['end_byte'],
            line_start=data['line_start'],
            line_end=data['line_end'],
            properties=properties,
            parent_id=data.get('parent_id'),
            complexity_score=data.get('complexity_score', 0.0),
            function_analysis=function_analysis,
            class_analysis=class_analysis,
            error_analysis=error_analysis,
            performance_info=performance_info,
            semantic_tags=semantic_tags,
            quality_score=data.get('quality_score', 0.0),
            usage_frequency=data.get('usage_frequency', 0),
            last_updated=last_updated,
            source_confidence=data.get('source_confidence', 1.0),
            llm_insights=llm_insights,
            llm_confidence=data.get('llm_confidence', 0.0)
        )


@dataclass
class EnhancedSyntaxRelation:
    """拡張構文関係 - 意味的関係を含む"""
    source_id: str
    target_id: str
    relation_type: Union[EnhancedRelationType, str]  # 後方互換性のためUnion
    properties: Dict[str, Any] = field(default_factory=dict)
    
    # RAG特化フィールド
    confidence_score: float = 1.0           # 関係の信頼度
    semantic_similarity: float = 0.0        # 意味的類似度
    functional_similarity: float = 0.0      # 機能的類似度
    usage_frequency: int = 0                # 関係の使用頻度
    context_relevance: float = 0.0          # 文脈関連性
    
    # メタデータ
    discovery_method: str = "static_analysis"  # 発見方法（static_analysis, llm, manual等）
    last_verified: Optional[datetime] = None   # 最終検証日時
    quality_score: float = 0.0                 # 関係の品質スコア
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'relation_type': self.relation_type.value if isinstance(self.relation_type, EnhancedRelationType) else self.relation_type,
            'properties': json.dumps(self.properties) if self.properties else '{}',
            'confidence_score': self.confidence_score,
            'semantic_similarity': self.semantic_similarity,
            'functional_similarity': self.functional_similarity,
            'usage_frequency': self.usage_frequency,
            'context_relevance': self.context_relevance,
            'discovery_method': self.discovery_method,
            'last_verified': self.last_verified.isoformat() if self.last_verified else None,
            'quality_score': self.quality_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedSyntaxRelation':
        """辞書から復元"""
        properties = json.loads(data.get('properties', '{}'))
        
        last_verified = None
        if data.get('last_verified'):
            last_verified = datetime.fromisoformat(data['last_verified'])
        
        return cls(
            source_id=data['source_id'],
            target_id=data['target_id'],
            relation_type=EnhancedRelationType(data['relation_type']),
            properties=properties,
            confidence_score=data.get('confidence_score', 1.0),
            semantic_similarity=data.get('semantic_similarity', 0.0),
            functional_similarity=data.get('functional_similarity', 0.0),
            usage_frequency=data.get('usage_frequency', 0),
            context_relevance=data.get('context_relevance', 0.0),
            discovery_method=data.get('discovery_method', 'static_analysis'),
            last_verified=last_verified,
            quality_score=data.get('quality_score', 0.0)
        )


# 便利な定数とヘルパー関数
RAG_OPTIMIZED_NODE_TYPES = [
    EnhancedNodeType.FUNCTION_DOC,
    EnhancedNodeType.USAGE_EXAMPLE,
    EnhancedNodeType.ERROR_HANDLING,
    EnhancedNodeType.PERFORMANCE_INFO,
    EnhancedNodeType.INPUT_OUTPUT,
    EnhancedNodeType.ALTERNATIVE,
    EnhancedNodeType.TEST_CASE,
    EnhancedNodeType.BEST_PRACTICE
]

SEMANTIC_RELATION_TYPES = [
    EnhancedRelationType.SIMILAR_FUNCTION,
    EnhancedRelationType.COMPATIBLE_INPUT,
    EnhancedRelationType.COMPATIBLE_OUTPUT,
    EnhancedRelationType.ALTERNATIVE_TO,
    EnhancedRelationType.PERFORMANCE_RELATED,
    EnhancedRelationType.ERROR_RELATED
]


def create_enhanced_node(
    node_id: str,
    node_type: EnhancedNodeType,
    name: str,
    text: str,
    **kwargs
) -> EnhancedSyntaxNode:
    """拡張構文ノードの便利な作成関数"""
    return EnhancedSyntaxNode(
        node_id=node_id,
        node_type=node_type,
        name=name,
        text=text,
        start_byte=kwargs.get('start_byte', 0),
        end_byte=kwargs.get('end_byte', 0),
        line_start=kwargs.get('line_start', 0),
        line_end=kwargs.get('line_end', 0),
        properties=kwargs.get('properties', {}),
        **{k: v for k, v in kwargs.items() if k not in ['start_byte', 'end_byte', 'line_start', 'line_end', 'properties']}
    )


def create_enhanced_relation(
    source_id: str,
    target_id: str,
    relation_type: EnhancedRelationType,
    **kwargs
) -> EnhancedSyntaxRelation:
    """拡張構文関係の便利な作成関数"""
    return EnhancedSyntaxRelation(
        source_id=source_id,
        target_id=target_id,
        relation_type=relation_type,
        **kwargs
    )