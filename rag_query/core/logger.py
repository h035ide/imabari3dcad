"""
RAG Query ログ管理

統一されたログ機能を提供します。
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def get_logger(name: str, log_level: str = "INFO", log_file: Optional[Path] = None) -> logging.Logger:
    """
    統一されたロガーを取得する
    
    Args:
        name: ロガー名
        log_level: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        log_file: ログファイルパス（指定時はファイル出力も行う）
        
    Returns:
        設定されたロガー
    """
    logger = logging.getLogger(name)
    
    # 既に設定済みの場合はそのまま返す
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # フォーマッター設定
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # ファイルハンドラー（指定時のみ）
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def setup_progress_logger(name: str) -> logging.Logger:
    """
    進捗表示用の簡易ロガーを設定する
    
    Args:
        name: ロガー名
        
    Returns:
        進捗表示用ロガー
    """
    logger = logging.getLogger(f"{name}.progress")
    
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    
    # シンプルなフォーマッター（進捗表示用）
    formatter = logging.Formatter("%(message)s")
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger
