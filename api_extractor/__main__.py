"""Command line interface for the EvoShip API extractor."""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from .api_parser import ApiExtractor
from .llm_pipeline import LLMApiExtractor, LLMExtractionConfig
from .type_parser import parse_type_definitions


def parse_args() -> argparse.Namespace:
    defaults = LLMExtractionConfig()

    parser = argparse.ArgumentParser(
        description="Extract structured EvoShip API metadata."
    )
    parser.add_argument("--api-doc", type=Path, required=True, help="Path to api.txt")
    parser.add_argument(
        "--api-arg", type=Path, required=True, help="Path to api_arg.txt"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Destination JSON file. Defaults to stdout if omitted.",
    )
    parser.add_argument(
        "--indent", type=int, default=2, help="Indentation level for JSON output."
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Use the LLM-based extractor instead of the legacy regex parser.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=defaults.model,
        help="LLM model identifier when using --llm.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=defaults.chunk_size,
        help="Chunk size for LLM extraction.",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=defaults.chunk_overlap,
        help="Chunk overlap for LLM extraction.",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    api_text = args.api_doc.read_text(encoding="utf-8")
    type_text = args.api_arg.read_text(encoding="utf-8")
    type_defs = parse_type_definitions(type_text)
    if args.llm:
        config = LLMExtractionConfig(
            model=args.model,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
        extractor = LLMApiExtractor(type_defs, config)
        entries = extractor.extract(api_text)
    else:
        extractor = ApiExtractor(type_defs)
        entries = extractor.parse_api_text(api_text)
    result = {
        "type_definitions": [asdict(definition) for definition in type_defs],
        "api_entries": [
            {
                "entry_type": entry.entry_type,
                "name": entry.name,
                "description": entry.description,
                "category": entry.category,
                "params": [
                    {
                        "name": param.name,
                        "position": param.position,
                        "type": param.type,
                        "description": param.description,
                        "is_required": param.is_required,
                        "default_value": param.default_value,
                        "array_info": (
                            asdict(param.array_info) if param.array_info else None
                        ),
                    }
                    for param in entry.params
                ],
                "returns": (
                    {
                        "type": entry.returns.type if entry.returns else None,
                        "description": (
                            entry.returns.description if entry.returns else None
                        ),
                        "is_array": entry.returns.is_array if entry.returns else False,
                    }
                    if entry.returns
                    else None
                ),
                "notes": entry.notes,
                "implementation_status": entry.implementation_status,
                "properties": [
                    {
                        "name": prop.name,
                        "type": prop.type,
                        "description": prop.description,
                        "array_info": (
                            asdict(prop.array_info) if prop.array_info else None
                        ),
                    }
                    for prop in entry.properties
                ],
            }
            for entry in entries
        ],
    }
    output: Optional[Path] = args.output
    if output:
        output.write_text(
            json.dumps(result, ensure_ascii=False, indent=args.indent), encoding="utf-8"
        )
    else:
        print(json.dumps(result, ensure_ascii=False, indent=args.indent))


if __name__ == "__main__":
    main()
