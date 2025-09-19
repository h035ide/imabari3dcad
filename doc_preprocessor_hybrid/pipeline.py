from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from .config import PipelineConfig
from .graph_builder import build_graph_payload
from .llm_enricher import enrich_bundle
from .rule_parser import dump_bundle, generate_vector_chunks, load_bundle, parse_api_documents


def _write_jsonl(records, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _write_graph(payload: Dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")



def run_pipeline(
    config: Optional[PipelineConfig] = None,
    use_llm: bool = False,
    model_overrides: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    cfg = config or PipelineConfig()

    bundle = None
    audit: list[Dict[str, object]] = []
    bundle_source = "parsed"
    used_existing_structured = False

    if not use_llm:
        existing_path: Path | None = None
        if cfg.structured_output_enriched.exists():
            existing_path = cfg.structured_output_enriched
            bundle_source = "structured_api_enriched"
        elif cfg.structured_output.exists():
            existing_path = cfg.structured_output
            bundle_source = "structured_api"
        if existing_path is not None:
            bundle = load_bundle(existing_path)
            used_existing_structured = True

    if bundle is None:
        bundle = parse_api_documents(cfg.api_doc_path, cfg.api_arg_path)
        dump_bundle(bundle, cfg.structured_output)
        bundle_source = "parsed"

    if use_llm:
        audit = enrich_bundle(bundle, enabled=True, model_config=model_overrides)
        dump_bundle(bundle, cfg.structured_output_enriched)
        bundle_source = "structured_api_enriched"
    else:
        audit = []

    graph_payload = build_graph_payload(bundle)
    _write_graph(graph_payload, cfg.graph_output)

    vector_records = list(generate_vector_chunks(bundle.api_entries))
    _write_jsonl(vector_records, cfg.vector_output)

    structured_path = (
        cfg.structured_output_enriched
        if use_llm or (used_existing_structured and cfg.structured_output_enriched.exists())
        else cfg.structured_output
    )

    return {
        "raw_structured_output": str(cfg.structured_output),
        "structured_output": str(structured_path),
        "graph_output": str(cfg.graph_output),
        "vector_output": str(cfg.vector_output),
        "audit": audit,
        "bundle_source": bundle_source,
        "used_existing_structured": used_existing_structured,
    }
