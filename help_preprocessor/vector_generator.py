from __future__ import annotations

"""Embedding generation utilities for help sections."""

from dataclasses import dataclass
from typing import Iterable, Iterator

from .schemas import HelpSection


@dataclass(slots=True)
class VectorChunk:
    """Represents a chunk of text ready for embedding."""

    chunk_id: str
    text: str
    metadata: dict


class HelpVectorGenerator:
    """Chunk and embed help sections for downstream vector stores."""

    def __init__(self, chunk_size: int = 1200, chunk_overlap: int = 120) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def build_chunks(self, section: HelpSection) -> list[dict]:
        """Yield chunk payloads with associated metadata."""

        chunks: list[VectorChunk] = []
        for idx, (offset, text) in enumerate(self._split_section(section.content)):
            chunk_id = f"{section.section_id}:{idx}"
            metadata = {
                "section_id": section.section_id,
                "title": section.title,
                "offset": offset,
                "length": len(text),
                "anchors": section.anchors,
                "link_count": len(section.links),
                "media_count": len(section.media),
            }
            chunks.append(VectorChunk(chunk_id=chunk_id, text=text, metadata=metadata))
        return [
            {
                "id": chunk.chunk_id,
                "text": chunk.text,
                "metadata": chunk.metadata,
            }
            for chunk in chunks
        ]

    def embed_chunks(self, chunks: Iterable[dict]) -> Iterable[dict]:  # pragma: no cover - placeholder
        """Attach vector representations to chunk payloads."""

        raise NotImplementedError("Embedding logic has not been implemented yet.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _split_section(self, content: str) -> Iterator[tuple[int, str]]:
        normalized = content.strip()
        if not normalized:
            return
        step = self.chunk_size - self.chunk_overlap
        start = 0
        length = len(normalized)
        while start < length:
            end = min(start + self.chunk_size, length)
            text = normalized[start:end]
            yield start, text
            if end == length:
                break
            start += step
