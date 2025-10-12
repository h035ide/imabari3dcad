"""structured_api/type_definitions.json を LlamaIndex 形式へ変換し Neo4j / Chroma に格納するユーティリティ."""

from __future__ import annotations

import argparse
import json
import datetime
import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, cast

import chromadb
from dotenv import load_dotenv
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.core.graph_stores.types import EntityNode, Relation
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.readers.json import JSONReader
from llama_index.vector_stores.chroma import ChromaVectorStore

LOGGER = logging.getLogger(__name__)

DEFAULT_JQ_SCHEMA = ".type_definitions[]"


def _legacy_load_type_definitions(json_path: Path) -> List[Dict[str, Any]]:
    with json_path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)
    definitions = payload.get("type_definitions", [])
    if not isinstance(definitions, list):
        raise ValueError("type_definitions キーがリストではありません")
    return definitions


def load_type_definitions(
    json_path: Path,
    *,
    jq_schema: str = DEFAULT_JQ_SCHEMA,
) -> Tuple[List[Dict[str, Any]], List[Document]]:
    if jq_schema.strip() == "":
        LOGGER.debug("Empty jq_schema provided; falling back to legacy loader")
        definitions = _legacy_load_type_definitions(json_path)
        return definitions, []

    if jq_schema.strip() != DEFAULT_JQ_SCHEMA:
        LOGGER.debug(
            "JSONReader は jq_schema をサポートしないため、指定値 %s を無視します",
            jq_schema,
        )

    reader = JSONReader()
    try:
        raw_documents = reader.load_data(input_file=str(json_path))
    except Exception as exc:  # pragma: no cover - runtime dependency on jq
        LOGGER.warning(
            "JSONReader load failed for %s (schema=%s): %s -- falling back to legacy loader",
            json_path,
            jq_schema,
            exc,
        )
        definitions = _legacy_load_type_definitions(json_path)
        return definitions, []

    definitions: List[Dict[str, Any]] = []
    for doc in raw_documents:
        payload: Dict[str, Any] | None = None
        text_payload = doc.text or ""
        candidate: Any
        if text_payload:
            try:
                candidate = json.loads(text_payload)
            except json.JSONDecodeError as exc:
                LOGGER.debug("Failed to decode JSONReader payload: %s", exc)
                candidate = None
        else:
            candidate = (
                doc.metadata.get("json_dict")
                if isinstance(doc.metadata, dict)
                else None
            )
        if isinstance(candidate, dict):
            payload = candidate
        if payload is None:
            LOGGER.debug("Skipping non-dict payload from JSONReader: %s", doc.metadata)
            continue
        source = payload.get("source")
        if not isinstance(source, dict):
            source = {"path": str(json_path)}
        else:
            source.setdefault("path", str(json_path))
        payload["source"] = source
        definitions.append(payload)

    if not definitions:
        LOGGER.warning(
            "JSONReader produced no usable type definitions for %s; using legacy loader",
            json_path,
        )
        definitions = _legacy_load_type_definitions(json_path)
        return definitions, raw_documents

    return definitions, raw_documents


