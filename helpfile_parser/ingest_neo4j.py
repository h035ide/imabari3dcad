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
from itertools import islice

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
from llama_index.core.indices.property_graph.transformations import (
    ImplicitPathExtractor,
)
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.schema import MetadataMode, TextNode
from llama_index.core.settings import Settings
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore

try:  # pragma: no cover - import resolution guard
    from .helpfile_parser import HelpDocument, iter_help_documents
except ImportError:  # pragma: no cover - fallback when executed as a script
    # When executed as a script, add the parent directory to path
    # and import from the same directory
    CURRENT_DIR = Path(__file__).resolve().parent
    if str(CURRENT_DIR) not in sys.path:
        sys.path.insert(0, str(CURRENT_DIR))
    import helpfile_parser as _helpfile_parser  # type: ignore
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


@dataclass(frozen=True, slots=True)
class DocumentInfo:
    id: str
    source_path: str
    title: str
    headings: List[str]
    section_count: int
    last_modified: Optional[str]
    extracted_at: Optional[str]


@dataclass(frozen=True, slots=True)
class SectionInfo:
    id: str
    document_id: str
    source_path: str
    title: str
    heading: str
    level: int
    index: int
    last_modified: Optional[str]
    extracted_at: Optional[str]


@dataclass(slots=True)
class PreparedCorpus:
    documents: List[Document]
    doc_infos: Dict[str, DocumentInfo]
    section_infos: Dict[str, SectionInfo]


def _clean_props(**properties: Any) -> Dict[str, Any]:
    return {
        key: value
        for key, value in properties.items()
        if value not in (None, "")
    }


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


def _prepare_corpus(help_docs: Sequence[HelpDocument]) -> PreparedCorpus:
    documents: List[Document] = []
    doc_infos: Dict[str, DocumentInfo] = {}
    section_infos: Dict[str, SectionInfo] = {}

    for help_doc in help_docs:
        source_path = str(help_doc.source_path.resolve())
        document_id = source_path
        last_modified = _to_iso(help_doc.last_modified)
        extracted_at = _to_iso(help_doc.extracted_at)

        doc_infos[document_id] = DocumentInfo(
            id=document_id,
            source_path=source_path,
            title=help_doc.title,
            headings=list(help_doc.headings),
            section_count=len(help_doc.sections),
            last_modified=last_modified,
            extracted_at=extracted_at,
        )

        for section_index, section in enumerate(help_doc.sections):
            heading = (section.heading or "Untitled Section").strip()
            section_id = _hash_identifier(source_path, str(section_index), heading)
            content = (section.content or "").strip()
            text = heading if not content else f"{heading}\n\n{content}"

            section_infos[section_id] = SectionInfo(
                id=section_id,
                document_id=document_id,
                source_path=source_path,
                title=help_doc.title,
                heading=heading,
                level=section.level,
                index=section_index,
                last_modified=last_modified,
                extracted_at=extracted_at,
            )

            if text:
                documents.append(
                    Document(
                        text=text,
                        metadata={
                            "document_id": document_id,
                            "source_path": source_path,
                            "section_id": section_id,
                            "title": help_doc.title,
                            "section_heading": heading,
                            "section_level": section.level,
                            "section_index": section_index,
                            "last_modified": last_modified,
                            "extracted_at": extracted_at,
                            "data_source": DATA_SOURCE,
                        },
                        doc_id=section_id,
                    )
                )

    return PreparedCorpus(
        documents=documents,
        doc_infos=doc_infos,
        section_infos=section_infos,
    )


