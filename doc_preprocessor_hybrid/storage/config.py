from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def _str_to_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Neo4jConnectionConfig:
    uri: Optional[str]
    username: Optional[str]
    password: Optional[str]
    database: Optional[str]
    clear_existing: bool

    @property
    def enabled(self) -> bool:
        return bool(self.uri and self.username and self.password)

    @classmethod
    def from_env(cls) -> "Neo4jConnectionConfig":
        return cls(
            uri=os.getenv("NEO4J_URI"),
            username=os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER"),
            password=os.getenv("NEO4J_PASSWORD"),
            database=os.getenv("NEO4J_DATABASE"),
            clear_existing=_str_to_bool(os.getenv("NEO4J_CLEAR", "true")),
        )


@dataclass(frozen=True)
class ChromaConfig:
    persist_directory: Optional[Path]
    collection_name: Optional[str]
    embedding_provider: str
    embedding_model: str
    clear_collection: bool
    metadata_source: str

    @property
    def enabled(self) -> bool:
        return bool(self.collection_name)

    @property
    def openai_api_key(self) -> Optional[str]:
        return os.getenv("OPENAI_API_KEY")

    @classmethod
    def from_env(cls) -> "ChromaConfig":
        persist_dir = os.getenv("CHROMA_PERSIST_DIRECTORY")
        provider = os.getenv("CHROMA_EMBEDDING_PROVIDER", "openai").lower()
        model = os.getenv("CHROMA_EMBEDDING_MODEL")
        if not model:
            if provider == "openai":
                model = "text-embedding-3-small"
            else:
                model = "sentence-transformers/all-MiniLM-L6-v2"
        return cls(
            persist_directory=Path(persist_dir) if persist_dir else Path("vector_store"),
            collection_name=os.getenv("CHROMA_COLLECTION", "evo_ship_api"),
            embedding_provider=provider,
            embedding_model=model,
            clear_collection=_str_to_bool(os.getenv("CHROMA_CLEAR", "true")),
            metadata_source=os.getenv("CHROMA_SOURCE_LABEL", "structured_api_enriched"),
        )


@dataclass(frozen=True)
class StorageConfig:
    neo4j: Neo4jConnectionConfig
    chroma: ChromaConfig

    @classmethod
    def load(cls) -> "StorageConfig":
        return cls(neo4j=Neo4jConnectionConfig.from_env(), chroma=ChromaConfig.from_env())
