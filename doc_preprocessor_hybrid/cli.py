from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import PipelineConfig
from .logging_config import setup_logging
from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Hybrid EVO.SHIP API preprocessing pipeline"
    )
    parser.add_argument("--api-doc", default="data/src/api.txt", help="Path to api.txt")
    parser.add_argument(
        "--api-arg", default="data/src/api_arg.txt", help="Path to api_arg.txt"
    )
    parser.add_argument(
        "--output-dir",
        default="doc_preprocessor_hybrid/out",
        help="Output directory for generated artifacts",
    )
    parser.add_argument(
        "--llm", action="store_true", help="Enable LLM enrichment phase"
    )
    parser.add_argument("--model", default=None, help="Override OpenAI model id")
    parser.add_argument(
        "--store-neo4j",
        action="store_true",
        help="Persist results into Neo4j using env credentials",
    )
    parser.add_argument(
        "--store-chroma",
        action="store_true",
        help="Persist vector chunks into ChromaDB",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print plan without writing files"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level",
    )
    parser.add_argument(
        "--disable-debug-logging", action="store_true", help="Disable debug logging"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # ログレベルを設定
    log_level = args.log_level
    if args.disable_debug_logging:
        log_level = "WARNING"

    config = PipelineConfig(
        api_doc_path=Path(args.api_doc),
        api_arg_path=Path(args.api_arg),
        output_dir=Path(args.output_dir),
        log_level=log_level,
        enable_debug_logging=not args.disable_debug_logging,
    )

    # ログ設定を初期化
    logger = setup_logging(
        log_level=config.log_level, log_file=config.log_file, log_dir=config.output_dir
    )

    logger.info("=" * 60)
    logger.info("Starting CLI execution")
    logger.info(f"Arguments: {vars(args)}")
    logger.info("=" * 60)

    model_overrides = {"model": args.model} if args.model else None

    if args.dry_run:
        logger.info("Dry run mode - generating preview only")
        preview = {
            "api_doc": str(config.api_doc_path),
            "api_arg": str(config.api_arg_path),
            "output_dir": str(config.output_dir),
            "llm": args.llm,
            "model": args.model,
            "store_neo4j": args.store_neo4j,
            "store_chroma": args.store_chroma,
            "log_level": config.log_level,
            "log_file": str(config.log_file),
        }
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        logger.info("Dry run completed successfully")
        return 0

    try:
        result = run_pipeline(
            config=config,
            use_llm=args.llm,
            model_overrides=model_overrides,
            store_neo4j=args.store_neo4j,
            store_chroma=args.store_chroma,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        logger.info("CLI execution completed successfully")
        return 0
    except Exception as exc:
        logger.error(f"CLI execution failed: {exc}")
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
