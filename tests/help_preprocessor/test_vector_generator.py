from pathlib import Path

import pytest

from help_preprocessor.vector_generator import HelpVectorGenerator
from help_preprocessor.schemas import HelpSection


def make_section(content: str) -> HelpSection:
    return HelpSection(
        section_id="sec-1",
        title="Overview",
        content=content,
        anchors=["overview"],
        links=[],
        media=[],
    )


def test_build_chunks_respects_size_and_overlap() -> None:
    generator = HelpVectorGenerator(chunk_size=8, chunk_overlap=2)
    section = make_section("abcdefghijklmnop")
    chunks = generator.build_chunks(section)

    assert len(chunks) == 3
    assert chunks[0]["text"] == "abcdefgh"
    assert chunks[1]["text"].startswith("gh"), "chunks should overlap by two characters"
    assert chunks[0]["metadata"]["offset"] == 0
    assert chunks[1]["metadata"]["offset"] == 6


def test_build_chunks_handles_empty_text() -> None:
    generator = HelpVectorGenerator(chunk_size=5, chunk_overlap=1)
    section = make_section("   \n\t")
    assert generator.build_chunks(section) == []


def test_invalid_chunk_configuration() -> None:
    with pytest.raises(ValueError):
        HelpVectorGenerator(chunk_size=0, chunk_overlap=0)
    with pytest.raises(ValueError):
        HelpVectorGenerator(chunk_size=10, chunk_overlap=10)
    with pytest.raises(ValueError):
        HelpVectorGenerator(chunk_size=10, chunk_overlap=-1)
