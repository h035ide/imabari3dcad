from __future__ import annotations

from typing import Any

from help_preprocessor.storage.chroma_loader import HelpChromaLoader
from help_preprocessor.storage.neo4j_loader import HelpNeo4jLoader


class _StubSession:
    def __init__(self) -> None:
        self.queries: list[tuple[str, dict[str, Any]]] = []

    def run(self, query: str, **parameters: Any) -> None:
        self.queries.append((query, parameters))

    def __enter__(self) -> "_StubSession":  # pragma: no cover - context manager glue
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover
        return None


class _StubDriver:
    def __init__(self) -> None:
        self.sessions: list[tuple[str | None, _StubSession]] = []

    def session(self, database: str | None = None) -> _StubSession:
        session = _StubSession()
        self.sessions.append((database, session))
        return session

    def close(self) -> None:  # pragma: no cover - compatibility
        return None


class _FakeCollection:
    def __init__(self) -> None:
        self.upserts: list[dict[str, Any]] = []

    def upsert(self, **payload: Any) -> None:
        self.upserts.append(payload)


class _FakeChromaClient:
    def __init__(self) -> None:
        self.collections: dict[str, _FakeCollection] = {}
        self.deleted: list[str] = []

    def get_or_create_collection(self, name: str, metadata: dict[str, Any] | None = None) -> _FakeCollection:
        return self.collections.setdefault(name, _FakeCollection())

    def delete_collection(self, name: str) -> None:
        self.collections.pop(name, None)
        self.deleted.append(name)


def test_neo4j_loader_upsert_and_cleanup() -> None:
    driver = _StubDriver()
    loader = HelpNeo4jLoader(
        uri="bolt://example",
        username="neo4j",
        password="secret",
        database="neo4j",
        driver=driver,
    )

    nodes = [
        {
            "id": "category:root",
            "labels": ["HelpCategory"],
            "properties": {"name": "Root", "topic_count": 1},
        }
    ]
    relationships = [
        {
            "start": "category:root",
            "end": "topic:overview",
            "type": "HAS_TOPIC",
            "properties": {"order": 0},
        }
    ]

    loader.upsert(nodes, relationships)
    assert driver.sessions, "session should be opened"
    node_query, node_params = driver.sessions[0][1].queries[0]
    assert "MERGE (n:HelpCategory" in node_query
    assert node_params["id"] == "category:root"
    assert node_params["props"]["name"] == "Root"

    rel_query, rel_params = driver.sessions[0][1].queries[1]
    assert "MERGE (start)-[rel:HAS_TOPIC]->(end)" in rel_query
    assert rel_params["start_id"] == "category:root"

    loader.cleanup(["HelpCategory", "HelpTopic"])
    cleanup_query, _ = driver.sessions[1][1].queries[0]
    assert "MATCH (n) WHERE" in cleanup_query
    loader.close()


def test_chroma_loader_upsert_and_purge() -> None:
    client = _FakeChromaClient()
    loader = HelpChromaLoader("evoship-help", client=client)

    chunks = [
        {
            "id": "doc#intro",
            "text": "Intro text",
            "metadata": {"section": "intro"},
        },
        {
            "id": "doc#overview",
            "text": "Overview",
            "metadata": {"section": "overview"},
            "embedding": [0.1, 0.2],
        },
    ]

    loader.upsert(chunks)
    collection = client.collections["evoship-help"]
    assert collection.upserts, "chunks should be forwarded"
    payload = collection.upserts[0]
    assert payload["ids"] == ["doc#intro", "doc#overview"]
    assert payload["metadatas"][0]["source"] == "evoship-help"
    assert "embeddings" not in payload

    loader.purge()
    assert "evoship-help" in client.deleted


