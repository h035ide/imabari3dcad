"""
RAG Query モジュール

RAG（Retrieval-Augmented Generation）クエリ処理を提供します。
設定管理、グラフデータの取り込み、クエリ処理などの機能を提供します。
"""

# 設定モジュールから主要な設定をエクスポート
from .config import (
    # パス設定
    DATA_DIR,
    CHROMA_PERSIST_DIR,
    API_ARG_TXT_CANDIDATES,
    # Neo4j設定
    NEO4J_URI,
    NEO4J_USER,
    NEO4J_PASSWORD,
    NEO4J_DATABASE,
    # LLM設定
    LLM_MODEL_NAME,
    LLM_TEMPERATURE,
    LLM_REQUEST_TIMEOUT,
    # APIキー
    OPENAI_API_KEY,
    GEMINI_API_KEY,
)

# パブリックAPIとして公開する要素を定義
__all__ = [
    # パス設定
    "DATA_DIR",
    "CHROMA_PERSIST_DIR",
    "API_ARG_TXT_CANDIDATES",
    # Neo4j設定
    "NEO4J_URI",
    "NEO4J_USER",
    "NEO4J_PASSWORD",
    "NEO4J_DATABASE",
    # LLM設定
    "LLM_MODEL_NAME",
    "LLM_TEMPERATURE",
    "LLM_REQUEST_TIMEOUT",
    # APIキー
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
]

