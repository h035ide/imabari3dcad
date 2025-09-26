from pathlib import Path

import json

from help_preprocessor.config import HelpPreprocessorConfig
from help_preprocessor.pipeline import HelpPreprocessorPipeline


def _create_help_source(tmp_path: Path) -> tuple[Path, Path, Path]:
    source_root = tmp_path / "help"
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "out"
    source_root.mkdir()
    cache_dir.mkdir()
    output_dir.mkdir()
    media_dir = source_root / "media"
    media_dir.mkdir()
    (media_dir / "image.png").write_bytes(b"fake")

    html_content = (
        '<html><head><title>Doc Title</title></head><body>'
        '<p>Intro text</p>'
        '<h2 id="overview">Overview</h2><p>Overview text</p>'
        '<h3>Details</h3><p>Details text <img src="media/image.png" /></p>'
        '</body></html>'
    )
    (source_root / "topic_one.html").write_bytes(html_content.encode("shift_jis"))

    index_text = '*Top\nTopic One (topic_one)\n'
    index_path = source_root / "index.txt"
    index_path.write_bytes(index_text.encode("shift_jis"))

    return source_root, cache_dir, output_dir


def _build_config(source_root: Path, cache_dir: Path, output_dir: Path) -> HelpPreprocessorConfig:
    return HelpPreprocessorConfig(
        source_root=source_root,
        cache_dir=cache_dir,
        output_dir=output_dir,
        index_file=source_root / "index.txt",
    )


def test_pipeline_builds_and_caches(tmp_path: Path) -> None:
    source_root, cache_dir, output_dir = _create_help_source(tmp_path)
    config = _build_config(source_root, cache_dir, output_dir)

    pipeline = HelpPreprocessorPipeline(config)
    result = pipeline.build_only()

    assert result.graph_nodes
    assert result.vector_chunks
    assert (cache_dir / "index_parse.json").exists()

    mutated = '*Changed\nOther\n'
    (source_root / "index.txt").write_bytes(mutated.encode("shift_jis"))
    cached = pipeline.build_only()
    assert cached.artifacts.root_category.children[0].name == "Top"

    data = json.loads((cache_dir / "index_parse.json").read_text(encoding="utf-8"))
    assert data["diagnostics"]["html_samples"]


def test_pipeline_storage_integration(tmp_path: Path) -> None:
    source_root, cache_dir, output_dir = _create_help_source(tmp_path)
    config = _build_config(source_root, cache_dir, output_dir)

    class RecordingNeo4j:
        def __init__(self) -> None:
            self.calls: list[tuple[list[dict], list[dict]]] = []

        def upsert(self, nodes: list[dict], relationships: list[dict]) -> None:
            self.calls.append((nodes, relationships))

    class RecordingChroma:
        def __init__(self) -> None:
            self.calls: list[list[dict]] = []

        def upsert(self, chunks: list[dict]) -> None:
            self.calls.append(chunks)

    neo4j_loader = RecordingNeo4j()
    chroma_loader = RecordingChroma()
    pipeline = HelpPreprocessorPipeline(config, neo4j_loader=neo4j_loader, chroma_loader=chroma_loader)

    result = pipeline.run(dry_run=False)

    assert neo4j_loader.calls
    assert chroma_loader.calls
    assert result.graph_nodes
    assert result.vector_chunks


def test_pipeline_dry_run_skips_storage(tmp_path: Path) -> None:
    source_root, cache_dir, output_dir = _create_help_source(tmp_path)
    config = _build_config(source_root, cache_dir, output_dir)

    class RecordingLoader:
        def __init__(self) -> None:
            self.calls = 0

        def upsert(self, *_args) -> None:
            self.calls += 1

    loader = RecordingLoader()
    pipeline = HelpPreprocessorPipeline(config, neo4j_loader=loader, chroma_loader=loader)
    pipeline.run(dry_run=True)

    assert loader.calls == 0


