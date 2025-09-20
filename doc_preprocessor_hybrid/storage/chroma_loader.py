from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List

import chromadb
from chromadb.api import ClientAPI
from chromadb.utils import embedding_functions

from ..schemas import ApiBundle
from .config import ChromaConfig


class ChromaIngestError(RuntimeError):
    pass


def _create_client(config: ChromaConfig) -> ClientAPI:
    if config.persist_directory and str(config.persist_directory).strip():
        config.persist_directory.mkdir(parents=True, exist_ok=True)
        return chromadb.PersistentClient(path=str(config.persist_directory))  # type: ignore[arg-type]
    return chromadb.Client()


def _build_embedding_function(config: ChromaConfig):
    provider = config.embedding_provider
    if provider == "openai":
        api_key = config.openai_api_key
        if not api_key:
            raise ChromaIngestError("OPENAI_API_KEY is required when CHROMA_EMBEDDING_PROVIDER=openai")
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name=config.embedding_model,
        )
    if provider in {"sentence-transformers", "sbert"}:
        return embedding_functions.SentenceTransformerEmbeddingFunction(model_name=config.embedding_model)
    raise ChromaIngestError(f"Unsupported embedding provider: {provider}")


def _load_vector_records(path: Path) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []
    if not path.exists():
        raise FileNotFoundError(f"Vector chunks file not found: {path}")
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def store_vectors(
    bundle: ApiBundle,
    vector_path: Path,
    config: ChromaConfig,
) -> Dict[str, object]:
    if not config.enabled:
        raise ValueError("Chroma collection name is not configured (CHROMA_COLLECTION)")

    records = _load_vector_records(vector_path)
    if not records:
        return {"documents": 0}

    embedding_function = _build_embedding_function(config)
    client = _create_client(config)

    if config.clear_collection:
        try:
            client.delete_collection(config.collection_name)
        except chromadb.errors.NotFoundError:
            pass

    collection = client.get_or_create_collection(
        name=config.collection_name,
        embedding_function=embedding_function,
        metadata={"source": config.metadata_source},
    )

    ids: List[str] = []
    documents: List[str] = []
    metadatas: List[Dict[str, object]] = []

    entry_lookup = {entry.name: entry for entry in bundle.api_entries}

    for record in records:
        doc_id = str(record.get("id"))
        if not doc_id:
            continue
        ids.append(doc_id)
        documents.append(record.get("content", ""))
        entry = entry_lookup.get(doc_id)
        metadata: Dict[str, object] = {
            "object": record.get("object"),
            "title_jp": record.get("title_jp"),
        }
        if entry:
            metadata.update(
                {
                    "category": entry.category,
                    "object_name": entry.object_name,
                }
            )
        metadatas.append(metadata)

    if not ids:
        return {"documents": 0}

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    return {"documents": len(ids), "collection": config.collection_name}
