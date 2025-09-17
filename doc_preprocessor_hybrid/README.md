# Hybrid Preprocessing Pipeline

This module builds a two-stage preprocessing flow for the EVO.SHIP API documents.

1. **Deterministic extraction**
   - Parse `api.txt` into object/function definitions with parameters and return metadata.
   - Parse `api_arg.txt` into normalized type descriptions.
   - Produce a baseline JSON that follows the existing `type_definitions` / `api_entries` schema.
2. **Targeted LLM enrichment (optional)**
   - Send only ambiguous entries (missing descriptions, unclear categories, etc.) to an LLM.
   - Merge the edited fragments back into the baseline JSON while preserving traceability.
3. **Structured outputs**
 - `structured_api.json`: the enriched schema-aligned view.
 - `graph_payload.json`: triples + node metadata ready for Neo4j ingestion.
 - `vector_chunks.jsonl`: text chunks for vector DB construction.

The deterministic layer reuses the rule-based strengths of the current pipeline, while the second stage keeps the LLM usage scoped and auditable.

## Usage

```bash
python -m doc_preprocessor_hybrid.cli --api-doc data/src/api.txt --api-arg data/src/api_arg.txt --output-dir doc_preprocessor_hybrid/out
```

Add `--llm` (with a valid `OPENAI_API_KEY`) to enable the enrichment step.
