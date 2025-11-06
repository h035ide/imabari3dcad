"""
RAG Query コアモジュール

共通データモデル、例外、ログ管理などの基盤機能を提供します。
"""

from .models import (
    GraphNode,
    GraphRelationship,
    GraphDocument,
    IngestionResult,
    QueryRequest,
    QueryResponse,
)
from .exceptions import (
    RAGQueryError,
    ConfigurationError,
    DataProcessingError,
    StorageError,
    QueryError,
)
from .logger import (
    get_logger,
    set_global_log_file,
    get_global_log_file,
    add_file_handler_to_existing_loggers,
)

__all__ = [
    # データモデル
    "GraphNode",
    "GraphRelationship",
    "GraphDocument",
    "IngestionResult",
    "QueryRequest",
    "QueryResponse",
    # 例外
    "RAGQueryError",
    "ConfigurationError",
    "DataProcessingError",
    "StorageError",
    "QueryError",
    # ログ
    "get_logger",
    "set_global_log_file",
    "get_global_log_file",
    "add_file_handler_to_existing_loggers",
]
