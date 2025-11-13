"""
RAG比較機能の設定ファイル管理モジュール

機密情報（APIキー、パスワードなど）は.envファイルで管理し、
その他の設定（RAG方式の定義、デフォルト値など）はJSON設定ファイルで管理します。
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

# 循環インポートを避けるため、RAG_TYPE_PROPERTY_GRAPHを直接定義
RAG_TYPE_PROPERTY_GRAPH = "property_graph"


@dataclass(slots=True)
class RAGComparisonSettings:
    """RAG比較機能のデフォルト設定"""

    top_k: int = 5
    log_level: str = "INFO"
    console_level: str = "WARNING"
    default_rag_type: str = RAG_TYPE_PROPERTY_GRAPH
    default_chunk_size: int = 800
    default_chunk_overlap: int = 120


@dataclass(slots=True)
class RAGComparisonConfig:
    """RAG比較機能の設定ファイルの構造"""

    rag_configs: List[Dict[str, Any]] = field(default_factory=list)
    default_settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RAGComparisonConfig:
        """辞書から設定を読み込む"""
        return cls(
            rag_configs=data.get("rag_configs", []),
            default_settings=data.get("default_settings", {}),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式に変換"""
        return {
            "rag_configs": self.rag_configs,
            "default_settings": self.default_settings,
            "metadata": self.metadata,
        }

    def load_rag_configs(self) -> List[Any]:  # RAGConfigの型ヒント
        """設定ファイルからRAGConfigのリストを生成"""
        # 循環インポートを避けるため、動的にインポート
        from .rag_comparison import RAGConfig

        configs = []
        for config_dict in self.rag_configs:
            try:
                # 必須フィールドをチェック
                if "name" not in config_dict or "description" not in config_dict:
                    logging.warning("RAG設定にnameまたはdescriptionがありません。スキップします: %s", config_dict)
                    continue

                # RAGConfigを作成
                config = RAGConfig(
                    name=config_dict["name"],
                    description=config_dict["description"],
                    rag_type=config_dict.get("rag_type", RAG_TYPE_PROPERTY_GRAPH),
                    chunk_size=config_dict.get("chunk_size", 800),
                    chunk_overlap=config_dict.get("chunk_overlap", 120),
                    use_llm_extract=config_dict.get("use_llm_extract", False),
                    llm_model=config_dict.get("llm_model"),
                    embed_kg_nodes=config_dict.get("embed_kg_nodes", True),
                    database=config_dict.get("database"),
                    chroma_persist_dir=config_dict.get("chroma_persist_dir"),
                    chroma_collection=config_dict.get("chroma_collection"),
                )
                configs.append(config)
            except Exception as exc:
                logging.warning("RAG設定の読み込みに失敗しました: %s, エラー: %s", config_dict, exc)
        return configs

    def get_settings(self) -> RAGComparisonSettings:
        """デフォルト設定を取得"""
        settings_dict = self.default_settings
        return RAGComparisonSettings(
            top_k=settings_dict.get("top_k", 5),
            log_level=settings_dict.get("log_level", "INFO"),
            console_level=settings_dict.get("console_level", "WARNING"),
            default_rag_type=settings_dict.get("default_rag_type", RAG_TYPE_PROPERTY_GRAPH),
            default_chunk_size=settings_dict.get("default_chunk_size", 800),
            default_chunk_overlap=settings_dict.get("default_chunk_overlap", 120),
        )


def load_config_file(config_path: Path) -> RAGComparisonConfig:
    """設定ファイルを読み込む"""
    if not config_path.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return RAGComparisonConfig.from_dict(data)
    except json.JSONDecodeError as exc:
        raise ValueError(f"設定ファイルのJSON形式が不正です: {config_path}, エラー: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"設定ファイルの読み込みに失敗しました: {config_path}, エラー: {exc}") from exc


def save_config_file(config: RAGComparisonConfig, config_path: Path) -> None:
    """設定ファイルを保存"""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)


def create_default_config_file(config_path: Path) -> None:
    """デフォルト設定ファイルを作成"""
    # 循環インポートを避けるため、動的にインポート
    from .rag_comparison import DEFAULT_CONFIGS

    default_config = RAGComparisonConfig(
        rag_configs=[config.to_dict() for config in DEFAULT_CONFIGS],
        default_settings={
            "top_k": 5,
            "log_level": "INFO",
            "console_level": "WARNING",
            "default_rag_type": RAG_TYPE_PROPERTY_GRAPH,
            "default_chunk_size": 800,
            "default_chunk_overlap": 120,
        },
        metadata={
            "version": "1.0",
            "description": "RAG比較機能の設定ファイル",
            "note": "機密情報（APIキー、パスワードなど）は.envファイルで管理してください",
        },
    )
    save_config_file(default_config, config_path)
    logging.info("デフォルト設定ファイルを作成しました: %s", config_path)


def merge_configs(
    file_configs: List[Any],  # RAGConfigの型ヒント
    default_configs: List[Any],  # RAGConfigの型ヒント
    use_file_only: bool = False,
) -> List[Any]:  # RAGConfigの型ヒント
    """設定ファイルの設定とデフォルト設定をマージ"""
    if use_file_only:
        return file_configs

    # 設定ファイルの設定を優先
    file_config_map = {config.name: config for config in file_configs}
    merged = list(file_configs)

    # デフォルト設定で、設定ファイルにないものを追加
    for default_config in default_configs:
        if default_config.name not in file_config_map:
            merged.append(default_config)

    return merged
