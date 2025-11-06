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
    LLM_VERBOSITY,
    LLM_REASONING_EFFORT,
    LLM_RESPONSE_FORMAT,
    LLM_OUTPUT_VERSION,
    LLM_REQUEST_TIMEOUT,
    IS_INFERENCE_MODEL,
    # 埋め込みモデル設定
    EMBEDDING_MODEL_NAME,
    EMBEDDING_BATCH_SIZE,
    # APIキー
    OPENAI_API_KEY,
    GEMINI_API_KEY,
    # 設定関数
    get_langchain_llm_config,
    get_llamaindex_llm_config,
    get_langchain_embedding_config,
    get_llamaindex_embedding_config,
    print_llm_config,
    print_embedding_config,
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
    "LLM_VERBOSITY",
    "LLM_REASONING_EFFORT",
    "LLM_RESPONSE_FORMAT",
    "LLM_OUTPUT_VERSION",
    "LLM_REQUEST_TIMEOUT",
    "IS_INFERENCE_MODEL",
    # 埋め込みモデル設定
    "EMBEDDING_MODEL_NAME",
    "EMBEDDING_BATCH_SIZE",
    # APIキー
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    # 設定関数
    "get_langchain_llm_config",
    "get_llamaindex_llm_config",
    "get_langchain_embedding_config",
    "get_llamaindex_embedding_config",
    "print_llm_config",
    "print_embedding_config",
]
