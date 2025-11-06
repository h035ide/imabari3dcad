"""
設定管理モジュール
- 機密情報（APIキー、パスワード）: .envファイルから読み込み
- アプリケーション設定（パス、モデル設定など）: config.yamlから読み込み
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import yaml

# .envファイルから機密情報を読み込み
load_dotenv()

# ===== 機密情報（.envから読み込み） =====
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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

# LLM設定
LLM_MODEL_NAME = _yaml_config.get("llm", {}).get("model_name", "gpt-4")
LLM_TEMPERATURE = _yaml_config.get("llm", {}).get("temperature", 0)
LLM_REQUEST_TIMEOUT = _yaml_config.get("llm", {}).get("request_timeout", None)
