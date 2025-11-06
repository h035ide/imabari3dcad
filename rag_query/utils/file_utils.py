"""
ファイル操作ユーティリティ

ファイル読み込み、ディレクトリ操作などの共通機能を提供します。
"""

from pathlib import Path
from typing import List, Tuple, Optional
from ..core.exceptions import DataProcessingError
from ..core.logger import get_logger

logger = get_logger(__name__)


def read_text_file(file_path: Path, encoding: str = "utf-8") -> str:
    """
    テキストファイルを読み込む

    Args:
        file_path: ファイルパス
        encoding: エンコーディング

    Returns:
        ファイル内容

    Raises:
        DataProcessingError: ファイル読み込み失敗時
    """
    try:
        if not file_path.exists():
            raise DataProcessingError(f"ファイルが見つかりません: {file_path}")

        return file_path.read_text(encoding=encoding)
    except Exception as e:
        raise DataProcessingError(f"ファイル読み込みエラー: {file_path}", str(e))


def read_api_files(file_paths: List[Path]) -> List[Tuple[str, str]]:
    """
    API仕様書ファイルを読み込む

    Args:
        file_paths: ファイルパスのリスト

    Returns:
        (ファイル名, 内容)のタプルのリスト
    """
    api_files = []

    for file_path in file_paths:
        if not file_path.exists():
            logger.warning(f"APIファイルが見つかりません: {file_path}")
            continue

        try:
            content = read_text_file(file_path)
            api_files.append((file_path.name, content))
            logger.info(f"APIファイルを読み込みました: {file_path.name}")
        except DataProcessingError as e:
            logger.error(f"APIファイル読み込みエラー: {e}")

    return api_files


def read_script_files(data_dir: Path, pattern: str = "*.py") -> List[Tuple[str, str]]:
    """
    スクリプトファイルを読み込む

    Args:
        data_dir: データディレクトリ
        pattern: ファイルパターン

    Returns:
        (ファイル名, 内容)のタプルのリスト
    """
    script_files = []

    if not data_dir.exists():
        logger.warning(f"データディレクトリが見つかりません: {data_dir}")
        return script_files

    for file_path in data_dir.glob(pattern):
        if file_path.is_file():
            try:
                content = read_text_file(file_path)
                script_files.append((file_path.name, content))
                logger.info(f"スクリプトファイルを読み込みました: {file_path.name}")
            except DataProcessingError as e:
                logger.error(f"スクリプトファイル読み込みエラー: {e}")

    return script_files


def ensure_directory(dir_path: Path) -> None:
    """
    ディレクトリの存在を確保する（存在しない場合は作成）

    Args:
        dir_path: ディレクトリパス

    Raises:
        DataProcessingError: ディレクトリ作成失敗時
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise DataProcessingError(f"ディレクトリ作成エラー: {dir_path}", str(e))


def find_file_from_candidates(candidates: List[Path]) -> Optional[Path]:
    """
    候補リストから最初に見つかったファイルを返す

    Args:
        candidates: 候補ファイルパスのリスト

    Returns:
        見つかったファイルパス、またはNone
    """
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None
