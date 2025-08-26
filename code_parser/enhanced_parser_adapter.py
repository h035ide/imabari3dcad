"""
Enhanced Parser Adapter

既存のtreesitter_neo4j_advanced.pyを拡張データモデルに対応させるための
アダプター機能を提供します。
"""

from typing import Dict, List, Any, Optional, Union
import json
import logging
from datetime import datetime

from .enhanced_data_models import (
    EnhancedNodeType, EnhancedRelationType,
    EnhancedSyntaxNode, EnhancedSyntaxRelation,
    FunctionAnalysis, ClassAnalysis, ErrorAnalysis, PerformanceInfo,
    create_enhanced_node, create_enhanced_relation
)

# 既存のモジュールからインポート（相対インポート）
try:
    from .treesitter_neo4j_advanced import (
        NodeType, RelationType, SyntaxNode, SyntaxRelation,
        TreeSitterNeo4jAnalyzer
    )
except ImportError:
    # フォールバック：直接インポート
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from treesitter_neo4j_advanced import (
        NodeType, RelationType, SyntaxNode, SyntaxRelation,
        TreeSitterNeo4jAnalyzer
    )

logger = logging.getLogger(__name__)


class EnhancedParserAdapter:
    """既存パーサーを拡張データモデルに適応させるアダプター"""
    
    def __init__(self, base_analyzer: TreeSitterNeo4jAnalyzer = None):
        """アダプターの初期化"""
        self.base_analyzer = base_analyzer
        self.node_type_mapping = self._create_node_type_mapping()
        self.relation_type_mapping = self._create_relation_type_mapping()
        
    def _create_node_type_mapping(self) -> Dict[NodeType, EnhancedNodeType]:
        """既存ノードタイプから拡張ノードタイプへのマッピング"""
        return {
            NodeType.MODULE: EnhancedNodeType.MODULE,
            NodeType.CLASS: EnhancedNodeType.CLASS,
            NodeType.FUNCTION: EnhancedNodeType.FUNCTION,
            NodeType.VARIABLE: EnhancedNodeType.VARIABLE,
            NodeType.PARAMETER: EnhancedNodeType.PARAMETER,
            NodeType.IMPORT: EnhancedNodeType.IMPORT,
            NodeType.COMMENT: EnhancedNodeType.COMMENT,
            NodeType.CALL: EnhancedNodeType.CALL,
            NodeType.ASSIGNMENT: EnhancedNodeType.ASSIGNMENT,
            NodeType.ATTRIBUTE: EnhancedNodeType.ATTRIBUTE,
            NodeType.STRING: EnhancedNodeType.STRING,
            NodeType.NUMBER: EnhancedNodeType.NUMBER,
            NodeType.BOOLEAN: EnhancedNodeType.BOOLEAN,
            NodeType.OPERATOR: EnhancedNodeType.OPERATOR,
            NodeType.DECORATOR: EnhancedNodeType.DECORATOR,
            NodeType.ANNOTATION: EnhancedNodeType.ANNOTATION,
            NodeType.EXCEPTION: EnhancedNodeType.EXCEPTION,
            NodeType.LOOP: EnhancedNodeType.LOOP,
            NodeType.CONDITION: EnhancedNodeType.CONDITION
        }
    
    def _create_relation_type_mapping(self) -> Dict[RelationType, EnhancedRelationType]:
        """既存リレーションタイプから拡張リレーションタイプへのマッピング"""
        return {
            RelationType.CONTAINS: EnhancedRelationType.CONTAINS,
            RelationType.CALLS: EnhancedRelationType.CALLS,
            RelationType.USES: EnhancedRelationType.USES,
            RelationType.IMPORTS: EnhancedRelationType.IMPORTS,
            RelationType.HAS_PARAMETER: EnhancedRelationType.HAS_PARAMETER,
            RelationType.RETURNS: EnhancedRelationType.RETURNS,
            RelationType.ASSIGNS: EnhancedRelationType.ASSIGNS,
            RelationType.HAS_ATTRIBUTE: EnhancedRelationType.HAS_ATTRIBUTE,
            RelationType.REFERENCES: EnhancedRelationType.REFERENCES,
            RelationType.DECLARES: EnhancedRelationType.DECLARES,
            RelationType.INHERITS: EnhancedRelationType.INHERITS,
            RelationType.IMPLEMENTS: EnhancedRelationType.IMPLEMENTS,
            RelationType.DECORATES: EnhancedRelationType.DECORATES,
            RelationType.THROWS: EnhancedRelationType.THROWS,
            RelationType.HANDLES: EnhancedRelationType.HANDLES,
            RelationType.ITERATES: EnhancedRelationType.ITERATES,
            RelationType.CONDITIONAL: EnhancedRelationType.CONDITIONAL
        }
    
    def convert_syntax_node(self, legacy_node: SyntaxNode) -> EnhancedSyntaxNode:
        """既存のSyntaxNodeを拡張版に変換"""
        # ノードタイプの変換
        enhanced_node_type = self.node_type_mapping.get(
            legacy_node.node_type, 
            EnhancedNodeType.MODULE  # デフォルト値
        )
        
        # 基本的な拡張ノードの作成
        enhanced_node = EnhancedSyntaxNode(
            node_id=legacy_node.node_id,
            node_type=enhanced_node_type,
            name=legacy_node.name,
            text=legacy_node.text,
            start_byte=legacy_node.start_byte,
            end_byte=legacy_node.end_byte,
            line_start=legacy_node.line_start,
            line_end=legacy_node.line_end,
            properties=legacy_node.properties,
            parent_id=legacy_node.parent_id,
            complexity_score=legacy_node.complexity_score,
            llm_insights=legacy_node.llm_insights,
            last_updated=datetime.now(),
            source_confidence=1.0
        )
        
        # ノードタイプ別の追加処理
        if enhanced_node_type == EnhancedNodeType.FUNCTION:
            enhanced_node.function_analysis = self._extract_function_analysis(legacy_node)
        elif enhanced_node_type == EnhancedNodeType.CLASS:
            enhanced_node.class_analysis = self._extract_class_analysis(legacy_node)
        
        return enhanced_node
    
    def convert_syntax_relation(self, legacy_relation: SyntaxRelation) -> EnhancedSyntaxRelation:
        """既存のSyntaxRelationを拡張版に変換"""
        # リレーションタイプの変換
        enhanced_relation_type = self.relation_type_mapping.get(
            legacy_relation.relation_type,
            EnhancedRelationType.USES  # デフォルト値
        )
        
        return EnhancedSyntaxRelation(
            source_id=legacy_relation.source_id,
            target_id=legacy_relation.target_id,
            relation_type=enhanced_relation_type,
            properties=legacy_relation.properties,
            confidence_score=1.0,  # 既存データは高信頼度
            discovery_method="static_analysis",
            last_verified=datetime.now(),
            quality_score=0.8  # 既存データの品質スコア
        )
    
    def _extract_function_analysis(self, node: SyntaxNode) -> Optional[FunctionAnalysis]:
        """関数ノードから分析情報を抽出"""
        try:
            # LLM分析結果がある場合は活用
            if node.llm_insights:
                return FunctionAnalysis(
                    purpose=node.llm_insights.get('purpose', '分析中'),
                    input_spec=node.llm_insights.get('input_spec', {}),
                    output_spec=node.llm_insights.get('output_spec', {}),
                    usage_examples=node.llm_insights.get('usage_examples', []),
                    error_handling=node.llm_insights.get('error_handling', []),
                    performance=node.llm_insights.get('performance', {}),
                    limitations=node.llm_insights.get('limitations', []),
                    alternatives=[],
                    related_functions=[],
                    security_considerations=[],
                    test_cases=[],
                    complexity_metrics={'score': node.complexity_score},
                    dependencies=[],
                    version_compatibility={}
                )
            
            # 基本的な分析情報を生成
            return FunctionAnalysis(
                purpose=f"関数 {node.name} の処理",
                input_spec=self._analyze_function_parameters(node),
                output_spec={'type': 'unknown', 'description': '戻り値の分析が必要'},
                usage_examples=[],
                error_handling=[],
                performance={'complexity_score': node.complexity_score},
                limitations=[],
                alternatives=[],
                related_functions=[],
                security_considerations=[],
                test_cases=[],
                complexity_metrics={'score': node.complexity_score},
                dependencies=[],
                version_compatibility={}
            )
        except Exception as e:
            logger.warning(f"関数分析抽出エラー: {str(e)}")
            return None
    
    def _extract_class_analysis(self, node: SyntaxNode) -> Optional[ClassAnalysis]:
        """クラスノードから分析情報を抽出"""
        try:
            return ClassAnalysis(
                purpose=f"クラス {node.name} の定義",
                design_pattern="Unknown",
                inheritance=[],
                methods=[],
                instance_variables=[],
                usage_scenarios=[],
                performance={},
                thread_safety="Unknown",
                security_considerations=[],
                test_strategy="Unknown",
                instantiation_patterns=[],
                lifecycle_info={}
            )
        except Exception as e:
            logger.warning(f"クラス分析抽出エラー: {str(e)}")
            return None
    
    def _analyze_function_parameters(self, node: SyntaxNode) -> Dict[str, Any]:
        """関数のパラメータを分析"""
        # ノードのプロパティから引数情報を抽出
        parameters = {}
        if 'parameters' in node.properties:
            for param in node.properties['parameters']:
                parameters[param] = {
                    'type': 'unknown',
                    'required': True,
                    'description': f'パラメータ {param}'
                }
        
        return parameters
    
    def enhance_existing_data(self, nodes: List[SyntaxNode], relations: List[SyntaxRelation]) -> tuple[List[EnhancedSyntaxNode], List[EnhancedSyntaxRelation]]:
        """既存データを一括で拡張"""
        enhanced_nodes = []
        enhanced_relations = []
        
        # ノードの変換
        for node in nodes:
            try:
                enhanced_node = self.convert_syntax_node(node)
                enhanced_nodes.append(enhanced_node)
            except Exception as e:
                logger.error(f"ノード変換エラー {node.node_id}: {str(e)}")
        
        # リレーションの変換
        for relation in relations:
            try:
                enhanced_relation = self.convert_syntax_relation(relation)
                enhanced_relations.append(enhanced_relation)
            except Exception as e:
                logger.error(f"リレーション変換エラー {relation.source_id}->{relation.target_id}: {str(e)}")
        
        return enhanced_nodes, enhanced_relations
    
    def create_enhanced_documentation_nodes(self, function_nodes: List[EnhancedSyntaxNode]) -> List[EnhancedSyntaxNode]:
        """関数ノードから関連ドキュメントノードを生成"""
        doc_nodes = []
        
        for func_node in function_nodes:
            if func_node.node_type != EnhancedNodeType.FUNCTION:
                continue
            
            # 関数ドキュメントノード
            if func_node.function_analysis and func_node.function_analysis.purpose:
                doc_node = create_enhanced_node(
                    node_id=f"{func_node.node_id}_doc",
                    node_type=EnhancedNodeType.FUNCTION_DOC,
                    name=f"{func_node.name}_documentation",
                    text=func_node.function_analysis.purpose,
                    properties={
                        'parent_function': func_node.node_id,
                        'content_type': 'purpose_description'
                    },
                    quality_score=0.7,
                    semantic_tags=['documentation', 'function_purpose']
                )
                doc_nodes.append(doc_node)
            
            # 使用例ノード
            if func_node.function_analysis and func_node.function_analysis.usage_examples:
                for i, example in enumerate(func_node.function_analysis.usage_examples):
                    example_node = create_enhanced_node(
                        node_id=f"{func_node.node_id}_example_{i}",
                        node_type=EnhancedNodeType.USAGE_EXAMPLE,
                        name=f"{func_node.name}_example_{i}",
                        text=example,
                        properties={
                            'parent_function': func_node.node_id,
                            'example_index': i
                        },
                        quality_score=0.8,
                        semantic_tags=['example', 'usage_pattern']
                    )
                    doc_nodes.append(example_node)
        
        return doc_nodes
    
    def create_enhanced_relations(self, enhanced_nodes: List[EnhancedSyntaxNode]) -> List[EnhancedSyntaxRelation]:
        """拡張ノード間の意味的関係を生成"""
        enhanced_relations = []
        
        # 関数とそのドキュメントの関係
        for node in enhanced_nodes:
            if node.node_type == EnhancedNodeType.FUNCTION_DOC:
                parent_function_id = node.properties.get('parent_function')
                if parent_function_id:
                    relation = create_enhanced_relation(
                        source_id=parent_function_id,
                        target_id=node.node_id,
                        relation_type=EnhancedRelationType.DOCUMENTS,
                        confidence_score=1.0,
                        discovery_method="generated",
                        quality_score=0.9
                    )
                    enhanced_relations.append(relation)
            
            elif node.node_type == EnhancedNodeType.USAGE_EXAMPLE:
                parent_function_id = node.properties.get('parent_function')
                if parent_function_id:
                    relation = create_enhanced_relation(
                        source_id=parent_function_id,
                        target_id=node.node_id,
                        relation_type=EnhancedRelationType.USES_PATTERN,
                        confidence_score=0.9,
                        discovery_method="generated",
                        quality_score=0.8
                    )
                    enhanced_relations.append(relation)
        
        return enhanced_relations
    
    def generate_similarity_relations(self, function_nodes: List[EnhancedSyntaxNode], similarity_threshold: float = 0.7) -> List[EnhancedSyntaxRelation]:
        """関数間の類似性関係を生成"""
        similarity_relations = []
        
        # 簡単な名前ベースの類似性判定（後でより高度な手法に置き換え可能）
        for i, node1 in enumerate(function_nodes):
            if node1.node_type != EnhancedNodeType.FUNCTION:
                continue
                
            for j, node2 in enumerate(function_nodes[i+1:], i+1):
                if node2.node_type != EnhancedNodeType.FUNCTION:
                    continue
                
                # 名前の類似性を簡単に計算
                similarity = self._calculate_name_similarity(node1.name, node2.name)
                
                if similarity >= similarity_threshold:
                    relation = create_enhanced_relation(
                        source_id=node1.node_id,
                        target_id=node2.node_id,
                        relation_type=EnhancedRelationType.SIMILAR_FUNCTION,
                        semantic_similarity=similarity,
                        functional_similarity=similarity * 0.8,  # 保守的な見積もり
                        confidence_score=0.6,
                        discovery_method="name_similarity",
                        quality_score=0.5
                    )
                    similarity_relations.append(relation)
        
        return similarity_relations
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """関数名の類似性を計算（簡易版）"""
        if name1 == name2:
            return 1.0
        
        # 共通部分文字列の長さベースの類似性
        common_length = 0
        min_length = min(len(name1), len(name2))
        
        for i in range(min_length):
            if name1[i] == name2[i]:
                common_length += 1
            else:
                break
        
        # 逆順でも確認
        reverse_common = 0
        for i in range(1, min_length + 1):
            if name1[-i] == name2[-i]:
                reverse_common += 1
            else:
                break
        
        total_common = max(common_length, reverse_common)
        similarity = total_common / max(len(name1), len(name2))
        
        return similarity


