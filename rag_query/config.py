"""
設定管理モジュール
- 機密情報（APIキー、パスワード）: .envファイルから読み込み
- アプリケーション設定（パス、モデル設定など）: config.yamlから読み込み
"""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv
import yaml

# .envファイルから機密情報を読み込み
load_dotenv()

# ===== 機密情報（.envから読み込み） =====
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ===== アプリケーション設定（config.yamlから読み込み） =====
_CONFIG_FILE = Path(__file__).parent / "config.yaml"


def _load_yaml_config() -> dict:
    """config.yamlを読み込む"""
    if _CONFIG_FILE.exists():
        with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    else:
        raise FileNotFoundError(f"config.yaml not found: {_CONFIG_FILE}")


_yaml_config = _load_yaml_config()

# パス設定
paths_config = _yaml_config.get("paths", {})
DATA_DIR = Path(paths_config.get("data_dir", "data"))
CHROMA_PERSIST_DIR = Path(paths_config.get("chroma_persist_dir", "data/chroma_db"))

# API引数テキストファイルの候補パス
api_arg_candidates = paths_config.get("api_arg_txt", ["data/src/api_arg.txt"])
API_ARG_TXT_CANDIDATES = [Path(p) for p in api_arg_candidates]

# Neo4j設定
NEO4J_DATABASE = _yaml_config.get("neo4j", {}).get("database", "neo4j")

# LLM設定（環境変数で上書き可能）
llm_config = _yaml_config.get("llm", {})
LLM_MODEL_NAME = os.getenv("LLM_MODEL", llm_config.get("model_name", "gpt-4"))
LLM_TEMPERATURE = llm_config.get("temperature", 0)
LLM_VERBOSITY = llm_config.get("verbosity", "high")
LLM_REASONING_EFFORT = llm_config.get("reasoning_effort", "high")
LLM_RESPONSE_FORMAT = llm_config.get("response_format", "text")
LLM_OUTPUT_VERSION = llm_config.get("output_version", "responses/v1")
LLM_REQUEST_TIMEOUT = llm_config.get("request_timeout", None)

# 埋め込みモデル設定（環境変数で上書き可能）
embedding_config = _yaml_config.get("embedding", {})
EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL", embedding_config.get("model_name", "text-embedding-3-small")
)
EMBEDDING_BATCH_SIZE = int(
    os.getenv("EMBEDDING_BATCH_SIZE", str(embedding_config.get("batch_size", 100)))
)


def _is_inference_model(model_name: str) -> bool:
    """
    推論モデルかどうかを判定する

    Args:
        model_name: モデル名

    Returns:
        推論モデルの場合True
    """
    inference_models = ["o4-mini", "o4", "gpt-5", "gpt-5-mini", "gpt-5-nano"]
    return any(model in model_name.lower() for model in inference_models)


# 推論モデル判定
IS_INFERENCE_MODEL = _is_inference_model(LLM_MODEL_NAME)

# 推論モデルの場合、temperatureはNoneに設定
if IS_INFERENCE_MODEL:
    LLM_TEMPERATURE = None


def get_langchain_llm_config() -> Dict[str, Any]:
    """
    LangChain用のLLM設定辞書を取得する

    Returns:
        LangChain用LLM設定辞書
    """
    config = {
        "model_name": LLM_MODEL_NAME,
        "openai_api_key": OPENAI_API_KEY,
    }

    if IS_INFERENCE_MODEL:
        # 推論モデル用パラメータ
        config.update(
            {
                "reasoning_effort": LLM_REASONING_EFFORT,
                "output_version": LLM_OUTPUT_VERSION,
                "verbosity": LLM_VERBOSITY,
                "response_format": LLM_RESPONSE_FORMAT,
            }
        )
    else:
        # 標準モデル用パラメータ
        if LLM_TEMPERATURE is not None:
            config["temperature"] = LLM_TEMPERATURE

    if LLM_REQUEST_TIMEOUT is not None:
        config["request_timeout"] = LLM_REQUEST_TIMEOUT

    return config


def get_llamaindex_llm_config() -> Dict[str, Any]:
    """
    LlamaIndex用のLLM設定辞書を取得する

    Returns:
        LlamaIndex用LLM設定辞書
    """
    config = {
        "model": LLM_MODEL_NAME,
        "api_key": OPENAI_API_KEY,
    }

    if IS_INFERENCE_MODEL:
        # 推論モデル用パラメータ
        config.update(
            {
                "reasoning_effort": LLM_REASONING_EFFORT,
                "output_version": LLM_OUTPUT_VERSION,
                "verbosity": LLM_VERBOSITY,
                "response_format": LLM_RESPONSE_FORMAT,
            }
        )
    else:
        # 標準モデル用パラメータ
        if LLM_TEMPERATURE is not None:
            config["temperature"] = LLM_TEMPERATURE

    return config


def get_langchain_embedding_config() -> Dict[str, Any]:
    """
    LangChain用の埋め込みモデル設定辞書を取得する

    Returns:
        LangChain用埋め込みモデル設定辞書
    """
    return {
        "model": EMBEDDING_MODEL_NAME,
        "openai_api_key": OPENAI_API_KEY,
    }


def get_llamaindex_embedding_config() -> Dict[str, Any]:
    """
    LlamaIndex用の埋め込みモデル設定辞書を取得する

    Returns:
        LlamaIndex用埋め込みモデル設定辞書
    """
    return {
        "model": EMBEDDING_MODEL_NAME,
        "batch_size": EMBEDDING_BATCH_SIZE,
        "api_key": OPENAI_API_KEY,
    }


def print_llm_config() -> None:
    """LLM設定を表示する"""
    print("🤖 LLM設定:")
    print(f"  モデル: {LLM_MODEL_NAME}")
    print(f"  推論モデル: {'✅' if IS_INFERENCE_MODEL else '❌'}")
    print(f"  Temperature: {LLM_TEMPERATURE}")
    print(f"  Response Format: {LLM_RESPONSE_FORMAT}")

    if IS_INFERENCE_MODEL:
        print(f"  Verbosity: {LLM_VERBOSITY}")
        print(f"  Reasoning Effort: {LLM_REASONING_EFFORT}")

    print("\n📋 LangChain設定:")
    langchain_config = get_langchain_llm_config()
    for key, value in langchain_config.items():
        if key != "openai_api_key":  # APIキーは表示しない
            print(f"  {key}: {value}")

    print("\n📋 LlamaIndex設定:")
    llamaindex_config = get_llamaindex_llm_config()
    for key, value in llamaindex_config.items():
        if key != "api_key":  # APIキーは表示しない
            print(f"  {key}: {value}")


def print_embedding_config() -> None:
    """埋め込みモデル設定を表示する"""
    print("🔤 埋め込みモデル設定:")
    print(f"  モデル: {EMBEDDING_MODEL_NAME}")
    print(f"  バッチサイズ: {EMBEDDING_BATCH_SIZE}")

    print("\n📋 LangChain設定:")
    langchain_config = get_langchain_embedding_config()
    for key, value in langchain_config.items():
        if key != "openai_api_key":  # APIキーは表示しない
            print(f"  {key}: {value}")

    print("\n📋 LlamaIndex設定:")
    llamaindex_config = get_llamaindex_embedding_config()
    for key, value in llamaindex_config.items():
        if key != "api_key":  # APIキーは表示しない
            print(f"  {key}: {value}")
