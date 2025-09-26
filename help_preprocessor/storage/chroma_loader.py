from __future__ import annotations

"""Chroma loader tailored for EVOSHIP help embeddings."""

from typing import Iterable, Mapping, Sequence


class HelpChromaLoader:
    """Persist help embeddings into a dedicated Chroma collection."""

    def __init__(
        self,
        collection_name: str,
        persist_directory: str | None = None,
        *,
        client=None,
        metadata: Mapping | None = None,
    ) -> None:
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self._client = client or self._create_client(persist_directory)
        self._collection_metadata = dict(metadata or {"source": "evoship-help"})

    def _create_client(self, persist_directory: str | None):  # pragma: no cover
        from chromadb import Client
        from chromadb.config import Settings

        settings = Settings(
            persist_directory=persist_directory,
            is_persistent=persist_directory is not None,
        )
        return Client(settings)

    def _get_collection(self):
        return self._client.get_or_create_collection(
            name=self.collection_name,
            metadata=self._collection_metadata,
        )

    def upsert(self, chunks: Iterable[Mapping]) -> None:
        collection = self._get_collection()
        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[Mapping] = []
        embeddings: list[Sequence[float]] = []
        use_embeddings = True

        for chunk in chunks:
            chunk_id = str(chunk["id"])
            text = chunk.get("text", "")
            metadata = dict(chunk.get("metadata", {}))
            metadata.setdefault("source", self._collection_metadata.get("source", "evoship-help"))

            ids.append(chunk_id)
            documents.append(text)
            metadatas.append(metadata)

            vector = chunk.get("embedding")
            if vector is None:
                use_embeddings = False
            else:
                embeddings.append(vector)

        if not ids:
            return

        kwargs = {"ids": ids, "documents": documents, "metadatas": metadatas}
        if use_embeddings and len(embeddings) == len(ids):
            kwargs["embeddings"] = embeddings
        collection.upsert(**kwargs)

    def purge(self) -> None:
        self._client.delete_collection(name=self.collection_name)
