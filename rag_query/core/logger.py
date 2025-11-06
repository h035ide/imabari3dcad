"""
RAG Query ログ管理

統一されたログ機能を提供します。
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# グローバルなログファイルパス（全ロガーで共有）
_global_log_file: Optional[Path] = None


def set_global_log_file(log_file: Path) -> None:
    """
    グローバルなログファイルパスを設定する
    
    Args:
        log_file: ログファイルパス
    """
    global _global_log_file
    _global_log_file = log_file


def get_global_log_file() -> Optional[Path]:
    """
    グローバルなログファイルパスを取得する
    
    Returns:
        ログファイルパス（設定されていない場合はNone）
    """
    return _global_log_file


def get_logger(
    name: str, log_level: str = "INFO", log_file: Optional[Path] = None
) -> logging.Logger:
    """
    統一されたロガーを取得する

    Args:
        name: ロガー名
        log_level: コンソール出力のログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        log_file: ログファイルパス（指定時はファイル出力も行う。日付・時刻情報が自動追加される）

    Returns:
        設定されたロガー

    Note:
        - コンソール出力: INFOレベル以上（最小限）
        - ファイル出力: DEBUGレベル以上（詳細）
        - ログファイル名に日付・時刻情報（YYYY-MM-DD_HHMMSS形式）が自動追加される
    """
    logger = logging.getLogger(name)

    # 既に設定済みの場合はそのまま返す
    if logger.handlers:
        return logger

    # ログファイルパスが指定されていない場合は、グローバル設定を使用
    if log_file is None:
        log_file = get_global_log_file()

    # ロガーのレベルはDEBUGに設定（ファイル出力でDEBUGを記録するため）
    logger.setLevel(logging.DEBUG)

    # フォーマッター設定
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # コンソールハンドラー（最小限のレベル：INFO）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイルハンドラー（詳細なレベル：DEBUG）
    if log_file:
        # ログファイル名に日付・時刻情報を追加
        log_file_with_datetime = _add_datetime_to_log_file(log_file)
        log_file_with_datetime.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file_with_datetime, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # ファイルは常にDEBUGレベル
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def _add_datetime_to_log_file(log_file: Path) -> Path:
    """
    ログファイル名に日付・時刻情報を追加する

    Args:
        log_file: 元のログファイルパス

    Returns:
        日付・時刻情報が追加されたログファイルパス

    Examples:
        log/app.log -> log/app_2024-01-15_143052.log
        app.log -> app_2024-01-15_143052.log
    """
    # 日付と時刻を YYYY-MM-DD_HHMMSS 形式で取得
    datetime_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    # ファイル名と拡張子を分離
    if log_file.suffix:
        # 拡張子がある場合
        new_name = f"{log_file.stem}_{datetime_str}{log_file.suffix}"
    else:
        # 拡張子がない場合
        new_name = f"{log_file.name}_{datetime_str}"

    # 新しいパスを構築
    return log_file.parent / new_name


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
