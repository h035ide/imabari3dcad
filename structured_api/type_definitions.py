"""structured_api/type_definitions.json を LlamaIndex 形式へ変換し Neo4j / Chroma に格納するユーティリティ."""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import chromadb
from dotenv import load_dotenv
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.core.graph_stores.types import EntityNode, Relation
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.vector_stores.chroma import ChromaVectorStore


LOGGER = logging.getLogger(__name__)


def load_type_definitions(json_path: Path) -> List[Dict[str, Any]]:
    with json_path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)
    definitions = payload.get("type_definitions", [])
    if not isinstance(definitions, list):
        raise ValueError("type_definitions キーがリストではありません")
    return definitions


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


def build_documents(definitions: List[Dict[str, Any]]) -> List[Document]:
    documents: List[Document] = []
    for typedef in definitions:
        name = typedef.get("name", "不明")
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
            text = source.get("text")
            if text:
                lines.append("原文:\n" + text)

        metadata = {
            "type": "type_definition",
            "name": name,
            "canonical_type": canonical or "",
            "source_path": source.get("path") if isinstance(source, dict) else "",
        }

        content = "\n".join(lines)
        documents.append(Document(text=content, metadata=metadata))
    return documents


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
        nodes[node_id] = EntityNode(
            id=node_id,
            name=str(name),
            label=label,
            properties={**normalized_props},
        )
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
    definitions: List[Dict[str, Any]]
) -> Tuple[List[EntityNode], List[Relation]]:
    nodes: Dict[str, EntityNode] = {}
    relations: List[Relation] = []

    for typedef in definitions:
        name = typedef.get("name", "")
        if not name:
            continue
        node_id = f"type::{name}"
        description = typedef.get("description")
        canonical = typedef.get("canonical_type")
        source = typedef.get("source") if isinstance(typedef.get("source"), dict) else {}
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
                entry_id = entry.get("id") or entry.get("description") or json.dumps(entry, ensure_ascii=False)
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
                entry_id = entry.get("id") or entry.get("description") or json.dumps(entry, ensure_ascii=False)
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
                payload = {"value": value, "variant": variant, "explanation": explanation}
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
) -> Tuple[int, int]:
    store = Neo4jPropertyGraphStore(
        url=uri,
        username=username,
        password=password,
        database=database,
    )
    if nodes:
        store.upsert_nodes(nodes)
    if relations:
        store.upsert_relations(relations)
    return len(nodes), len(relations)


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    default_json = Path(__file__).with_name("type_definitions.json")
    parser = argparse.ArgumentParser(
        description="structured_api/type_definitions.json を LlamaIndex に取り込み、Neo4j と Chroma に格納します。",
    )
    parser.add_argument("--json-path", type=Path, default=default_json)
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
            logging.FileHandler(log_file, encoding="utf-8")  # ファイル出力
        ]
    )

    LOGGER.info("ログファイルに保存中: %s", log_file)

    if not args.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY が未設定です。環境変数または引数で指定してください。")
    if not args.neo4j_uri or not args.neo4j_user or not args.neo4j_password:
        raise RuntimeError("Neo4j 接続情報が不足しています。NEO4J_URI / USER / PASSWORD を確認してください。")

    LOGGER.info("type_definitions を読み込み中: %s", args.json_path)
    definitions = load_type_definitions(args.json_path)
    LOGGER.info("型定義件数: %d", len(definitions))

    LOGGER.info("Chroma 用ドキュメントを生成中...")
    documents = build_documents(definitions)
    chroma_count = persist_to_chroma(
        documents,
        persist_dir=args.chroma_persist_dir,
        collection_name=args.chroma_collection,
        embedding_model=args.embedding_model,
        openai_api_key=args.openai_api_key,
    )
    LOGGER.info(
        "Chroma へ %d 件のドキュメントを保存 (ディレクトリ=%s, コレクション=%s)",
        chroma_count,
        args.chroma_persist_dir,
        args.chroma_collection,
    )

    LOGGER.info("Neo4j グラフ要素を構築中...")
    nodes, relations = build_graph_elements(definitions)
    # 任意: トリプルJSONのエクスポート
    if args.export_triples_json:
        try:
            triples = build_triples(nodes, relations)
            args.export_triples_json.parent.mkdir(parents=True, exist_ok=True)
            with args.export_triples_json.open("w", encoding="utf-8") as fp:
                json.dump(triples, fp, ensure_ascii=False, indent=2)
            LOGGER.info("トリプルを JSON に出力: %s", args.export_triples_json)
        except Exception as exc:
            LOGGER.error("トリプル JSON 出力に失敗: %s", exc)
    node_count, relation_count = persist_to_neo4j(
        nodes,
        relations,
        uri=args.neo4j_uri,
        username=args.neo4j_user,
        password=args.neo4j_password,
        database=args.neo4j_database,
    )
    LOGGER.info(
        "Neo4j へノード %d 件、リレーション %d 件を upsert", node_count, relation_count
    )


if __name__ == "__main__":
    main()
