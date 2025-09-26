from pathlib import Path

import pytest

from help_preprocessor.index_parser import HelpIndexParser


def write_index(tmp_path: Path, content: str) -> Path:
    index_path = tmp_path / "index.txt"
    index_path.write_text(content, encoding="shift_jis")
    return index_path


def test_parse_builds_hierarchy(tmp_path: Path) -> None:
    content = (
        "*Top Level\n"
        "First Topic (topic_one)\n"
        "    Second Topic topic_two\n"
        "\n"
        "**Sub Level\n"
        "\tSub Topic(sub_topic)\n"
    )
    index_path = write_index(tmp_path, content)
    parser = HelpIndexParser(index_path)
    root = parser.parse()

    assert len(root.children) == 1
    top = root.children[0]
    assert top.name == "Top Level"
    assert [t.topic_id for t in top.topics] == ["topic_one", "topic_two"]

    sub = top.children[0]
    assert sub.name == "Sub Level"
    assert [t.topic_id for t in sub.topics] == ["sub_topic"]
    assert (index_path.parent / "topic_one.html") == top.topics[0].source_path

    assert list(parser.iter_errors()) == []


def test_parse_generates_fallback_ids(tmp_path: Path) -> None:
    content = "*Guide\n無題\n"
    index_path = write_index(tmp_path, content)
    parser = HelpIndexParser(index_path)
    root = parser.parse()

    topics = root.children[0].topics
    assert topics[0].topic_id.startswith("item")
    errors = list(parser.iter_errors())
    assert any("Missing topic identifier" in msg for msg in errors)
