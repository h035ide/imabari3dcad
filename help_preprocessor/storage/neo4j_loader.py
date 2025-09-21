from __future__ import annotations

"""Neo4j loader tailored for EVOSHIP help data."""

from typing import Iterable


class HelpNeo4jLoader:
    """Persist graph payloads into a dedicated Neo4j database."""

    def __init__(self, uri: str, username: str, password: str, database: str | None = None) -> None:
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database

    def upsert(self, nodes: Iterable[dict], relationships: Iterable[dict]) -> None:  # pragma: no cover - placeholder
        """Write nodes and relationships into Neo4j."""

        raise NotImplementedError("Neo4j upsert logic has not been implemented yet.")

    def cleanup(self) -> None:  # pragma: no cover - placeholder
        """Perform help-specific cleanup operations prior to ingestion."""

        raise NotImplementedError("Cleanup strategy has not been implemented yet.")
