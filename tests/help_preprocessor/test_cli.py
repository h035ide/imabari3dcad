from pathlib import Path
import os
import json
import subprocess
import sys
import pytest

from help_preprocessor import cli
from help_preprocessor.config import HelpPreprocessorConfig
from help_preprocessor.pipeline import HelpPreprocessorPipeline


def _create_sample_help(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "index.txt").write_text("*Top\nTopic One (topic_one)\n", encoding="shift_jis")
    html = '<html><body><p>Intro</p><h2>Overview</h2><p>Content</p></body></html>'
    (root / "topic_one.html").write_text(html, encoding="shift_jis")


def test_cli_dry_run_creates_cache(tmp_path: Path) -> None:
    source_root = tmp_path / "help"
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "out"
    _create_sample_help(source_root)

    env = os.environ.copy()
    env.update({
        "HELP_SOURCE_ROOT": str(source_root),
        "HELP_CACHE_DIR": str(cache_dir),
        "HELP_OUTPUT_DIR": str(output_dir),
        "HELP_LOG_LEVEL": "INFO",
    })

    result = subprocess.run(
        [sys.executable, "-m", "help_preprocessor.cli", "--dry-run", "--sample-limit", "1"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr

    config = HelpPreprocessorConfig(
        source_root=source_root,
        cache_dir=cache_dir,
        output_dir=output_dir,
        index_file=source_root / "index.txt",
    )
    pipeline = HelpPreprocessorPipeline(config)
    pipeline_result = pipeline.run(dry_run=True)

    cache_file = cache_dir / "index_parse.json"
    assert cache_file.exists()
    payload = json.loads(cache_file.read_text(encoding="utf-8"))
    assert payload["diagnostics"].get("html_samples")
    assert "index_errors" in payload["diagnostics"]
    assert pipeline_result.graph_nodes


def test_cli_wires_storage_backends(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    source_root = tmp_path / "help"
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "out"
    persist_dir = tmp_path / "persist"

    _create_sample_help(source_root)
    cache_dir.mkdir()
    output_dir.mkdir()
    persist_dir.mkdir()

    monkeypatch.setenv("HELP_SOURCE_ROOT", str(source_root))
    monkeypatch.setenv("HELP_CACHE_DIR", str(cache_dir))
    monkeypatch.setenv("HELP_OUTPUT_DIR", str(output_dir))
    monkeypatch.setenv("HELP_LOG_LEVEL", "INFO")
    monkeypatch.setenv("HELP_NEO4J_URI", "bolt://example")
    monkeypatch.setenv("HELP_NEO4J_USERNAME", "neo4j")
    monkeypatch.setenv("HELP_NEO4J_PASSWORD", "secret")
    monkeypatch.setenv("HELP_NEO4J_DATABASE", "help-db")
    monkeypatch.setenv("HELP_CHROMA_COLLECTION", "evoship-help")
    monkeypatch.setenv("HELP_CHROMA_PERSIST_DIR", str(persist_dir))

    created: dict[str, object] = {}

    class RecordingNeo4j:
        def __init__(
            self,
            uri: str,
            username: str,
            password: str,
            database: str | None = None,
            *,
            driver=None,
        ) -> None:
            self.params = {
                "uri": uri,
                "username": username,
                "password": password,
                "database": database,
            }
            self.upserts: list[tuple[list[dict], list[dict]]] = []
            self.closed = False
            created["neo4j"] = self

        def upsert(self, nodes: list[dict], relationships: list[dict]) -> None:
            self.upserts.append((nodes, relationships))

        def close(self) -> None:
            self.closed = True

    class RecordingChroma:
        def __init__(
            self,
            collection_name: str,
            persist_directory: str | None = None,
            *,
            client=None,
            metadata=None,
        ) -> None:
            self.params = {
                "collection": collection_name,
                "persist_directory": persist_directory,
            }
            self.upserts: list[list[dict]] = []
            created["chroma"] = self

        def upsert(self, chunks: list[dict]) -> None:
            self.upserts.append(chunks)

    monkeypatch.setattr(cli, "HelpNeo4jLoader", RecordingNeo4j)
    monkeypatch.setattr(cli, "HelpChromaLoader", RecordingChroma)

    cli.main([])

    neo4j = created.get("neo4j")
    chroma = created.get("chroma")
    assert neo4j is not None and chroma is not None
    assert neo4j.params["database"] == "help-db"
    assert chroma.params["persist_directory"] == str(persist_dir)
    assert neo4j.upserts, "Neo4j loader should receive data"
    assert chroma.upserts, "Chroma loader should receive data"
    assert getattr(neo4j, "closed", False) is True


