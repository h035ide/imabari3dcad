from __future__ import annotations

"""Graph construction pipeline pieces for the help preprocessor."""

from dataclasses import dataclass

from .schemas import HelpCategory, HelpTopic


@dataclass(slots=True)
class GraphNode:
    """Lightweight representation of a graph node."""

    node_id: str
    labels: list[str]
    properties: dict


@dataclass(slots=True)
class GraphRelationship:
    """Lightweight representation of a graph relationship."""

    start: str
    end: str
    rel_type: str
    properties: dict


class HelpGraphBuilder:
    """Create Neo4j-ready payloads from help category structures."""

    def __init__(
        self,
        *,
        category_label: str = "HelpCategory",
        topic_label: str = "HelpTopic",
        category_rel_type: str = "HAS_CHILD_CATEGORY",
        topic_rel_type: str = "HAS_TOPIC",
    ) -> None:
        self.category_label = category_label
        self.topic_label = topic_label
        self.category_rel_type = category_rel_type
        self.topic_rel_type = topic_rel_type

    def build_nodes(self, root_category: HelpCategory) -> list[dict]:
        """Return graph node dictionaries ready for ingestion."""

        nodes: list[GraphNode] = []
        self._collect_category_nodes(root_category, nodes)
        return [
            {
                "id": node.node_id,
                "labels": node.labels,
                "properties": node.properties,
            }
            for node in nodes
        ]

    def build_relationships(self, root_category: HelpCategory) -> list[dict]:
        """Return graph relationship dictionaries ready for ingestion."""

        relationships: list[GraphRelationship] = []
        self._collect_relationships(root_category, relationships)
        return [
            {
                "start": rel.start,
                "end": rel.end,
                "type": rel.rel_type,
                "properties": rel.properties,
            }
            for rel in relationships
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _collect_category_nodes(self, category: HelpCategory, nodes: list[GraphNode]) -> None:
        nodes.append(
            GraphNode(
                node_id=self._category_node_id(category.category_id),
                labels=[self.category_label],
                properties={
                    "category_id": category.category_id,
                    "name": category.name,
                    "topic_count": len(category.topics),
                    "child_count": len(category.children),
                },
            )
        )
        for topic in category.topics:
            nodes.append(self._topic_node(topic))
        for child in category.children:
            self._collect_category_nodes(child, nodes)

    def _collect_relationships(
        self,
        category: HelpCategory,
        relationships: list[GraphRelationship],
    ) -> None:
        start_id = self._category_node_id(category.category_id)
        for idx, child in enumerate(category.children):
            relationships.append(
                GraphRelationship(
                    start=start_id,
                    end=self._category_node_id(child.category_id),
                    rel_type=self.category_rel_type,
                    properties={"order": idx},
                )
            )
            self._collect_relationships(child, relationships)
        for idx, topic in enumerate(category.topics):
            relationships.append(
                GraphRelationship(
                    start=start_id,
                    end=self._topic_node_id(topic.topic_id),
                    rel_type=self.topic_rel_type,
                    properties={"order": idx},
                )
            )

    def _topic_node(self, topic: HelpTopic) -> GraphNode:
        return GraphNode(
            node_id=self._topic_node_id(topic.topic_id),
            labels=[self.topic_label],
            properties={
                "topic_id": topic.topic_id,
                "title": topic.title,
                "source_path": str(topic.source_path),
                "section_count": len(topic.sections),
            },
        )

    @staticmethod
    def _category_node_id(category_id: str) -> str:
        return f"category:{category_id}"

    @staticmethod
    def _topic_node_id(topic_id: str) -> str:
        return f"topic:{topic_id}"
