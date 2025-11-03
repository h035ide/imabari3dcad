from __future__ import annotations

import argparse
import hashlib
import itertools
import logging
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

from dotenv import load_dotenv
from neo4j import GraphDatabase, Session
from llama_index.core import Document
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.schema import MetadataMode, TextNode

try:  # pragma: no cover - import resolution guard
    from helpfile_parser.helpfile_parser import HelpDocument, iter_help_documents
except ImportError:  # pragma: no cover - fallback when executed as a script
    ROOT_DIR = Path(__file__).resolve().parent.parent
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    from helpfile_parser import helpfile_parser as _helpfile_parser  # type: ignore

    HelpDocument = _helpfile_parser.HelpDocument
    iter_help_documents = _helpfile_parser.iter_help_documents


DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 120
DEFAULT_BATCH_SIZE = 50


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


def _batched(iterable: Iterable[Dict], size: int) -> Iterator[List[Dict]]:
    iterator = iter(iterable)
    while True:
        batch = list(itertools.islice(iterator, size))
        if not batch:
            break
        yield batch


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


def _ensure_constraints(session: Session) -> None:
    queries = (
        """
        CREATE CONSTRAINT help_document_source IF NOT EXISTS
        FOR (d:HelpDocument)
        REQUIRE d.source_path IS UNIQUE
        """,
        """
        CREATE CONSTRAINT help_section_id IF NOT EXISTS
        FOR (s:HelpSection)
        REQUIRE s.section_id IS UNIQUE
        """,
        """
        CREATE CONSTRAINT help_chunk_id IF NOT EXISTS
        FOR (c:HelpChunk)
        REQUIRE c.chunk_id IS UNIQUE
        """,
    )
    for query in queries:
        session.run(query)


def _wipe_existing_graph(session: Session) -> None:
    session.run(
        """
        MATCH (n)
        WHERE n:HelpChunk OR n:HelpSection OR n:HelpDocument
        DETACH DELETE n
        """
    )


def _prepare_documents(help_docs: Sequence[HelpDocument]) -> Tuple[List[Document], List[Dict], List[Dict]]:
    documents: List[Document] = []
    doc_records: List[Dict] = []
    section_records: List[Dict] = []

    for help_doc in help_docs:
        source_path = str(help_doc.source_path.resolve())
        last_modified = _to_iso(help_doc.last_modified)
        extracted_at = _to_iso(help_doc.extracted_at)

        doc_record = {
            "source_path": source_path,
            "title": help_doc.title,
            "headings": list(help_doc.headings),
            "section_count": len(help_doc.sections),
            "last_modified": last_modified,
            "extracted_at": extracted_at,
        }
        doc_records.append(doc_record)

        for section_index, section in enumerate(help_doc.sections):
            heading = (section.heading or "Untitled Section").strip()
            section_id = _hash_identifier(source_path, str(section_index), heading)
            content = (section.content or "").strip()
            text = heading if not content else f"{heading}\n\n{content}"

            metadata = {
                "source_path": source_path,
                "title": help_doc.title,
                "section_heading": heading,
                "section_level": section.level,
                "section_index": section_index,
                "section_id": section_id,
                "last_modified": last_modified,
                "extracted_at": extracted_at,
            }

            section_records.append(
                {
                    "section_id": section_id,
                    "source_path": source_path,
                    "title": help_doc.title,
                    "section_heading": heading,
                    "section_level": section.level,
                    "section_index": section_index,
                    "last_modified": last_modified,
                    "extracted_at": extracted_at,
                }
            )

            if text:
                documents.append(Document(text=text, metadata=metadata, doc_id=section_id))

    return documents, doc_records, section_records


def _build_chunk_records(nodes: Sequence[TextNode]) -> List[Dict]:
    chunk_records: List[Dict] = []
    chunk_counters: Dict[Tuple[str, int], int] = defaultdict(int)

    for node in nodes:
        text = node.get_content(metadata_mode=MetadataMode.NONE).strip()
        if not text:
            continue

        metadata = dict(node.metadata)
        source_path = metadata.get("source_path")
        section_index = metadata.get("section_index")
        section_id = metadata.get("section_id")

        if source_path is None or section_index is None or section_id is None:
            logging.debug(
                "Skipping node %s due to missing core metadata (source_path=%s, section_index=%s, section_id=%s)",
                node.node_id,
                source_path,
                section_index,
                section_id,
            )
            continue

        counter_key = (source_path, int(section_index))
        chunk_index = chunk_counters[counter_key]
        chunk_counters[counter_key] += 1

        start_idx = node.start_char_idx
        end_idx = node.end_char_idx
        char_span = None
        if isinstance(start_idx, int) and isinstance(end_idx, int):
            char_span = max(end_idx - start_idx, 0)

        chunk_records.append(
            {
                "chunk_id": node.node_id,
                "text": text,
                "text_length": len(text),
                "chunk_index": chunk_index,
                "chunk_size": char_span if char_span is not None else len(text),
                "start_char_idx": start_idx,
                "end_char_idx": end_idx,
                "source_path": source_path,
                "title": metadata.get("title"),
                "section_id": section_id,
                "section_heading": metadata.get("section_heading"),
                "section_level": metadata.get("section_level"),
                "section_index": metadata.get("section_index"),
                "last_modified": metadata.get("last_modified"),
                "extracted_at": metadata.get("extracted_at"),
            }
        )

    return chunk_records


