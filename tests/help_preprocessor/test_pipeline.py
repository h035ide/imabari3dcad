from __future__ import annotations

from pathlib import Path

import json

from help_preprocessor.config import HelpPreprocessorConfig
from help_preprocessor.pipeline import HelpPreprocessorPipeline
from help_preprocessor.schemas import HelpCategory, HelpSection


def _create_html(path: Path, name: str, *, encoding: str = "shift_jis") -> None:
    html_content = "<html><body>テスト</body></html>".encode(encoding)
    (path / f"{name}.html").write_bytes(html_content)


def _create_index(path: Path) -> Path:
    index_text = "*Top\nTopic One (topic_one)\n"
    index_path = path / "index.txt"
    index_path.write_text(index_text, encoding="shift_jis")
    return index_path


class _TestablePipeline(HelpPreprocessorPipeline):
    def __init__(self, *args, sections: list[HelpSection] | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._test_sections = sections or []

    def _iter_sections(self, root: HelpCategory):  # type: ignore[override]
        yield from self._test_sections


def test_pipeline_builds_and_caches(tmp_path: Path) -> None:
    source_root = tmp_path / "help"
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "out"
    source_root.mkdir()
    cache_dir.mkdir()
    output_dir.mkdir()

    index_path = _create_index(source_root)
    _create_html(source_root, "topic_one")

    config = HelpPreprocessorConfig(
        source_root=source_root,
        cache_dir=cache_dir,
        output_dir=output_dir,
        index_file=index_path,
    )

    fake_section = HelpSection(
        section_id="topic_one#intro",
        title="Intro",
        content="This is a sample section for vector chunks.",
        anchors=["intro"],
        links=[],
        media=[],
    )

    pipeline = _TestablePipeline(config, sections=[fake_section])

    result = pipeline.build_only()

    assert isinstance(result.artifacts.root_category, HelpCategory)
    assert (cache_dir / "index_parse.json").exists()
    assert result.graph_nodes  # at least root node
    assert result.vector_chunks  # synthetic section produced chunk

    # Mutate index to ensure cache is used on second call
    index_path.write_text("*Changed\nOther\n", encoding="shift_jis")
    cached = pipeline.build_only()
    assert cached.artifacts.root_category.children[0].name == "Top"

    data = json.loads((cache_dir / "index_parse.json").read_text(encoding="utf-8"))
    assert data["diagnostics"]["html_samples"]


def test_pipeline_storage_integration(tmp_path: Path) -> None:
    source_root = tmp_path / "help"
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "out"
    source_root.mkdir()
    cache_dir.mkdir()
    output_dir.mkdir()

    index_path = _create_index(source_root)
    _create_html(source_root, "topic_one")

    config = HelpPreprocessorConfig(
        source_root=source_root,
        cache_dir=cache_dir,
        output_dir=output_dir,
        index_file=index_path,
    )

    class StubNeo4jLoader:
        def __init__(self) -> None:
            self.calls: list[tuple[list[dict], list[dict]]] = []

        def upsert(self, nodes: list[dict], relationships: list[dict]) -> None:
            self.calls.append((nodes, relationships))

    class StubChromaLoader:
        def __init__(self) -> None:
            self.calls: list[list[dict]] = []

        def upsert(self, chunks: list[dict]) -> None:
            self.calls.append(chunks)

    class StubGraphBuilder:
        def build_nodes(self, root: HelpCategory) -> list[dict]:
            return [{"id": "category:root", "labels": ["HelpCategory"], "properties": {"category_id": "root"}}]

        def build_relationships(self, root: HelpCategory) -> list[dict]:
            return []

    class StubVectorGenerator:
        def build_chunks(self, section: HelpSection) -> list[dict]:
            return [{"id": "chunk-1", "text": "hello", "metadata": {"section_id": section.section_id}}]

    neo4j_stub = StubNeo4jLoader()
    chroma_stub = StubChromaLoader()
    sample_section = HelpSection(
        section_id="topic_one#intro",
        title="Intro",
        content="text",
        anchors=[],
        links=[],
        media=[],
    )
    pipeline = _TestablePipeline(
        config,
        graph_builder=StubGraphBuilder(),
        vector_generator=StubVectorGenerator(),
        neo4j_loader=neo4j_stub,
        chroma_loader=chroma_stub,
        sections=[sample_section],
    )

    result = pipeline.run(dry_run=False)

    assert neo4j_stub.calls, "Neo4j loader should receive payloads"
    assert chroma_stub.calls, "Chroma loader should receive payloads"
    assert result.graph_nodes
    assert result.vector_chunks


def test_pipeline_dry_run_skips_storage(tmp_path: Path) -> None:
    source_root = tmp_path / "help"
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "out"
    source_root.mkdir()
    cache_dir.mkdir()
    output_dir.mkdir()

    index_path = _create_index(source_root)
    _create_html(source_root, "topic_one")

    config = HelpPreprocessorConfig(
        source_root=source_root,
        cache_dir=cache_dir,
        output_dir=output_dir,
        index_file=index_path,
    )

    class RecordingLoader:
        def __init__(self) -> None:
            self.calls = 0

        def upsert(self, *_args) -> None:
            self.calls += 1

    loader = RecordingLoader()
    pipeline = _TestablePipeline(config, neo4j_loader=loader, chroma_loader=loader, sections=[])

    pipeline.run(dry_run=True)
    assert loader.calls == 0
