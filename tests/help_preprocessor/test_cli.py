from pathlib import Path
import os
import json
import subprocess
import sys

from help_preprocessor.config import HelpPreprocessorConfig
from help_preprocessor.pipeline import HelpPreprocessorPipeline


def _create_sample_help(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "index.txt").write_text("*Top\nTopic One (topic_one)\n", encoding="shift_jis")
    (root / "topic_one.html").write_text("<html><body>トピック</body></html>", encoding="shift_jis")


def test_cli_dry_run_creates_cache(tmp_path: Path) -> None:
    source_root = tmp_path / "help"
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "out"
    _create_sample_help(source_root)

    env = os.environ.copy()
    env.update(
        {
            "HELP_SOURCE_ROOT": str(source_root),
            "HELP_CACHE_DIR": str(cache_dir),
            "HELP_OUTPUT_DIR": str(output_dir),
            "HELP_LOG_LEVEL": "INFO",
        }
    )

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
    pipeline.run(dry_run=True)

    cache_file = cache_dir / "index_parse.json"
    assert cache_file.exists()
    payload = json.loads(cache_file.read_text(encoding="utf-8"))
    assert payload["diagnostics"].get("html_samples")
    assert "index_errors" in payload["diagnostics"]
