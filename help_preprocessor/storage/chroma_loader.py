from __future__ import annotations

"""Chroma loader tailored for EVOSHIP help embeddings."""

from typing import Iterable


class HelpChromaLoader:
    """Persist help embeddings into a dedicated Chroma collection."""

    def __init__(self, collection_name: str, persist_directory: str | None = None) -> None:
        self.collection_name = collection_name
        self.persist_directory = persist_directory

    def upsert(self, chunks: Iterable[dict]) -> None:  # pragma: no cover - placeholder
        """Write embedding chunks into Chroma."""

        raise NotImplementedError("Chroma upsert logic has not been implemented yet.")

    def purge(self) -> None:  # pragma: no cover - placeholder
        """Remove obsolete help data from the collection."""

        raise NotImplementedError("Chroma purge logic has not been implemented yet.")
