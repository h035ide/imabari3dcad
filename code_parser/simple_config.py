"""
シンプルな設定ファイル

コードパーサーの設定を一元管理します。
"""

import os
from pathlib import Path

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent

# データベース設定
NEO4J_CONFIG = {
    "uri": os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
    "user": os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER", "neo4j"),
    "password": os.getenv("NEO4J_PASSWORD", "password"),
    "database": os.getenv("NEO4J_DATABASE", "codeparsar")
}

# ベクトル検索設定
VECTOR_SEARCH_CONFIG = {
    "persist_directory": str(PROJECT_ROOT / "vector_store"),
    "collection_name": "python_code",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
}

# LLM設定
LLM_CONFIG = {
    "model_name": os.getenv("OPENAI_MODEL", "gpt-4"),
    "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.1")),
    "api_key": os.getenv("OPENAI_API_KEY")
}

# ファイル設定
FILE_CONFIG = {
    "default_file": "evoship/create_test.py",
    "supported_extensions": [".py", ".pyx", ".pyi"],
    "exclude_patterns": ["__pycache__", "*.pyc", ".git", "venv", "env"]
}

# ログ設定
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}

# パフォーマンス設定
PERFORMANCE_CONFIG = {
    "cache_ttl": 3600,  # 1時間
    "max_cache_size": 1000,
    "benchmark_iterations": 5
}

# 検索設定
SEARCH_CONFIG = {
    "default_top_k": 5,
    "max_top_k": 50,
    "similarity_threshold": 0.7
}