DOC_QUERY = """
UNWIND $batch AS row
MERGE (d:HelpDocument {source_path: row.source_path})
SET d.title = row.title,
    d.headings = row.headings,
    d.section_count = row.section_count,
    d.last_modified = row.last_modified,
    d.extracted_at = row.extracted_at,
    d.ingested_at = row.ingested_at
"""


SECTION_QUERY = """
UNWIND $batch AS row
MERGE (s:HelpSection {section_id: row.section_id})
SET s.source_path = row.source_path,
    s.title = row.title,
    s.section_heading = row.section_heading,
    s.section_level = row.section_level,
    s.section_index = row.section_index,
    s.last_modified = row.last_modified,
    s.extracted_at = row.extracted_at,
    s.ingested_at = row.ingested_at
WITH row, s
MATCH (d:HelpDocument {source_path: row.source_path})
MERGE (d)-[:HAS_SECTION]->(s)
"""


CHUNK_QUERY = """
UNWIND $batch AS row
MERGE (c:HelpChunk {chunk_id: row.chunk_id})
SET c.source_path = row.source_path,
    c.title = row.title,
    c.text = row.text,
    c.text_length = row.text_length,
    c.chunk_index = row.chunk_index,
    c.chunk_size = row.chunk_size,
    c.start_char_idx = row.start_char_idx,
    c.end_char_idx = row.end_char_idx,
    c.section_heading = row.section_heading,
    c.section_level = row.section_level,
    c.section_index = row.section_index,
    c.last_modified = row.last_modified,
    c.extracted_at = row.extracted_at,
    c.ingested_at = row.ingested_at
WITH row, c
MATCH (d:HelpDocument {source_path: row.source_path})
MERGE (d)-[:HAS_CHUNK]->(c)
WITH row, c
MATCH (s:HelpSection {section_id: row.section_id})
MERGE (s)-[:HAS_CHUNK]->(c)
"""


def _persist_records(
    driver,
    database: str,
    doc_records: Sequence[Dict],
    section_records: Sequence[Dict],
    chunk_records: Sequence[Dict],
    batch_size: int,
) -> None:
    with driver.session(database=database) as session:
        if doc_records:
            logging.info("Neo4jへ%d件のHelpDocumentを保存します。", len(doc_records))
            for batch in _batched(doc_records, batch_size):
                session.run(DOC_QUERY, batch=batch)

        if section_records:
            logging.info("Neo4jへ%d件のHelpSectionを保存します。", len(section_records))
            for batch in _batched(section_records, batch_size):
                session.run(SECTION_QUERY, batch=batch)

        if chunk_records:
            logging.info("Neo4jへ%d件のHelpChunkを保存します。", len(chunk_records))
            for batch in _batched(chunk_records, batch_size):
                session.run(CHUNK_QUERY, batch=batch)


def ingest_help_files(
    root: Path,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    batch_size: int = DEFAULT_BATCH_SIZE,
    database: Optional[str] = None,
    wipe: bool = False,
    dry_run: bool = False,
) -> IngestStats:
    if chunk_size <= 0:
        raise ValueError("chunk_size は正の整数で指定してください。")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap は0以上で指定してください。")
    if batch_size <= 0:
        raise ValueError("batch_size は正の整数で指定してください。")

    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")

    help_docs = list(iter_help_documents(root))
    if not help_docs:
        logging.warning("指定ディレクトリにヘルプHTMLファイルが見つかりませんでした: %s", root)
        return IngestStats(0, 0, 0)

    documents, doc_records, section_records = _prepare_documents(help_docs)

    if not documents:
        logging.warning("解析可能なセクションが存在しませんでした: %s", root)
        return IngestStats(len(doc_records), 0, 0)

    parser = SimpleNodeParser.from_defaults(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    nodes = parser.get_nodes_from_documents(documents)
    chunk_records = _build_chunk_records(nodes)

    stats = IngestStats(len(doc_records), len(section_records), len(chunk_records))
    logging.info(
        "LlamaIndexでチャンク化完了: %s (chunk_size=%d, overlap=%d)",
        stats,
        chunk_size,
        chunk_overlap,
    )

    ingestion_timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    for record in doc_records:
        record["ingested_at"] = ingestion_timestamp
    for record in section_records:
        record["ingested_at"] = ingestion_timestamp
    for record in chunk_records:
        record["ingested_at"] = ingestion_timestamp

    if dry_run:
        logging.info("dry-runモードのためNeo4jへの書き込みをスキップします。")
        return stats

    load_dotenv()
    uri, user, password, database_name = _resolve_neo4j_config(database)
    driver = GraphDatabase.driver(uri, auth=(user, password))

    try:
        with driver.session(database=database_name) as session:
            _ensure_constraints(session)
            if wipe:
                logging.info("既存のヘルプグラフを削除します。")
                _wipe_existing_graph(session)

        _persist_records(driver, database_name, doc_records, section_records, chunk_records, batch_size)
    finally:
        driver.close()

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
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Neo4j 書き込み時のバッチサイズ (デフォルト: {DEFAULT_BATCH_SIZE})",
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
            batch_size=args.batch_size,
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

