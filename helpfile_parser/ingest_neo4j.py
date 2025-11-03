from __future__ import annotations

import argparse
import hashlib
import logging
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from dotenv import load_dotenv
from llama_index.core import Document
from llama_index.core.graph_stores.types import (
    ChunkNode,
    EntityNode,
    KG_NODES_KEY,
    KG_RELATIONS_KEY,
    Relation,
)
from llama_index.core.indices.property_graph.base import PropertyGraphIndex
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.schema import MetadataMode, TextNode
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore

try:  # pragma: no cover - import resolution guard
    from .helpfile_parser import HelpDocument, iter_help_documents
except ImportError:  # pragma: no cover - fallback when executed as a script
    ROOT_DIR = Path(__file__).resolve().parent.parent
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    from helpfile_parser import helpfile_parser as _helpfile_parser  # type: ignore

    HelpDocument = _helpfile_parser.HelpDocument
    iter_help_documents = _helpfile_parser.iter_help_documents


DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 120
DATA_SOURCE = "EVOSHIP_HELP_FILES"


@dataclass(slots=True)
class IngestStats:
    documents: int
    sections: int
    chunks: int

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return (
            f"{self.documents} documents, "
            f"{self.sections} sections, "
            f"{self.chunks} chunks"
        )


def _to_iso(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.replace(microsecond=0).isoformat()


def _hash_identifier(*parts: str) -> str:
    joined = "||".join(parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()


def _resolve_neo4j_config(database_override: Optional[str] = None) -> Tuple[str, str, str, str]:
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    database = database_override or os.getenv("NEO4J_DATABASE") or "neo4j"

    if not uri or not user or not password:
        raise EnvironmentError(
            "Neo4j接続情報が不足しています。NEO4J_URI, NEO4J_USER (または NEO4J_USERNAME), "
            "NEO4J_PASSWORD を環境変数または .env に設定してください。"
        )
    return uri, user, password, database


def _prepare_documents(
    help_docs: Sequence[HelpDocument],
) -> Tuple[List[Document], Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    documents: List[Document] = []
    doc_metadata: Dict[str, Dict[str, str]] = {}
    section_metadata: Dict[str, Dict[str, str]] = {}

    for help_doc in help_docs:
        source_path = str(help_doc.source_path.resolve())
        document_id = source_path
        last_modified = _to_iso(help_doc.last_modified)
        extracted_at = _to_iso(help_doc.extracted_at)

        doc_metadata[document_id] = {
            "document_id": document_id,
            "source_path": source_path,
            "title": help_doc.title,
            "headings": list(help_doc.headings),
            "section_count": len(help_doc.sections),
            "last_modified": last_modified or "",
            "extracted_at": extracted_at or "",
            "data_source": DATA_SOURCE,
        }

        for section_index, section in enumerate(help_doc.sections):
            heading = (section.heading or "Untitled Section").strip()
            section_id = _hash_identifier(source_path, str(section_index), heading)
            content = (section.content or "").strip()
            text = heading if not content else f"{heading}\n\n{content}"

            section_metadata[section_id] = {
                "section_id": section_id,
                "document_id": document_id,
                "source_path": source_path,
                "title": help_doc.title,
                "section_heading": heading,
                "section_level": section.level,
                "section_index": section_index,
                "last_modified": last_modified or "",
                "extracted_at": extracted_at or "",
                "data_source": DATA_SOURCE,
            }

            if text:
                metadata = {
                    "document_id": document_id,
                    "source_path": source_path,
                    "title": help_doc.title,
                    "section_heading": heading,
                    "section_level": section.level,
                    "section_index": section_index,
                    "section_id": section_id,
                    "last_modified": last_modified,
                    "extracted_at": extracted_at,
                    "data_source": DATA_SOURCE,
                }
                documents.append(Document(text=text, metadata=metadata, doc_id=section_id))

    return documents, doc_metadata, section_metadata


def _build_property_graph_nodes(
    nodes: Sequence[TextNode],
    doc_metadata: Dict[str, Dict[str, Any]],
    section_metadata: Dict[str, Dict[str, Any]],
) -> List[TextNode]:
    processed_nodes: List[TextNode] = []
    chunk_counters: Dict[Tuple[str, str], int] = defaultdict(int)

    for node in nodes:
        text = node.get_content(metadata_mode=MetadataMode.NONE).strip()
        if not text:
            continue

        metadata = dict(node.metadata)
        document_id = metadata.get("document_id")
        section_id = metadata.get("section_id")

        if not document_id or not section_id:
            logging.debug(
                "Skipping node %s due to missing document/section metadata (document_id=%s, section_id=%s)",
                node.node_id,
                document_id,
                section_id,
            )
            continue

        doc_props = dict(doc_metadata.get(document_id, {}))
        section_props = dict(section_metadata.get(section_id, {}))

        # Ensure core metadata is propagated
        source_path = section_props.get("source_path") or doc_props.get("source_path")
        section_index = section_props.get("section_index")

        counter_key = (document_id, section_id)
        chunk_index = chunk_counters[counter_key]
        chunk_counters[counter_key] += 1

        chunk_properties: Dict[str, Any] = {
            "chunk_id": node.node_id,
            "document_id": document_id,
            "section_id": section_id,
            "source_path": source_path,
            "title": metadata.get("title"),
            "section_heading": metadata.get("section_heading"),
            "section_level": metadata.get("section_level"),
            "section_index": section_index,
            "last_modified": metadata.get("last_modified"),
            "extracted_at": metadata.get("extracted_at"),
            "chunk_index": chunk_index,
            "text_length": len(text),
            "start_char_idx": node.start_char_idx,
            "end_char_idx": node.end_char_idx,
            "data_source": DATA_SOURCE,
        }

        doc_props.setdefault("data_source", DATA_SOURCE)
        section_props.setdefault("data_source", DATA_SOURCE)

        doc_entity = EntityNode(
            name=document_id,
            label="HelpDocument",
            properties={k: v for k, v in doc_props.items() if v not in (None, "")},
        )
        section_entity = EntityNode(
            name=section_id,
            label="HelpSection",
            properties={k: v for k, v in section_props.items() if v not in (None, "")},
        )
        chunk_entity = ChunkNode(
            text=text,
            id_=node.node_id,
            label="HelpChunk",
            properties={k: v for k, v in chunk_properties.items() if v is not None},
        )

        relations = [
            Relation(
                label="HAS_SECTION",
                source_id=doc_entity.id,
                target_id=section_entity.id,
                properties={"data_source": DATA_SOURCE},
            ),
            Relation(
                label="HAS_CHUNK",
                source_id=doc_entity.id,
                target_id=chunk_entity.id,
                properties={
                    "data_source": DATA_SOURCE,
                    "section_id": section_id,
                    "chunk_index": chunk_index,
                },
            ),
            Relation(
                label="HAS_CHUNK",
                source_id=section_entity.id,
                target_id=chunk_entity.id,
                properties={
                    "data_source": DATA_SOURCE,
                    "chunk_index": chunk_index,
                },
            ),
        ]

        node.metadata.update(chunk_properties)
        node.metadata[KG_NODES_KEY] = [doc_entity, section_entity, chunk_entity]
        node.metadata[KG_RELATIONS_KEY] = relations

        processed_nodes.append(node)

    return processed_nodes


def _wipe_existing_graph(graph_store: Neo4jPropertyGraphStore) -> None:
    graph_store.structured_query(
        "MATCH (n) WHERE n.data_source = $source DETACH DELETE n",
        param_map={"source": DATA_SOURCE},
    )


def ingest_help_files(
    root: Path,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    database: Optional[str] = None,
    wipe: bool = False,
    dry_run: bool = False,
) -> IngestStats:
    if chunk_size <= 0:
        raise ValueError("chunk_size は正の整数で指定してください。")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap は0以上で指定してください。")
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")

    help_docs = list(iter_help_documents(root))
    if not help_docs:
        logging.warning("指定ディレクトリにヘルプHTMLファイルが見つかりませんでした: %s", root)
        return IngestStats(0, 0, 0)

    documents, doc_metadata, section_metadata = _prepare_documents(help_docs)

    if not documents:
        logging.warning("解析可能なセクションが存在しませんでした: %s", root)
        return IngestStats(len(doc_metadata), 0, 0)

    parser = SimpleNodeParser.from_defaults(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    nodes = parser.get_nodes_from_documents(documents)
    graph_nodes = _build_property_graph_nodes(nodes, doc_metadata, section_metadata)

    stats = IngestStats(len(doc_metadata), len(section_metadata), len(graph_nodes))
    logging.info(
        "LlamaIndexでチャンク化完了: %s (chunk_size=%d, overlap=%d)",
        stats,
        chunk_size,
        chunk_overlap,
    )

    if dry_run:
        logging.info("dry-runモードのためNeo4jへの書き込みをスキップします。")
        return stats

    load_dotenv()
    uri, user, password, database_name = _resolve_neo4j_config(database)
    graph_store = Neo4jPropertyGraphStore(
        username=user,
        password=password,
        url=uri,
        database=database_name,
    )
    try:
        if wipe:
            logging.info("既存のヘルプグラフを削除します。")
            _wipe_existing_graph(graph_store)

        PropertyGraphIndex(
            nodes=graph_nodes,
            property_graph_store=graph_store,
            kg_extractors=[],
            embed_kg_nodes=False,
            show_progress=False,
        )
    finally:
        graph_store.close()

    return stats


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="EVOSHIPヘルプHTMLをLlamaIndexでチャンク化しNeo4jへ格納します。",
    )
    parser.add_argument(
        "root",
        type=Path,
        help="EVOSHIP_HELP_FILES ディレクトリへのパス",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"LlamaIndex SimpleNodeParser のチャンクサイズ (デフォルト: {DEFAULT_CHUNK_SIZE})",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP,
        help=f"チャンク間のオーバーラップ文字数 (デフォルト: {DEFAULT_CHUNK_OVERLAP})",
    )
    parser.add_argument(
        "--database",
        type=str,
        help="ターゲットとなるNeo4jデータベース名 (NEO4J_DATABASE を上書き)",
    )
    parser.add_argument(
        "--wipe",
        action="store_true",
        help="既存の HelpDocument/HelpSection/HelpChunk ノードを削除してからインポートします。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="チャンク化のみ実行し、Neo4jへの書き込みは行いません。",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
        help="ログレベルを指定します (デフォルト: INFO)",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv if argv is not None else None)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s %(message)s",
    )

    try:
        stats = ingest_help_files(
            args.root,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            database=args.database,
            wipe=args.wipe,
            dry_run=args.dry_run,
        )
    except Exception as exc:  # pragma: no cover - CLI entry point
        logging.error("インポート処理中にエラーが発生しました: %s", exc)
        return 1

    logging.info("処理が完了しました: %s", stats)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI guard
    sys.exit(main())
