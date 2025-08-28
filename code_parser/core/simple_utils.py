"""
シンプルなユーティリティ機能

コードパーサーで使用する共通のユーティリティ機能を提供します。
"""

import os
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union


class FileUtils:
    """ファイル操作のユーティリティ"""
    
    @staticmethod
    def ensure_directory(path: str) -> None:
        """ディレクトリが存在しない場合は作成"""
        Path(path).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def get_file_hash(file_path: str) -> str:
        """ファイルのハッシュ値を取得"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    @staticmethod
    def is_python_file(file_path: str) -> bool:
        """Pythonファイルかどうかを判定"""
        return Path(file_path).suffix.lower() in ['.py', '.pyx', '.pyi']
    
    @staticmethod
    def find_python_files(directory: str, recursive: bool = True) -> List[str]:
        """Pythonファイルを検索"""
        python_files = []
        path = Path(directory)
        
        if recursive:
            pattern = "**/*.py"
        else:
            pattern = "*.py"
        
        for file_path in path.glob(pattern):
            if file_path.is_file():
                python_files.append(str(file_path))
        
        return python_files


class ValidationUtils:
    """バリデーションのユーティリティ"""
    
    @staticmethod
    def validate_neo4j_config(uri: str, user: str, password: str) -> bool:
        """Neo4j設定の妥当性をチェック"""
        if not uri or not user or not password:
            return False
        
        if not uri.startswith(('neo4j://', 'neo4j+s://', 'bolt://', 'bolt+s://')):
            return False
        
        return True
    
    @staticmethod
    def validate_file_path(file_path: str) -> bool:
        """ファイルパスの妥当性をチェック"""
        if not file_path:
            return False
        
        path = Path(file_path)
        return path.exists() and path.is_file()
    
    @staticmethod
    def validate_python_code(code: str) -> bool:
        """Pythonコードの妥当性をチェック（基本的なチェック）"""
        if not code or not code.strip():
            return False
        
        # 基本的な構文チェック
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError:
            return False


class CacheUtils:
    """キャッシュのユーティリティ"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """キャッシュの初期化"""
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
        self.timestamps = {}
    
    def get(self, key: str) -> Optional[Any]:
        """キャッシュから値を取得"""
        if key not in self.cache:
            return None
        
        # TTLチェック
        if time.time() - self.timestamps[key] > self.ttl:
            del self.cache[key]
            del self.timestamps[key]
            return None
        
        return self.cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """キャッシュに値を設定"""
        # 最大サイズチェック
        if len(self.cache) >= self.max_size:
            # 最も古いエントリを削除
            oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
        
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def clear(self) -> None:
        """キャッシュをクリア"""
        self.cache.clear()
        self.timestamps.clear()


class PerformanceUtils:
    """パフォーマンス測定のユーティリティ"""
    
    @staticmethod
    def measure_time(func):
        """関数の実行時間を測定するデコレータ"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"{func.__name__} の実行時間: {execution_time:.4f}秒")
            return result
        return wrapper
    
    @staticmethod
    def benchmark_function(func, iterations: int = 5, *args, **kwargs) -> Dict[str, float]:
        """関数のベンチマークを実行"""
        times = []
        
        for _ in range(iterations):
            start_time = time.time()
            func(*args, **kwargs)
            end_time = time.time()
            times.append(end_time - start_time)
        
        return {
            "min_time": min(times),
            "max_time": max(times),
            "avg_time": sum(times) / len(times),
            "total_time": sum(times),
            "iterations": iterations
        }


class LogUtils:
    """ログのユーティリティ"""
    
    @staticmethod
    def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
        """ログ設定をセットアップ"""
        import logging
        
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        if log_file:
            logging.basicConfig(
                level=getattr(logging, level.upper()),
                format=log_format,
                handlers=[
                    logging.FileHandler(log_file),
                    logging.StreamHandler()
                ]
            )
        else:
            logging.basicConfig(
                level=getattr(logging, level.upper()),
                format=log_format
            )
    
    @staticmethod
    def get_logger(name: str):
        """ロガーを取得"""
        import logging
        return logging.getLogger(name)


class ConfigUtils:
    """設定のユーティリティ"""
    
    @staticmethod
    def load_env_file(env_path: str = ".env") -> Dict[str, str]:
        """環境変数ファイルを読み込み"""
        env_vars = {}
        
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
        
        return env_vars
    
    @staticmethod
    def get_config_value(key: str, default: Any = None) -> Any:
        """設定値を取得"""
        return os.getenv(key, default)
    
    @staticmethod
    def require_config_value(key: str) -> str:
        """必須の設定値を取得（存在しない場合はエラー）"""
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"必須の設定値 '{key}' が設定されていません")
        return value
