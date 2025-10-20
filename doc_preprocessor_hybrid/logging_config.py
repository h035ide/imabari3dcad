"""ログ設定モジュール"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    log_dir: Optional[Path] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    ログ設定を初期化する

    Args:
        log_level: ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: ログファイルのパス（指定しない場合は自動生成）
        log_dir: ログディレクトリ（指定しない場合は出力ディレクトリを使用）
        max_file_size: ログファイルの最大サイズ（バイト）
        backup_count: 保持するログファイル数

    Returns:
        設定されたロガー
    """
    # ログレベルを設定
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # ルートロガーを取得
    logger = logging.getLogger("doc_preprocessor_hybrid")
    logger.setLevel(numeric_level)

    # 既存のハンドラーをクリア
    logger.handlers.clear()

    # フォーマッターを設定
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # コンソールハンドラーを追加
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイルハンドラーを追加
    if log_file is None:
        if log_dir is None:
            log_dir = Path("doc_preprocessor_hybrid/out")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "pipeline.log"

    # ローテーティングファイルハンドラーを使用
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_file_size, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # プロパゲーションを無効化（重複出力を防ぐ）
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    指定された名前のロガーを取得する

    Args:
        name: ロガー名（通常はモジュール名）

    Returns:
        ロガーインスタンス
    """
    return logging.getLogger(f"doc_preprocessor_hybrid.{name}")
