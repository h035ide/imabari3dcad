"""
RAG Query カスタム例外定義

アプリケーション固有の例外クラスを定義します。
"""


class RAGQueryError(Exception):
    """RAG Query アプリケーションの基底例外クラス"""

    def __init__(self, message: str, details: str = None):
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class ConfigurationError(RAGQueryError):
    """設定関連のエラー"""

    pass


class DataProcessingError(RAGQueryError):
    """データ処理関連のエラー"""

    pass


class StorageError(RAGQueryError):
    """ストレージ関連のエラー"""

    pass


class QueryError(RAGQueryError):
    """クエリ処理関連のエラー"""

    pass


class ValidationError(RAGQueryError):
    """バリデーション関連のエラー"""

    pass


class LLMError(RAGQueryError):
    """LLM処理関連のエラー"""

    pass
