from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import PipelineConfig
from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hybrid EVO.SHIP API preprocessing pipeline")
    parser.add_argument("--api-doc", default="data/src/api.txt", help="Path to api.txt")
    parser.add_argument("--api-arg", default="data/src/api_arg.txt", help="Path to api_arg.txt")
    parser.add_argument(
        "--output-dir",
        default="doc_preprocessor_hybrid/out",
        help="Output directory for generated artifacts",
    )
    parser.add_argument("--llm", action="store_true", help="Enable LLM enrichment phase")
    parser.add_argument("--model", default=None, help="Override OpenAI model id")
    parser.add_argument("--store-neo4j", action="store_true", help="Persist results into Neo4j using env credentials")
    parser.add_argument("--store-chroma", action="store_true", help="Persist vector chunks into ChromaDB")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without writing files")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = PipelineConfig(
        api_doc_path=Path(args.api_doc),
        api_arg_path=Path(args.api_arg),
        output_dir=Path(args.output_dir),
    )

    model_overrides = {"model": args.model} if args.model else None

    if args.dry_run:
        preview = {
            "api_doc": str(config.api_doc_path),
            "api_arg": str(config.api_arg_path),
            "output_dir": str(config.output_dir),
            "llm": args.llm,
            "model": args.model,
            "store_neo4j": args.store_neo4j,
            "store_chroma": args.store_chroma,
        }
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return 0

    result = run_pipeline(
        config=config,
        use_llm=args.llm,
        model_overrides=model_overrides,
        store_neo4j=args.store_neo4j,
        store_chroma=args.store_chroma,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
