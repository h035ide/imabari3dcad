from __future__ import annotations

"""Configuration objects for the help preprocessor."""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Mapping, Optional


@dataclass(slots=True)
class HelpPreprocessorConfig:
    """Container for runtime configuration of the help ingestion pipeline."""

    source_root: Path
    cache_dir: Path
    output_dir: Path
    index_file: Optional[Path] = None
    encoding: str = "shift_jis"
    target_encoding: str = "utf-8"
    chunk_size: int = 1200
    chunk_overlap: int = 120
    log_level: str = "INFO"
    openai_model: Optional[str] = None
    chroma_collection: Optional[str] = None
    neo4j_uri: Optional[str] = None
    neo4j_username: Optional[str] = None
    neo4j_password: Optional[str] = None


def load_config_from_env(env: Mapping[str, str] | None = None) -> HelpPreprocessorConfig:
    """Create a configuration instance based on environment variables.

    Parameters
    ----------
    env:
        Optional mapping of environment variables. Defaults to ``os.environ``.
    """

    env_mapping: Mapping[str, str] = env or os.environ

    def _get_path(var_name: str, default: Path) -> Path:
        raw = env_mapping.get(var_name)
        if raw:
            return Path(raw).expanduser()
        return default

    def _get_optional_path(var_name: str) -> Optional[Path]:
        raw = env_mapping.get(var_name)
        if raw:
            return Path(raw).expanduser()
        return None

    def _get_int(var_name: str, default: int) -> int:
        raw = env_mapping.get(var_name)
        if raw in (None, ""):
            return default
        try:
            return int(raw)
        except ValueError as exc:  # pragma: no cover - defensive parsing
            raise ValueError(f"Environment variable {var_name} must be an integer: {raw!r}") from exc

    def _get_str(var_name: str, default: Optional[str] = None) -> Optional[str]:
        raw = env_mapping.get(var_name)
        if raw is None:
            return default
        stripped = raw.strip()
        return stripped or default

    source_root = _get_path("HELP_SOURCE_ROOT", Path("evoship/EVOSHIP_HELP_FILES"))
    cache_dir = _get_path("HELP_CACHE_DIR", Path("data/help_preprocessor/cache"))
    output_dir = _get_path("HELP_OUTPUT_DIR", Path("data/help_preprocessor/output"))

    index_file = _get_optional_path("HELP_INDEX_PATH")
    if index_file is None:
        candidate = source_root / "index.txt"
        if candidate.exists():
            index_file = candidate

    return HelpPreprocessorConfig(
        source_root=source_root,
        cache_dir=cache_dir,
        output_dir=output_dir,
        index_file=index_file,
        encoding=_get_str("HELP_SOURCE_ENCODING", "shift_jis") or "shift_jis",
        target_encoding=_get_str("HELP_TARGET_ENCODING", "utf-8") or "utf-8",
        chunk_size=_get_int("HELP_CHUNK_SIZE", 1200),
        chunk_overlap=_get_int("HELP_CHUNK_OVERLAP", 120),
        log_level=_get_str("HELP_LOG_LEVEL", "INFO") or "INFO",
        openai_model=_get_str("HELP_OPENAI_MODEL"),
        chroma_collection=_get_str("HELP_CHROMA_COLLECTION"),
        neo4j_uri=_get_str("HELP_NEO4J_URI"),
        neo4j_username=_get_str("HELP_NEO4J_USERNAME"),
        neo4j_password=_get_str("HELP_NEO4J_PASSWORD"),
    )