def _normalize_property(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    return json.dumps(value, ensure_ascii=False)


def _format_examples(examples: Iterable[Any]) -> str:
    formatted: List[str] = []
    for example in examples:
        if isinstance(example, dict):
            parts = []
            if "value" in example:
                parts.append(f"値: {example['value']}")
            if "variant" in example:
                parts.append(f"種別: {example['variant']}")
            if "explanation" in example:
                parts.append(f"説明: {example['explanation']}")
            if not parts:
                parts.append(json.dumps(example, ensure_ascii=False))
            formatted.append("; ".join(parts))
        else:
            formatted.append(str(example))
    return "\n".join(formatted)


def build_documents(
    definitions: List[Dict[str, Any]],
    *,
    source_documents: List[Document] | None = None,
) -> List[Document]:
    documents: List[Document] = []
    for idx, typedef in enumerate(definitions):
        name = typedef.get("name", "未知")
        canonical = typedef.get("canonical_type")
        description = typedef.get("description", "")
        alias = typedef.get("alias") or []
        one_of = typedef.get("one_of") or []
        variants = typedef.get("variants") or []
        examples = typedef.get("examples") or []
        source = typedef.get("source") or {}

        lines = [f"型名: {name}"]
        if canonical:
            lines.append(f"正規化型: {canonical}")
        if description:
            lines.append(f"概要: {description}")
        if alias:
            lines.append("別名: " + ", ".join(map(str, alias)))
        if one_of:
            variant_lines = []
            for entry in one_of:
                if isinstance(entry, dict):
                    label = entry.get("id")
                    desc = entry.get("description")
                    if label and desc:
                        variant_lines.append(f"- {label}: {desc}")
                    elif label:
                        variant_lines.append(f"- {label}")
                    elif desc:
                        variant_lines.append(f"- {desc}")
                else:
                    variant_lines.append(f"- {entry}")
            if variant_lines:
                lines.append("one_of:\n" + "\n".join(variant_lines))
        if variants:
            variant_lines = []
            for entry in variants:
                if isinstance(entry, dict):
                    label = entry.get("id")
                    desc = entry.get("description")
                    if label and desc:
                        variant_lines.append(f"- {label}: {desc}")
                    elif label:
                        variant_lines.append(f"- {label}")
                    elif desc:
                        variant_lines.append(f"- {desc}")
                else:
                    variant_lines.append(f"- {entry}")
            if variant_lines:
                lines.append("variants:\n" + "\n".join(variant_lines))
        if examples:
            lines.append("例:\n" + _format_examples(examples))
        if source and isinstance(source, dict):
            text_value = source.get("text")
            if text_value:
                lines.append("原文:\n" + text_value)

        base_metadata = {
            "type": "type_definition",
            "name": name,
            "canonical_type": canonical or "",
            "source_path": source.get("path") if isinstance(source, dict) else "",
        }
        if source_documents and idx < len(source_documents):
            base_metadata = {**source_documents[idx].metadata, **base_metadata}

        content = "\n".join(lines)
        document = Document(text=content, metadata=base_metadata)
        try:
            document.excluded_embed_metadata_keys = ["source_path"]
            document.excluded_llm_metadata_keys = ["source_path"]
        except AttributeError:  # pragma: no cover - older LlamaIndex versions
            pass
        documents.append(document)
    return documents


def _create_llm_path_extractor(
    *, llm_model: str | None, temperature: float
) -> Any | None:
    try:
        from llama_index.extractors.simple_path import (  # type: ignore[attr-defined]
            LLMPath,
            SimpleLLMPathExtractor,
        )
    except (
        ImportError
    ):  # pragma: no cover - optional dependency path differs across versions
        try:
            from llama_index.extractors.relationships.simple_path import (  # type: ignore[attr-defined]
                LLMPath,
                SimpleLLMPathExtractor,
            )
        except ImportError:
            return None

    llm = None
    extractor_kwargs: Dict[str, Any] = {}
    if llm_model:
        try:
            from llama_index.llms.openai import (
                OpenAI as _OpenAILLM,
            )  # local import to avoid hard dependency
        except ImportError:  # pragma: no cover - optional dependency
            _OpenAILLM = None  # type: ignore[assignment]
        if _OpenAILLM is not None:
            llm = _OpenAILLM(model=llm_model, temperature=temperature)
        else:
            LOGGER.warning(
                "llama_index.llms.openai.OpenAI not available; SimpleLLMPathExtractor will use default LLM"
            )
    elif temperature:
        extractor_kwargs["llm_kwargs"] = {"temperature": temperature}

    try:
        llm_paths = [
            LLMPath(
                path=["name"], description="Extract the canonical type name if missing"
            ),
            LLMPath(path=["alias", "*"], description="List alternative labels"),
            LLMPath(
                path=["variants", "*", "id"],
                description="Enumerate variant identifiers",
            ),
            LLMPath(
                path=["one_of", "*", "id"], description="Enumerate one_of identifiers"
            ),
            LLMPath(
                path=["examples", "*", "value"],
                description="Surface canonical example values",
            ),
        ]
    except Exception as exc:  # pragma: no cover - handle signature drift
        LOGGER.debug("Failed to construct LLMPath definitions: %s", exc)
        return None

    try:
        if llm is not None:
            return SimpleLLMPathExtractor(
                llm_paths=llm_paths, llm=llm, **extractor_kwargs
            )
        return SimpleLLMPathExtractor(llm_paths=llm_paths, **extractor_kwargs)
    except TypeError as exc:
        LOGGER.debug("SimpleLLMPathExtractor signature mismatch: %s", exc)
        try:
            return SimpleLLMPathExtractor(llm_paths=llm_paths, llm=llm)
        except (
            Exception
        ) as inner_exc:  # pragma: no cover - optional dependency mismatch
            LOGGER.warning(
                "Unable to instantiate SimpleLLMPathExtractor: %s", inner_exc
            )
            return None
    except Exception as exc:  # pragma: no cover - e.g., missing API keys
        LOGGER.warning("Unable to instantiate SimpleLLMPathExtractor: %s", exc)
        return None


def _add_node(
    nodes: Dict[str, EntityNode],
    node_id: str,
    *,
    name: str,
    label: str,
    properties: Dict[str, Any],
) -> str:
    if node_id not in nodes:
        # Normalize and avoid overwriting the unique key property "id" during SET
        normalized_props = {
            key: value
            for key, value in (
                (k, _normalize_property(v)) for k, v in properties.items()
            )
            if value is not None and key != "id"
        }
        display_name = str(name)
        node = EntityNode(
            name=node_id,
            label=label,
            properties={**normalized_props},
        )
        node.properties.setdefault("display_name", display_name)
        nodes[node_id] = node
    return node_id


def _add_relation(
    relations: List[Relation],
    *,
    label: str,
    start_id: str,
    end_id: str,
    properties: Dict[str, Any] | None = None,
) -> None:
    payload = {
        key: value
        for key, value in (
            (k, _normalize_property(v)) for k, v in (properties or {}).items()
        )
        if value is not None
    }
    relations.append(
        Relation(
            label=label,
            source_id=start_id,
            target_id=end_id,
            properties=payload,
        )
    )


def build_graph_elements(
    definitions: List[Dict[str, Any]],
    *,
    documents: List[Document] | None = None,
    use_llm_extractor: bool = False,
    llm_model: str | None = None,
    llm_temperature: float = 0.0,
) -> Tuple[List[EntityNode], List[Relation]]:
    nodes: Dict[str, EntityNode] = {}
    relations: List[Relation] = []

    llm_enrichments: Dict[str, Any] = {}
    if use_llm_extractor and documents:
        extractor = _create_llm_path_extractor(
            llm_model=llm_model, temperature=llm_temperature
        )
        if extractor is not None:
            try:
                extraction_results = extractor.extract(documents)
            except (
                AttributeError
            ):  # pragma: no cover - different extractor API versions
                extraction_results = extractor(documents)  # type: ignore[misc]
            except Exception as exc:  # pragma: no cover - runtime dependency on LLMs
                LOGGER.warning("SimpleLLMPathExtractor failed: %s", exc)
                extraction_results = []
            if extraction_results:
                for doc, result in zip(documents, extraction_results):
                    doc_name = (
                        doc.metadata.get("name")
                        if isinstance(doc.metadata, dict)
                        else None
                    )
                    if not doc_name:
                        doc_name = (
                            doc.metadata.get("id")
                            if isinstance(doc.metadata, dict)
                            else None
                        )
                    if hasattr(result, "to_dict"):
                        payload = result.to_dict()
                    else:
                        payload = result
                    if doc_name and isinstance(payload, dict):
                        llm_enrichments[str(doc_name)] = payload
    elif use_llm_extractor:
        LOGGER.info(
            "SimpleLLMPathExtractor requested but unavailable; continuing without LLM assistance"
        )

    for typedef in definitions:
        name = typedef.get("name", "")
        if not name:
            continue
        node_id = f"type::{name}"
        description = typedef.get("description")
        canonical = typedef.get("canonical_type")
        raw_source = typedef.get("source")
        source = raw_source if isinstance(raw_source, dict) else {}
        base_properties: Dict[str, Any] = {
            "raw_name": name,
            "description": description,
            "canonical_type": canonical,
            "py_type": typedef.get("py_type"),
            "alias": typedef.get("alias"),
            "one_of": typedef.get("one_of"),
            "variants": typedef.get("variants"),
            "examples": typedef.get("examples"),
            "source_path": source.get("path"),
            "source_text": source.get("text"),
        }
        llm_payload = llm_enrichments.get(name)
        if llm_payload:
            base_properties["llm_extractions"] = llm_payload
        _add_node(
            nodes,
            node_id,
            name=name,
            label="TypeDefinition",
            properties=base_properties,
        )

        if canonical:
            canonical_id = f"canonical::{canonical}"
            _add_node(
                nodes,
                canonical_id,
                name=canonical,
                label="CanonicalType",
                properties={"value": canonical},
            )
            _add_relation(
                relations,
                label="HAS_CANONICAL_TYPE",
                start_id=node_id,
                end_id=canonical_id,
            )

        for alias in typedef.get("alias") or []:
            alias_str = str(alias)
            alias_id = f"alias::{alias_str}"
            _add_node(
                nodes,
                alias_id,
                name=alias_str,
                label="Alias",
                properties={"value": alias_str},
            )
            _add_relation(
                relations,
                label="HAS_ALIAS",
                start_id=node_id,
                end_id=alias_id,
            )

        for entry in typedef.get("one_of") or []:
            if isinstance(entry, dict):
                entry_id = (
                    entry.get("id")
                    or entry.get("description")
                    or json.dumps(entry, ensure_ascii=False)
                )
                desc = entry.get("description")
            else:
                entry_id = str(entry)
                desc = None
            variant_node_id = f"oneof::{name}::{entry_id}"
            _add_node(
                nodes,
                variant_node_id,
                name=str(entry_id),
                label="OneOfVariant",
                properties={"description": desc, "owner": name},
            )
            _add_relation(
                relations,
                label="HAS_VARIANT",
                start_id=node_id,
                end_id=variant_node_id,
            )

        for entry in typedef.get("variants") or []:
            if isinstance(entry, dict):
                entry_id = (
                    entry.get("id")
                    or entry.get("description")
                    or json.dumps(entry, ensure_ascii=False)
                )
                desc = entry.get("description")
            else:
                entry_id = str(entry)
                desc = None
            variant_node_id = f"variant::{name}::{entry_id}"
            _add_node(
                nodes,
                variant_node_id,
                name=str(entry_id),
                label="Variant",
                properties={"description": desc, "owner": name},
            )
            _add_relation(
                relations,
                label="HAS_VARIANT",
                start_id=node_id,
                end_id=variant_node_id,
            )

        examples = typedef.get("examples") or []
        for idx, example in enumerate(examples):
            if isinstance(example, dict):
                value = example.get("value")
                variant = example.get("variant")
                explanation = example.get("explanation")
                payload = {
                    "value": value,
                    "variant": variant,
                    "explanation": explanation,
                }
                name_token = value or json.dumps(example, ensure_ascii=False)
            else:
                payload = {"value": example}
                name_token = str(example)
            example_id = f"example::{name}::{idx}"
            _add_node(
                nodes,
                example_id,
                name=name_token,
                label="Example",
                properties={**payload, "owner": name},
            )
            _add_relation(
                relations,
                label="HAS_EXAMPLE",
                start_id=node_id,
                end_id=example_id,
            )

    return list(nodes.values()), relations


def build_triples(
    nodes: List[EntityNode],
    relations: List[Relation],
) -> List[Dict[str, Any]]:
    """Convert nodes/relations to simple triples for external export.

    Each triple dictionary contains stable identifiers and light metadata so that
    downstream systems (including raw Neo4j importers) can reconstruct links
    without needing LlamaIndex-specific classes.
    """
    node_by_id: Dict[str, EntityNode] = {n.id: n for n in nodes}
    triples: List[Dict[str, Any]] = []
    for rel in relations:
        src = node_by_id.get(rel.source_id)
        dst = node_by_id.get(rel.target_id)
        if not src or not dst:
            # Skip dangling relation if any
            continue
        triples.append(
            {
                "subject_id": src.id,
                "subject_label": src.label,
                "subject_name": src.name,
                "predicate": rel.label,
                "object_id": dst.id,
                "object_label": dst.label,
                "object_name": dst.name,
                "edge_properties": rel.properties or {},
            }
        )
    return triples


def format_triples_extracted(
    nodes: List[EntityNode],
    relations: List[Relation],
    *,
    sources_name: str,
) -> Dict[str, Any]:
    """Produce JSON compatible with the provided extracted_triples schema.

    Structure:
    {
      "timestamp": ISO8601,
      "sources": {
        <sources_name>: {
          "triples": [ {source, source_type, label, target, target_type} ... ],
          "node_properties": { <name>: {type, properties} }
        }
      }
    }
    """
    node_by_id: Dict[str, EntityNode] = {n.id: n for n in nodes}
    # Build triples array
    triples: List[Dict[str, Any]] = []
    for rel in relations:
        src = node_by_id.get(rel.source_id)
        dst = node_by_id.get(rel.target_id)
        if not src or not dst:
            continue
        triples.append(
            {
                "source": src.name,
                "source_type": src.label,
                "label": rel.label,
                "target": dst.name,
                "target_type": dst.label,
            }
        )

    # Build node_properties map keyed by node name
    node_properties: Dict[str, Any] = {}
    for n in nodes:
        node_properties[n.name] = {
            "type": n.label,
            "properties": {**(n.properties or {}), "name": n.name},
        }

    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "sources": {
            sources_name: {
                "triples": triples,
                "node_properties": node_properties,
            }
        },
    }