def migrate_existing_analysis_to_enhanced(
    legacy_analyzer: TreeSitterNeo4jAnalyzer,
    enhanced_adapter: EnhancedParserAdapter = None
) -> Dict[str, Any]:
    """既存の分析結果を拡張データモデルに移行"""
    
    if enhanced_adapter is None:
        enhanced_adapter = EnhancedParserAdapter(legacy_analyzer)
    
    migration_results = {
        "timestamp": datetime.now().isoformat(),
        "legacy_nodes_count": 0,
        "legacy_relations_count": 0,
        "enhanced_nodes_count": 0,
        "enhanced_relations_count": 0,
        "errors": []
    }
    
    try:
        # 既存データの取得（実装は既存のAnalyzerに依存）
        # ここでは概念的な実装を示す
        legacy_nodes = []  # legacy_analyzer.get_all_nodes()
        legacy_relations = []  # legacy_analyzer.get_all_relations()
        
        migration_results["legacy_nodes_count"] = len(legacy_nodes)
        migration_results["legacy_relations_count"] = len(legacy_relations)
        
        # 拡張データモデルへの変換
        enhanced_nodes, enhanced_relations = enhanced_adapter.enhance_existing_data(
            legacy_nodes, legacy_relations
        )
        
        # 追加のドキュメントノードの生成
        doc_nodes = enhanced_adapter.create_enhanced_documentation_nodes(enhanced_nodes)
        enhanced_nodes.extend(doc_nodes)
        
        # 意味的関係の生成
        semantic_relations = enhanced_adapter.create_enhanced_relations(enhanced_nodes)
        enhanced_relations.extend(semantic_relations)
        
        # 類似性関係の生成
        similarity_relations = enhanced_adapter.generate_similarity_relations(enhanced_nodes)
        enhanced_relations.extend(similarity_relations)
        
        migration_results["enhanced_nodes_count"] = len(enhanced_nodes)
        migration_results["enhanced_relations_count"] = len(enhanced_relations)
        
        return migration_results
        
    except Exception as e:
        migration_results["errors"].append(str(e))
        logger.error(f"移行エラー: {str(e)}")
        return migration_results