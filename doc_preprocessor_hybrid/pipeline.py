from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from .config import PipelineConfig
from .graph_builder import build_graph_payload
from .llm_enricher import enrich_bundle
from .rule_parser import dump_bundle, generate_vector_chunks, parse_api_documents


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
    bundle = parse_api_documents(cfg.api_doc_path, cfg.api_arg_path)

    audit = enrich_bundle(bundle, enabled=use_llm, model_config=model_overrides)

    dump_bundle(bundle, cfg.structured_output)

    graph_payload = build_graph_payload(bundle)
    _write_graph(graph_payload, cfg.graph_output)

    vector_records = list(generate_vector_chunks(bundle.api_entries))
    _write_jsonl(vector_records, cfg.vector_output)

    return {
        "structured_output": str(cfg.structured_output),
        "graph_output": str(cfg.graph_output),
        "vector_output": str(cfg.vector_output),
        "audit": audit,
    }
