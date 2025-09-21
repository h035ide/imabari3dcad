from pathlib import Path

import json

from help_preprocessor.pipeline import HelpPreprocessorPipeline, ParsedArtifacts
from help_preprocessor.config import HelpPreprocessorConfig
from help_preprocessor.schemas import HelpCategory


def _create_html(path: Path, name: str, *, encoding: str = "shift_jis") -> None:
    html_content = "<html><body>テスト</body></html>".encode(encoding)
    (path / f"{name}.html").write_bytes(html_content)


def _create_index(path: Path) -> Path:
    index_text = "*Top\nTopic One (topic_one)\n"
    index_path = path / "index.txt"
    index_path.write_text(index_text, encoding="shift_jis")
    return index_path


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

    pipeline = HelpPreprocessorPipeline(config)
    artifacts = pipeline.build_only()

    assert isinstance(artifacts.root_category, HelpCategory)
    assert (cache_dir / "index_parse.json").exists()

    # Mutate index to ensure cache is used on second call
    index_path.write_text("*Changed\nOther\n", encoding="shift_jis")
    cached = pipeline.build_only()
    assert cached.root_category.children[0].name == "Top"

    data = json.loads((cache_dir / "index_parse.json").read_text(encoding="utf-8"))
    assert data["diagnostics"]["html_samples"]
