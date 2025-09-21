from __future__ import annotations

"""Command line interface for the help preprocessor."""

import argparse
import logging
from pathlib import Path
from typing import Sequence

from .config import HelpPreprocessorConfig, load_config_from_env
from .html_parser import HelpHTMLParser
from .pipeline import HelpPreprocessorPipeline


def build_parser() -> argparse.ArgumentParser:
    """Create an argument parser for the help preprocessor CLI."""

    parser = argparse.ArgumentParser(description="Process EVOSHIP help documentation.")
    parser.add_argument("source", nargs="?", help="Path to the root of the EVOSHIP help bundle.")
    parser.add_argument("--index", help="Optional index.txt path overriding the default location.")
    parser.add_argument("--dry-run", action="store_true", help="Run the pipeline without storage writes.")
    parser.add_argument(
        "--log-level",
        default=None,
        help="Override log level (defaults to configuration value).",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=3,
        help="Maximum number of HTML files to normalize during dry-run mode.",
    )
    return parser


def _apply_cli_overrides(config: HelpPreprocessorConfig, args: argparse.Namespace) -> HelpPreprocessorConfig:
    """Return a derived config reflecting CLI argument overrides."""

    source_root = Path(args.source) if args.source else config.source_root
    index_file = Path(args.index) if args.index else config.index_file
    log_level = args.log_level or config.log_level

    return HelpPreprocessorConfig(
        source_root=source_root,
        cache_dir=config.cache_dir,
        output_dir=config.output_dir,
        index_file=index_file,
        encoding=config.encoding,
        target_encoding=config.target_encoding,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        log_level=log_level,
        openai_model=config.openai_model,
        chroma_collection=config.chroma_collection,
        neo4j_uri=config.neo4j_uri,
        neo4j_username=config.neo4j_username,
        neo4j_password=config.neo4j_password,
    )


def _configure_logging(level_name: str) -> None:
    """Configure root logging to the requested level."""

    resolved = getattr(logging, level_name.upper(), None) if level_name else logging.INFO
    if not isinstance(resolved, int):  # pragma: no cover - defensive branch
        resolved = logging.INFO
    logging.basicConfig(level=resolved)


def _dry_run_normalize(config: HelpPreprocessorConfig, limit: int) -> None:
    """Normalize a sample of HTML files and log diagnostics."""

    html_files = sorted(config.source_root.rglob("*.html"))[:limit]
    if not html_files:
        logging.warning("No HTML files found under %s", config.source_root)
        return

    parser = HelpHTMLParser(config.source_root, encoding=config.encoding)
    for candidate in html_files:
        normalized, diag = parser.read_normalized_html(candidate)
        logging.info(
            "Normalized %s (encoding=%s, fallback=%s, BOM=%s)",
            candidate,
            diag.selected_encoding,
            diag.fallback_used,
            diag.had_bom,
        )
        logging.debug("Sample content: %s", normalized[:200])


def main(argv: Sequence[str] | None = None) -> None:  # pragma: no cover - thin wrapper
    """Entry point for command line execution."""

    parser = build_parser()
    args = parser.parse_args(argv)

    base_config = load_config_from_env()
    config = _apply_cli_overrides(base_config, args)

    _configure_logging(config.log_level)

    pipeline = HelpPreprocessorPipeline(config)

    if args.dry_run:
        _dry_run_normalize(config, args.sample_limit)
        return

    pipeline.run(dry_run=args.dry_run)
