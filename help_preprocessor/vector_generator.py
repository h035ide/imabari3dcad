from __future__ import annotations

"""Embedding generation utilities for help sections."""

from typing import Iterable

from .schemas import HelpSection


class HelpVectorGenerator:
    """Chunk and embed help sections for downstream vector stores."""

    def __init__(self, chunk_size: int = 1200, chunk_overlap: int = 120) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    # TODO(Phase3): Consume cached sections and map to chunk metadata records.
    def build_chunks(self, section: HelpSection) -> Iterable[dict]:  # pragma: no cover - placeholder
        """Yield chunk payloads with associated metadata."""

        raise NotImplementedError("Vector chunk generation has not been implemented yet.")

    def embed_chunks(self, chunks: Iterable[dict]) -> Iterable[dict]:  # pragma: no cover - placeholder
        """Attach vector representations to chunk payloads."""

        raise NotImplementedError("Embedding logic has not been implemented yet.")
