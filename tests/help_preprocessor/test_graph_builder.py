from pathlib import Path

import pytest

from help_preprocessor.graph_builder import HelpGraphBuilder
from help_preprocessor.schemas import HelpCategory, HelpTopic


def make_topic(topic_id: str, title: str, source: Path) -> HelpTopic:
    return HelpTopic(topic_id=topic_id, title=title, source_path=source, sections=[])


def test_graph_builder_creates_nodes_and_relationships(tmp_path: Path) -> None:
    source = tmp_path / "docs"
    source.mkdir()
    root = HelpCategory(category_id="root", name="Root", topics=[], children=[])

    cat_a = HelpCategory(category_id="cat_a", name="Category A", topics=[], children=[])
    cat_b = HelpCategory(category_id="cat_b", name="Category B", topics=[], children=[])
    root.children.extend([cat_a, cat_b])

    topic_1 = make_topic("topic_one", "Topic One", source / "topic_one.html")
    topic_2 = make_topic("topic_two", "Topic Two", source / "topic_two.html")
    cat_a.topics.append(topic_1)
    cat_b.topics.append(topic_2)

    builder = HelpGraphBuilder()
    nodes = builder.build_nodes(root)
    relationships = builder.build_relationships(root)

    category_nodes = [n for n in nodes if builder.category_label in n["labels"]]
    topic_nodes = [n for n in nodes if builder.topic_label in n["labels"]]

    assert {n["properties"]["category_id"] for n in category_nodes} == {"root", "cat_a", "cat_b"}
    assert {n["properties"]["topic_id"] for n in topic_nodes} == {"topic_one", "topic_two"}

    rel_types = {(r["start"], r["end"], r["type"]) for r in relationships}
    assert ("category:root", "category:cat_a", builder.category_rel_type) in rel_types
    assert ("category:root", "category:cat_b", builder.category_rel_type) in rel_types
    assert ("category:cat_a", "topic:topic_one", builder.topic_rel_type) in rel_types
    assert ("category:cat_b", "topic:topic_two", builder.topic_rel_type) in rel_types
