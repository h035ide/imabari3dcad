"""
RAG Query データモデル定義

アプリケーション全体で使用される共通データ構造を定義します。
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class NodeType(Enum):
    """ノードタイプの定義"""
    OBJECT = "Object"
    METHOD = "Method"
    PARAMETER = "Parameter"
    RETURN_VALUE = "ReturnValue"
    DATA_TYPE = "DataType"
    ATTRIBUTE = "Attribute"
    SCRIPT_EXAMPLE = "ScriptExample"
    METHOD_CALL = "MethodCall"


class RelationshipType(Enum):
    """リレーションシップタイプの定義"""
    BELONGS_TO = "BELONGS_TO"
    HAS_PARAMETER = "HAS_PARAMETER"
    HAS_RETURNS = "HAS_RETURNS"
    HAS_TYPE = "HAS_TYPE"
    HAS_ATTRIBUTE = "HAS_ATTRIBUTE"
    CONTAINS = "CONTAINS"
    CALLS = "CALLS"
    PASSES_RESULT_TO = "PASSES_RESULT_TO"
    NEXT = "NEXT"
    IS_EXAMPLE_OF = "IS_EXAMPLE_OF"


@dataclass
class GraphNode:
    """グラフノードのデータモデル"""
    id: str
    type: NodeType
    properties: Dict[str, Any]

    def __post_init__(self):
        """型の正規化"""
        if isinstance(self.type, str):
            self.type = NodeType(self.type)


@dataclass
class GraphRelationship:
    """グラフリレーションシップのデータモデル"""
    source: str
    target: str
    type: RelationshipType
    properties: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """型の正規化とデフォルト値設定"""
        if isinstance(self.type, str):
            self.type = RelationshipType(self.type)
        if self.properties is None:
            self.properties = {}


@dataclass
class GraphDocument:
    """グラフドキュメントのデータモデル"""
    nodes: List[GraphNode]
    relationships: List[GraphRelationship]
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """デフォルト値設定"""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class IngestionResult:
    """データ取り込み結果のデータモデル"""
    success: bool
    node_count: int
    relationship_count: int
    processing_time: float
    errors: List[str]
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """デフォルト値設定"""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class QueryRequest:
    """クエリリクエストのデータモデル"""
    query: str
    max_results: int = 10
    filters: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """デフォルト値設定"""
        if self.filters is None:
            self.filters = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class QueryResponse:
    """クエリレスポンスのデータモデル"""
    results: List[Dict[str, Any]]
    total_count: int
    processing_time: float
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """デフォルト値設定"""
        if self.metadata is None:
            self.metadata = {}
