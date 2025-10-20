from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from .config import PipelineConfig
from .graph_builder import build_graph_payload
from .llm_enricher import enrich_bundle
from .logging_config import setup_logging, get_logger
from .rule_parser import (
    dump_bundle,
    generate_vector_chunks,
    load_bundle,
    parse_api_documents,
)
from .storage.chroma_loader import ChromaIngestError, store_vectors
from .storage.config import StorageConfig
from .storage.neo4j_loader import store_bundle as store_bundle_in_neo4j


def _write_jsonl(records, path: Path) -> None:
    logger = get_logger("pipeline._write_jsonl")
    logger.debug(f"Writing {len(records)} records to {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    logger.info(f"Successfully wrote {len(records)} records to {path}")


def _write_graph(payload: Dict[str, object], path: Path) -> None:
    logger = get_logger("pipeline._write_graph")
    logger.debug(f"Writing graph payload to {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Successfully wrote graph payload to {path}")


def run_pipeline(
    config: Optional[PipelineConfig] = None,
    use_llm: bool = False,
    model_overrides: Optional[Dict[str, object]] = None,
    store_neo4j: bool = False,
    store_chroma: bool = False,
) -> Dict[str, object]:
    cfg = config or PipelineConfig()

    # ログ設定を初期化
    logger = setup_logging(
        log_level=cfg.log_level, log_file=cfg.log_file, log_dir=cfg.output_dir
    )

    logger.info("=" * 60)
    logger.info("Starting pipeline execution")
    logger.info(f"Configuration: {cfg}")
    logger.info(f"Use LLM: {use_llm}")
    logger.info(f"Store Neo4j: {store_neo4j}")
    logger.info(f"Store Chroma: {store_chroma}")
    logger.info("=" * 60)

    # Always re-parse and overwrite outputs
    audit: list[Dict[str, object]] = []
    bundle_source = "parsed"
    used_existing_structured = False

    logger.info("Parsing API documents (force re-parse)...")
    logger.info(f"API doc path: {cfg.api_doc_path}")
    logger.info(f"API arg path: {cfg.api_arg_path}")
    bundle = parse_api_documents(cfg.api_doc_path, cfg.api_arg_path)
    logger.info(
        f"Parsed bundle with {len(bundle.api_entries)} API entries "
        f"and {len(bundle.type_definitions)} type definitions"
    )
    logger.info(f"Saving structured output to: {cfg.structured_output}")
    dump_bundle(bundle, cfg.structured_output)
    bundle_source = "parsed"

    if use_llm:
        logger.info("Starting LLM enrichment phase...")
        api_doc_text = (
            cfg.api_doc_path.read_text(encoding="utf-8")
            if cfg.api_doc_path.exists()
            else None
        )
        api_arg_text = (
            cfg.api_arg_path.read_text(encoding="utf-8")
            if cfg.api_arg_path.exists()
            else None
        )
        logger.info(
            f"API doc text length: {len(api_doc_text) if api_doc_text else 0} characters"
        )
        logger.info(
            f"API arg text length: {len(api_arg_text) if api_arg_text else 0} characters"
        )

        audit = enrich_bundle(
            bundle,
            enabled=True,
            model_config=model_overrides,
            api_doc_text=api_doc_text,
            api_arg_text=api_arg_text,
        )
        logger.info(f"LLM enrichment completed with {len(audit)} audit entries")
        logger.info(f"Saving enriched bundle to: {cfg.structured_output_enriched}")
        dump_bundle(bundle, cfg.structured_output_enriched)
        bundle_source = "structured_api_enriched"
    else:
        logger.info("Skipping LLM enrichment phase")
        audit = []

    logger.info("Building graph payload...")
    graph_payload = build_graph_payload(bundle)
    logger.info(
        f"Graph payload contains {len(graph_payload.get('nodes', []))} nodes "
        f"and {len(graph_payload.get('relationships', []))} relationships"
    )
    _write_graph(graph_payload, cfg.graph_output)

    logger.info("Generating vector chunks...")
    vector_records = list(generate_vector_chunks(bundle.api_entries))
    logger.info(f"Generated {len(vector_records)} vector chunks")
    _write_jsonl(vector_records, cfg.vector_output)

    structured_path = (
        cfg.structured_output_enriched if use_llm else cfg.structured_output
    )

    storage_results: Dict[str, object] = {}
    if store_neo4j or store_chroma:
        logger.info("Starting storage operations...")
        storage_config = StorageConfig.load()
        if store_neo4j:
            logger.info("Storing data to Neo4j...")
            if storage_config.neo4j.enabled:
                try:
                    storage_results["neo4j"] = store_bundle_in_neo4j(
                        bundle, storage_config.neo4j
                    )
                    logger.info("Successfully stored data to Neo4j")
                except Exception as exc:  # pragma: no cover - connection errors
                    logger.error(f"Failed to store data to Neo4j: {exc}")
                    storage_results["neo4j"] = {"error": str(exc)}
            else:
                logger.warning(
                    "Neo4j storage disabled: NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD are required"
                )
                storage_results["neo4j"] = {
                    "error": "NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD are required",
                }
        if store_chroma:
            logger.info("Storing vectors to ChromaDB...")
            if storage_config.chroma.enabled:
                try:
                    storage_results["chroma"] = store_vectors(
                        bundle, cfg.vector_output, storage_config.chroma
                    )
                    logger.info("Successfully stored vectors to ChromaDB")
                except (ChromaIngestError, FileNotFoundError) as exc:
                    logger.error(f"Failed to store vectors to ChromaDB: {exc}")
                    storage_results["chroma"] = {"error": str(exc)}
                except Exception as exc:  # pragma: no cover
                    logger.error(f"Unexpected error storing vectors to ChromaDB: {exc}")
                    storage_results["chroma"] = {"error": str(exc)}
            else:
                logger.warning(
                    "ChromaDB storage disabled: CHROMA_COLLECTION must be set"
                )
                storage_results["chroma"] = {
                    "error": "CHROMA_COLLECTION must be set",
                }

    result: Dict[str, object] = {
        "raw_structured_output": str(cfg.structured_output),
        "structured_output": str(structured_path),
        "graph_output": str(cfg.graph_output),
        "vector_output": str(cfg.vector_output),
        "audit": audit,
        "bundle_source": bundle_source,
        "used_existing_structured": used_existing_structured,
    }
    if storage_results:
        result["storage"] = storage_results

    logger.info("=" * 60)
    logger.info("Pipeline execution completed successfully")
    logger.info("Output files:")
    logger.info(f"  - Structured output: {structured_path}")
    logger.info(f"  - Graph output: {cfg.graph_output}")
    logger.info(f"  - Vector output: {cfg.vector_output}")
    logger.info(f"  - Log file: {cfg.log_file}")
    logger.info(f"Bundle source: {bundle_source}")
    logger.info(f"Used existing structured: {used_existing_structured}")
    if audit:
        logger.info(f"Audit entries: {len(audit)}")
    if storage_results:
        logger.info(f"Storage results: {storage_results}")
    logger.info("=" * 60)

    return result
