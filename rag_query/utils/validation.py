"""
バリデーションユーティリティ

データの妥当性チェック機能を提供します。
"""

from typing import Dict, Any, List
from ..core.models import GraphNode, GraphRelationship, NodeType, RelationshipType
from ..core.exceptions import ValidationError


def validate_config(config: Dict[str, Any]) -> None:
    """
    設定データの妥当性をチェックする

    Args:
        config: 設定データ

    Raises:
        ValidationError: 設定が無効な場合
    """
    required_keys = ["paths", "neo4j", "llm"]

    for key in required_keys:
        if key not in config:
            raise ValidationError(f"必須設定項目が不足しています: {key}")

    # パス設定の検証
    paths_config = config["paths"]
    required_path_keys = ["data_dir", "chroma_persist_dir"]

    for key in required_path_keys:
        if key not in paths_config:
            raise ValidationError(f"必須パス設定が不足しています: {key}")


def validate_graph_data(
    nodes: List[Dict[str, Any]], relationships: List[Dict[str, Any]]
) -> None:
    """
    グラフデータの妥当性をチェックする

    Args:
        nodes: ノードデータのリスト
        relationships: リレーションシップデータのリスト

    Raises:
        ValidationError: データが無効な場合
    """
    node_ids = set()

    # ノードの検証
    for node in nodes:
        validate_node_dict(node)
        node_ids.add(node["id"])

    # リレーションシップの検証
    for relationship in relationships:
        validate_relationship_dict(relationship, node_ids)


def validate_node(node: GraphNode) -> None:
    """
    GraphNodeオブジェクトの妥当性をチェックする

    Args:
        node: ノードオブジェクト

    Raises:
        ValidationError: ノードが無効な場合
    """
    if not node.id or not isinstance(node.id, str):
        raise ValidationError("ノードIDが無効です")

    if not isinstance(node.type, NodeType):
        raise ValidationError(f"無効なノードタイプです: {node.type}")

    if not isinstance(node.properties, dict):
        raise ValidationError("ノードプロパティは辞書である必要があります")


def validate_relationship(
    relationship: GraphRelationship, valid_node_ids: set = None
) -> None:
    """
    GraphRelationshipオブジェクトの妥当性をチェックする

    Args:
        relationship: リレーションシップオブジェクト
        valid_node_ids: 有効なノードIDのセット

    Raises:
        ValidationError: リレーションシップが無効な場合
    """
    if not relationship.source or not isinstance(relationship.source, str):
        raise ValidationError("リレーションシップのソースIDが無効です")

    if not relationship.target or not isinstance(relationship.target, str):
        raise ValidationError("リレーションシップのターゲットIDが無効です")

    if not isinstance(relationship.type, RelationshipType):
        raise ValidationError(
            f"無効なリレーションシップタイプです: {relationship.type}"
        )

    if valid_node_ids:
        if relationship.source not in valid_node_ids:
            raise ValidationError(f"存在しないソースノードID: {relationship.source}")

        if relationship.target not in valid_node_ids:
            raise ValidationError(
                f"存在しないターゲットノードID: {relationship.target}"
            )


def validate_node_dict(node: Dict[str, Any]) -> None:
    """
    ノード辞書データの妥当性をチェックする

    Args:
        node: ノード辞書データ

    Raises:
        ValidationError: ノードが無効な場合
    """
    required_keys = ["id", "type"]

    for key in required_keys:
        if key not in node:
            raise ValidationError(f"ノードに必須フィールドが不足しています: {key}")

    if not node["id"] or not isinstance(node["id"], str):
        raise ValidationError("ノードIDが無効です")


def validate_relationship_dict(
    relationship: Dict[str, Any], valid_node_ids: set = None
) -> None:
    """
    リレーションシップ辞書データの妥当性をチェックする

    Args:
        relationship: リレーションシップ辞書データ
        valid_node_ids: 有効なノードIDのセット

    Raises:
        ValidationError: リレーションシップが無効な場合
    """
    required_keys = ["source", "target", "type"]

    for key in required_keys:
        if key not in relationship:
            raise ValidationError(
                f"リレーションシップに必須フィールドが不足しています: {key}"
            )

    if not relationship["source"] or not isinstance(relationship["source"], str):
        raise ValidationError("リレーションシップのソースIDが無効です")

    if not relationship["target"] or not isinstance(relationship["target"], str):
        raise ValidationError("リレーションシップのターゲットIDが無効です")

    if valid_node_ids:
        if relationship["source"] not in valid_node_ids:
            raise ValidationError(f"存在しないソースノードID: {relationship['source']}")

        if relationship["target"] not in valid_node_ids:
            raise ValidationError(
                f"存在しないターゲットノードID: {relationship['target']}"
            )