def persist_to_chroma(
    documents: List[Document],
    *,
    persist_dir: Path,
    collection_name: str,
    embedding_model: str,
    openai_api_key: str,
) -> int:
    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    chroma_collection = client.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    embed_model = OpenAIEmbedding(model=embedding_model, api_key=openai_api_key)
    VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_model=embed_model,
    )
    try:
        storage_context.persist(persist_dir=str(persist_dir))
    except Exception as exc:
        LOGGER.debug("StorageContext.persist skipped: %s", exc)
    return len(documents)


def persist_to_neo4j(
    nodes: List[EntityNode],
    relations: List[Relation],
    *,
    uri: str,
    username: str,
    password: str,
    database: str | None,
    build_property_graph_index: bool = False,
    graph_documents: Any | None = None,
) -> Tuple[int, int, bool]:
    store = Neo4jPropertyGraphStore(
        url=uri,
        username=username,
        password=password,
        database=database,
    )
    if nodes:
        store.upsert_nodes(list(nodes))  # type: ignore[arg-type]
    if relations:
        store.upsert_relations(list(relations))  # type: ignore[arg-type]

    built_index = False
    if build_property_graph_index:
        try:
            try:
                from llama_index.core.indices.property_graph import PropertyGraphIndex  # type: ignore[attr-defined]
            except ImportError:
                from llama_index.indices.property_graph import PropertyGraphIndex  # type: ignore[attr-defined]

            try:
                from llama_index.core.schema import GraphDocument  # type: ignore[attr-defined, import-error]
            except ImportError:
                from llama_index.schema import GraphDocument  # type: ignore[attr-defined, import-error]

            from_graph_documents = getattr(PropertyGraphIndex, "from_graph_documents", None)
            if from_graph_documents is None:
                LOGGER.warning(
                    "PropertyGraphIndex.from_graph_documents が利用できないため、インデックス構築をスキップします"
                )
                return len(nodes), len(relations), False

            storage_context = StorageContext.from_defaults(graph_store=cast(Any, store))
            if graph_documents:
                prepared_graph_documents = graph_documents
            else:
                prepared_graph_documents = [
                    GraphDocument(
                        nodes=list(nodes),
                        relationships=list(relations),
                        metadata={"source": "type_definitions"},
                        text="Type definitions property graph",
                    )
                ]
            try:
                from_graph_documents(
                    prepared_graph_documents,
                    storage_context=storage_context,
                    show_progress=False,
                )
                built_index = True
            except TypeError:
                # Older versions may not support show_progress argument
                from_graph_documents(
                    prepared_graph_documents,
                    storage_context=storage_context,
                )
                built_index = True
        except Exception as exc:  # pragma: no cover - runtime dependency on neo4j
            LOGGER.warning("Failed to build PropertyGraphIndex: %s", exc)
    return len(nodes), len(relations), built_index


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    default_json = Path(__file__).with_name("type_definitions.json")
    parser = argparse.ArgumentParser(
        description="structured_api/type_definitions.json を LlamaIndex に取り込み、Neo4j と Chroma に格納します。",
    )
    parser.add_argument("--json-path", type=Path, default=default_json)
    parser.add_argument(
        "--json-reader-schema",
        default=os.getenv("TYPEDEF_JSON_JQ_SCHEMA", DEFAULT_JQ_SCHEMA),
        help="jq schema passed to LlamaIndex JSONReader when loading type definitions",
    )
    parser.add_argument(
        "--chroma-persist-dir",
        type=Path,
        default=Path("data/chroma/type_definitions"),
    )
    parser.add_argument(
        "--chroma-collection",
        default="type_definitions",
    )
    parser.add_argument(
        "--embedding-model",
        default=os.getenv("TYPEDEF_EMBED_MODEL", "text-embedding-3-small"),
    )
    parser.add_argument(
        "--use-llm-extractor",
        action="store_true",
        help="Enable SimpleLLMPathExtractor-assisted graph construction",
    )
    parser.add_argument(
        "--llm-model",
        default=os.getenv("TYPEDEF_LLM_MODEL"),
        help="Override the LLM model used by SimpleLLMPathExtractor (defaults to global Settings)",
    )
    parser.add_argument(
        "--llm-temperature",
        type=float,
        default=float(os.getenv("TYPEDEF_LLM_TEMPERATURE", "0.0")),
        help="Sampling temperature supplied to the LLM extractor",
    )
    parser.add_argument(
        "--create-property-graph-index",
        action="store_true",
        help="Build and persist a PropertyGraphIndex on top of Neo4j after upserting nodes/relations",
    )
    parser.add_argument("--openai-api-key", default=os.getenv("OPENAI_API_KEY"))
    parser.add_argument("--neo4j-uri", default=os.getenv("NEO4J_URI"))
    parser.add_argument("--neo4j-user", default=os.getenv("NEO4J_USERNAME"))
    parser.add_argument("--neo4j-password", default=os.getenv("NEO4J_PASSWORD"))
    parser.add_argument(
        "--neo4j-database",
        default=os.getenv("NEO4J_DATABASE"),
        help="未指定の場合は Neo4j 側の既定 DB を使用します。",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("TYPEDEF_LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    parser.add_argument(
        "--export-triples-json",
        type=Path,
        help="ノード/リレーションから導出したトリプルを JSON で保存する出力パス",
    )
    parser.add_argument(
        "--export-triples-json-format",
        choices=["simple", "extracted"],
        default="simple",
        help="トリプルJSONの出力形式（simple: フラット三項, extracted: 提示スキーマ）",
    )
    parser.add_argument(
        "--export-triples-sources-name",
        default="type_definitions",
        help="extracted 形式の sources 配下で使用する名前",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    load_dotenv()
    args = parse_args(argv)

    # ログファイルのパスを設定（structured_api ディレクトリ内）
    log_dir = Path(__file__).parent
    log_file = log_dir / "type_definitions.log"

    # ログ設定：コンソールとファイル両方に出力
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format=log_format,
        handlers=[
            logging.StreamHandler(),  # コンソール出力
            logging.FileHandler(log_file, encoding="utf-8"),  # ファイル出力
        ],
    )

    LOGGER.info("ログファイルに保存中: %s", log_file)

    if not args.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY が未設定です。環境変数または引数で指定してください。"
        )
    if not args.neo4j_uri or not args.neo4j_user or not args.neo4j_password:
        raise RuntimeError(
            "Neo4j 接続情報が不足しています。NEO4J_URI / USER / PASSWORD を確認してください。"
        )

    LOGGER.info("type_definitions の読み込み元: %s", args.json_path)

    definitions, reader_documents = load_type_definitions(
        args.json_path,
        jq_schema=args.json_reader_schema,
    )

    LOGGER.info("取得した型定義の件数: %d", len(definitions))

    LOGGER.info("Chroma 向けドキュメントを作成中...")

    documents = build_documents(definitions, source_documents=reader_documents or None)

    chroma_count = persist_to_chroma(
        documents,
        persist_dir=args.chroma_persist_dir,
        collection_name=args.chroma_collection,
        embedding_model=args.embedding_model,
        openai_api_key=args.openai_api_key,
    )

    LOGGER.info(
        "Chroma に %d 件のドキュメントを保存 (ディレクトリ=%s, コレクション=%s)",
        chroma_count,
        args.chroma_persist_dir,
        args.chroma_collection,
    )

    LOGGER.info("Neo4j グラフを更新中...")

    nodes, relations = build_graph_elements(
        definitions,
        documents=documents,
        use_llm_extractor=args.use_llm_extractor,
        llm_model=args.llm_model,
        llm_temperature=args.llm_temperature,
    )

    # オプション: トリプル JSON のエクスポート

    if args.export_triples_json:

        try:

            args.export_triples_json.parent.mkdir(parents=True, exist_ok=True)

            if args.export_triples_json_format == "extracted":

                payload = format_triples_extracted(
                    nodes, relations, sources_name=args.export_triples_sources_name
                )

            else:

                payload = build_triples(nodes, relations)

            with args.export_triples_json.open("w", encoding="utf-8") as fp:

                json.dump(payload, fp, ensure_ascii=False, indent=2)

            LOGGER.info(
                "トリプル JSON(%s) を出力しました: %s",
                args.export_triples_json_format,
                args.export_triples_json,
            )

        except Exception as exc:

            LOGGER.error("トリプル JSON の出力に失敗しました: %s", exc)

    node_count, relation_count, built_index = persist_to_neo4j(
        nodes,
        relations,
        uri=args.neo4j_uri,
        username=args.neo4j_user,
        password=args.neo4j_password,
        database=args.neo4j_database,
        build_property_graph_index=args.create_property_graph_index,
    )

    LOGGER.info(
        "Neo4j にノード %d 件・リレーション %d 件を upsert", node_count, relation_count
    )

    if args.create_property_graph_index:

        if built_index:

            LOGGER.info("PropertyGraphIndex を構築しました")

        else:

            LOGGER.info("PropertyGraphIndex の構築はスキップされました")


if __name__ == "__main__":
    main()
