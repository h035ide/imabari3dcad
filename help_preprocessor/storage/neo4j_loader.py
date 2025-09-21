from __future__ import annotations

"""Neo4j loader tailored for EVOSHIP help data."""

import re
from typing import Iterable, Mapping, Sequence

from neo4j import Driver, GraphDatabase
from neo4j.exceptions import Neo4jError


class HelpNeo4jLoader:
    """Persist graph payloads into a dedicated Neo4j database."""

    def __init__(
        self,
        uri: str,
        username: str,
        password: str,
        database: str | None = None,
        *,
        driver: Driver | None = None,
    ) -> None:
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self._driver = driver or GraphDatabase.driver(uri, auth=(username, password))
        self._owns_driver = driver is None

    def close(self) -> None:
        """Close the underlying Neo4j driver if owned by this instance."""

        if self._owns_driver and self._driver is not None:
            self._driver.close()
            self._driver = None

    def upsert(self, nodes: Iterable[Mapping], relationships: Iterable[Mapping]) -> None:
        """Write nodes and relationships into Neo4j."""

        if self._driver is None:
            raise RuntimeError("Neo4j driver has been closed.")

        node_list = list(nodes)
        rel_list = list(relationships)

        try:
            with self._driver.session(database=self.database) as session:
                for node in node_list:
                    self._merge_node(session, node)
                for rel in rel_list:
                    self._merge_relationship(session, rel)
        except Neo4jError as exc:  # pragma: no cover - driver level errors
            raise RuntimeError("Failed to upsert help graph data") from exc

    def cleanup(self, labels: Sequence[str] | None = None) -> None:
        """Remove help-related nodes by label prior to ingestion."""

        if self._driver is None:
            raise RuntimeError("Neo4j driver has been closed.")

        target_labels = labels or ("HelpCategory", "HelpTopic")
        if not target_labels:
            return
        predicates = " OR ".join(f"n:{self._sanitize_label(label)}" for label in target_labels)
        query = f"MATCH (n) WHERE {predicates} DETACH DELETE n"

        try:
            with self._driver.session(database=self.database) as session:
                session.run(query)
        except Neo4jError as exc:  # pragma: no cover - driver level errors
            raise RuntimeError("Failed to cleanup help graph data") from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _merge_node(self, session, node: Mapping) -> None:
        node_id = node["id"]
        labels = [self._sanitize_label(label) for label in node.get("labels", []) if label]
        properties = dict(node.get("properties", {}))
        properties.pop("id", None)
        label_fragment = ":".join(labels)
        label_fragment = f":{label_fragment}" if label_fragment else ""
        query = f"MERGE (n{label_fragment} {{id: $id}}) SET n += $props"
        session.run(query, id=node_id, props=properties)

    def _merge_relationship(self, session, relationship: Mapping) -> None:
        start_id = relationship["start"]
        end_id = relationship["end"]
        rel_type = self._sanitize_label(relationship["type"])
        properties = dict(relationship.get("properties", {}))
        query = (
            "MATCH (start {id: $start_id}) "
            "MATCH (end {id: $end_id}) "
            f"MERGE (start)-[rel:{rel_type}]->(end) SET rel += $props"
        )
        session.run(query, start_id=start_id, end_id=end_id, props=properties)

    @staticmethod
    def _sanitize_label(value: str) -> str:
        match = re.findall(r"[A-Za-z0-9_]+", value)
        return "_".join(match) or "HelpNode"

    def __del__(self) -> None:  # pragma: no cover - safety net
        try:
            self.close()
        except Exception:
            pass