def _build_property_graph_nodes(
    nodes: Sequence[TextNode],
    doc_infos: Dict[str, DocumentInfo],
    section_infos: Dict[str, SectionInfo],
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

        doc_info = doc_infos[document_id]
        section_info = section_infos[section_id]

        # Ensure core metadata is propagated
        source_path = section_info.source_path or doc_info.source_path
        section_index = section_info.index

        counter_key = (document_id, section_id)
        chunk_index = chunk_counters[counter_key]
        chunk_counters[counter_key] += 1

        chunk_properties: Dict[str, Any] = {
            "chunk_id": node.node_id,
            "document_id": document_id,
            "section_id": section_id,
            "source_path": source_path,
            "title": section_info.title,
            "section_heading": section_info.heading,
            "section_level": section_info.level,
            "section_index": section_index,
            "last_modified": section_info.last_modified,
            "extracted_at": section_info.extracted_at,
            "chunk_index": chunk_index,
            "text_length": len(text),
            "start_char_idx": node.start_char_idx,
            "end_char_idx": node.end_char_idx,
            "data_source": DATA_SOURCE,
        }

        doc_props = _clean_props(
            document_id=doc_info.id,
            source_path=doc_info.source_path,
            title=doc_info.title,
            headings=doc_info.headings,
            section_count=doc_info.section_count,
            last_modified=doc_info.last_modified,
            extracted_at=doc_info.extracted_at,
            data_source=DATA_SOURCE,
        )
        section_props = _clean_props(
            section_id=section_info.id,
            document_id=section_info.document_id,
            source_path=section_info.source_path,
            title=section_info.title,
            section_heading=section_info.heading,
            section_level=section_info.level,
            section_index=section_info.index,
            last_modified=section_info.last_modified,
            extracted_at=section_info.extracted_at,
            data_source=DATA_SOURCE,
        )

        doc_entity = EntityNode(
            name=doc_info.id,
            label="HelpDocument",
            properties=doc_props,
        )
        section_entity = EntityNode(
            name=section_info.id,
            label="HelpSection",
            properties=section_props,
        )
        chunk_entity = ChunkNode(
            text=text,
            id_=node.node_id,
            label="HelpChunk",
            properties=_clean_props(**chunk_properties),
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
    max_files: Optional[int] = None,
    use_llm_extract: bool = False,
    llm_model: Optional[str] = None,
    export_dir: Optional[Path] = None,
    embed_kg_nodes: bool = True,
    help_docs: Optional[Sequence[HelpDocument]] = None,
) -> IngestStats:
    if chunk_size <= 0:
        raise ValueError("chunk_size は正の整数で指定してください。")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap は0以上で指定してください。")
    if max_files is not None and max_files < 0:
        raise ValueError("max_files は0以上で指定してください。")
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")

    # help_docsが指定されている場合はそれを使用、そうでない場合はrootから読み込む
    if help_docs is not None:
        help_docs = list(help_docs)
    else:
        documents_iter = iter_help_documents(root)
        if max_files is not None:
            documents_iter = islice(documents_iter, max_files)
        help_docs = list(documents_iter)
    if not help_docs:
        logging.warning("指定ディレクトリにヘルプHTMLファイルが見つかりませんでした: %s", root)
        return IngestStats(0, 0, 0)

    corpus = _prepare_corpus(help_docs)

    if not corpus.documents:
        logging.warning("解析可能なセクションが存在しませんでした: %s", root)
        return IngestStats(len(corpus.doc_infos), 0, 0)

    parser = SimpleNodeParser.from_defaults(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    nodes = parser.get_nodes_from_documents(corpus.documents)
    graph_nodes = _build_property_graph_nodes(nodes, corpus.doc_infos, corpus.section_infos)

    stats = IngestStats(len(corpus.doc_infos), len(corpus.section_infos), len(graph_nodes))
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

        if embed_kg_nodes:
            _ensure_default_embedding("text-embedding-3-small")

        if use_llm_extract:
            llm = _resolve_llm(model=llm_model)
            PropertyGraphIndex(
                nodes=graph_nodes,
                property_graph_store=graph_store,
                llm=llm,
                # kg_extractors は未指定でデフォルトの [SimpleLLMPathExtractor, ImplicitPathExtractor]
                embed_kg_nodes=embed_kg_nodes,
                show_progress=False,
            )
        else:
            PropertyGraphIndex(
                nodes=graph_nodes,
                property_graph_store=graph_store,
                kg_extractors=[ImplicitPathExtractor()],
                embed_kg_nodes=embed_kg_nodes,
                show_progress=False,
            )
        # オプション: グラフを書き出し
        if export_dir:
            try:
                _export_graph_as_jsonl(graph_store, export_dir)
            except Exception as exc:
                logging.warning("グラフのエクスポートに失敗しました: %s", exc)
    finally:
        graph_store.close()

    return stats


def _configure_logging(*, log_level: str, console_level: str, log_file: Optional[Path]) -> None:
    """Configure logging to minimize console output and optionally write to a file.

    - Console: minimal output (default WARNING)
    - File: detailed output at `log_level` (UTF-8)
    """
    # Configure console encoding for Windows PowerShell UTF-8 support
    if sys.platform == "win32":
        try:
            # Python 3.7+ supports reconfigure
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # pragma: no cover - best effort encoding setup
            pass

    root_logger = logging.getLogger()
    # Reset existing handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    numeric_log_level = getattr(logging, log_level.upper(), logging.INFO)
    numeric_console_level = getattr(logging, console_level.upper(), logging.WARNING)
    root_logger.setLevel(numeric_log_level)

    # Console handler (minimal)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_console_level)
    console_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    root_logger.addHandler(console_handler)

    # File handler (detailed) if requested
    if log_file:
        try:
            log_path = Path(log_file)
            if log_path.parent:
                log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setLevel(numeric_log_level)
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
            )
            root_logger.addHandler(file_handler)
        except Exception as exc:  # pragma: no cover - best effort logging setup
            logging.getLogger(__name__).warning("ログファイルの設定に失敗しました: %s", exc)


def _export_graph_as_jsonl(graph_store: Neo4jPropertyGraphStore, export_dir: Path) -> None:
    """`DATA_SOURCE` に紐づくノード/リレーションを JSONL で書き出す。

    - nodes.jsonl: {id, labels, properties}
    - relationships.jsonl: {id, type, start, end, properties}
    """
    export_dir = Path(export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)

    nodes_query = (
        "MATCH (n) WHERE n.data_source = $source "
        "RETURN id(n) AS id, labels(n) AS labels, properties(n) AS properties"
    )
    rels_query = (
        "MATCH (a)-[r]->(b) WHERE r.data_source = $source "
        "RETURN id(r) AS id, type(r) AS type, id(a) AS start, id(b) AS end, properties(r) AS properties"
    )

    param_map = {"source": DATA_SOURCE}

    # Neo4jPropertyGraphStore.structured_query は結果リストを返す想定
    node_rows = graph_store.structured_query(nodes_query, param_map=param_map)
    rel_rows = graph_store.structured_query(rels_query, param_map=param_map)

    nodes_path = export_dir / "nodes.jsonl"
    rels_path = export_dir / "relationships.jsonl"

    import json

    with nodes_path.open("w", encoding="utf-8") as f_nodes:
        for row in node_rows or []:
            # LlamaIndex の返却形式が dict である前提（無ければそのまま書く）
            data = {
                "id": row.get("id") if isinstance(row, dict) else row[0],
                "labels": row.get("labels") if isinstance(row, dict) else row[1],
                "properties": row.get("properties") if isinstance(row, dict) else row[2],
            }
            f_nodes.write(json.dumps(data, ensure_ascii=False) + "\n")

    with rels_path.open("w", encoding="utf-8") as f_rels:
        for row in rel_rows or []:
            data = {
                "id": row.get("id") if isinstance(row, dict) else row[0],
                "type": row.get("type") if isinstance(row, dict) else row[1],
                "start": row.get("start") if isinstance(row, dict) else row[2],
                "end": row.get("end") if isinstance(row, dict) else row[3],
                "properties": row.get("properties") if isinstance(row, dict) else row[4],
            }
            f_rels.write(json.dumps(data, ensure_ascii=False) + "\n")

    logging.info("グラフをエクスポートしました: %s", export_dir)


def _resolve_llm(*, model: Optional[str]):
    """OpenAI 固定で LLM を初期化して返す。失敗時は None を返す。"""
    try:
        from llama_index.llms.openai import OpenAI  # type: ignore

        return OpenAI(model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    except Exception as exc:  # pragma: no cover
        logging.warning("OpenAI LLM の初期化に失敗: %s", exc)
        return None


def _ensure_default_embedding(model_name: Optional[str] = None) -> None:
    """Set default embedding model for LlamaIndex Settings if not set.

    Prefer OpenAI `text-embedding-3-small` unless explicitly provided.
    """
    try:
        # Lazy import to avoid hard dependency when not used
        from llama_index.embeddings.openai import OpenAIEmbedding  # type: ignore

        if getattr(Settings, "embed_model", None) is None:
            default_model = model_name or os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            Settings.embed_model = OpenAIEmbedding(model=default_model)
    except Exception as exc:  # pragma: no cover
        logging.warning("埋め込みモデルの既定設定に失敗しました: %s", exc)


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
        "--use-llm-extract",
        action="store_true",
        help="LLMを用いたトリプレット抽出を有効化します（モデルは --llm-provider/--llm-model で指定）。",
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        help="使用するLLMモデル名（デフォルト: gpt-4o-mini）",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        help="読み込む最大ファイル数を指定します（0で0件、未指定で全件）。",
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
    parser.add_argument(
        "--log-file",
        type=Path,
        help="ログファイルの出力先パス。指定時はコンソール出力を最小限にします。",
    )
    parser.add_argument(
        "--console-level",
        default="WARNING",
        choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
        help="コンソール出力のログレベル (デフォルト: WARNING)",
    )
    parser.add_argument(
        "--export-dir",
        type=Path,
        help="インポート完了後にグラフをJSONLで書き出すディレクトリ（nodes.jsonl / relationships.jsonl）",
    )
    embed_group = parser.add_mutually_exclusive_group()
    embed_group.add_argument(
        "--embed-kg-nodes",
        dest="embed_kg_nodes",
        action="store_true",
        help="KGノードのベクトル埋め込みとベクタ検索を有効化（デフォルト有効）",
    )
    embed_group.add_argument(
        "--no-embed-kg-nodes",
        dest="embed_kg_nodes",
        action="store_false",
        help="KGノードのベクトル埋め込みとベクタ検索を無効化",
    )
    parser.set_defaults(embed_kg_nodes=True)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv if argv is not None else None)

    # 構造化されたロギング設定: ファイルへは詳細、コンソールは最小限
    _configure_logging(
        log_level=args.log_level,
        console_level=args.console_level,
        log_file=args.log_file,
    )

    try:
        stats = ingest_help_files(
            args.root,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            database=args.database,
            wipe=args.wipe,
            dry_run=args.dry_run,
            max_files=args.max_files,
            use_llm_extract=args.use_llm_extract,
            llm_model=args.llm_model,
            export_dir=args.export_dir,
            embed_kg_nodes=args.embed_kg_nodes,
        )
    except Exception as exc:  # pragma: no cover - CLI entry point
        logging.error("インポート処理中にエラーが発生しました: %s", exc)
        return 1

    logging.info("処理が完了しました: %s", stats)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI guard
    sys.exit(main())
