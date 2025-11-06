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
    if not _CONFIG_FILE.exists():
        # デフォルト値を返す
        return {
            "paths": {
                "data_dir": "data",
                "chroma_persist_dir": "data/chroma_db",
                "api_arg_txt_candidates": [
                    "/mnt/data/api_arg.txt",
                    "api_arg.txt",
                    "data/api_arg.txt"
                ]
            },
            "neo4j": {
                "database": "neo4j"
            },
            "llm": {
                "model_name": "gpt-5",
                "temperature": 0
            }
        }

    with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


_yaml_config = _load_yaml_config()

# パス設定
DATA_DIR = Path(_yaml_config.get("paths", {}).get("data_dir", "data"))
CHROMA_PERSIST_DIR = Path(_yaml_config.get("paths", {}).get("chroma_persist_dir", "data/chroma_db"))
API_ARG_TXT_CANDIDATES = [
    Path(p) for p in _yaml_config.get("paths", {}).get("api_arg_txt_candidates", [
        "/mnt/data/api_arg.txt",
        "api_arg.txt",
        "data/api_arg.txt"
    ])
]

# Neo4j設定
NEO4J_DATABASE = _yaml_config.get("neo4j", {}).get("database", "neo4j")

# LLM設定
LLM_MODEL_NAME = _yaml_config.get("llm", {}).get("model_name", "gpt-5")
LLM_TEMPERATURE = _yaml_config.get("llm", {}).get("temperature", 0)
LLM_REQUEST_TIMEOUT = _yaml_config.get("llm", {}).get("request_timeout", None)
