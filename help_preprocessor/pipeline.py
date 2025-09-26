from __future__ import annotations

"""High-level orchestration for the help preprocessor pipeline."""

from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
from typing import Any, Iterable

from .config import HelpPreprocessorConfig
from .graph_builder import HelpGraphBuilder
from .html_parser import HelpHTMLParser
from .index_parser import HelpIndexParser
from .schemas import HelpCategory, HelpSection, HelpTopic
from .storage.chroma_loader import HelpChromaLoader
from .storage.neo4j_loader import HelpNeo4jLoader
from .vector_generator import HelpVectorGenerator


@dataclass(slots=True)
class ParsedArtifacts:
    """Container for parsed index and HTML normalization results."""

    root_category: HelpCategory
    diagnostics: dict[str, Any]


@dataclass(slots=True)
class PipelineResult:
    """Aggregated output from a pipeline run."""

    artifacts: ParsedArtifacts
    graph_nodes: list[dict]
    graph_relationships: list[dict]
    vector_chunks: list[dict]


@dataclass(slots=True)
class HelpPreprocessorPipeline:
    """Coordinate parsing, graph building, and storage steps."""

    config: HelpPreprocessorConfig
    graph_builder: HelpGraphBuilder = field(default_factory=HelpGraphBuilder)
    vector_generator: HelpVectorGenerator = field(default_factory=HelpVectorGenerator)
    neo4j_loader: HelpNeo4jLoader | None = None
    chroma_loader: HelpChromaLoader | None = None
    _section_cache: dict[Path, list[HelpSection]] = field(default_factory=dict, init=False)

    def run(self, dry_run: bool = False) -> PipelineResult:
        """Execute the end-to-end pipeline."""

        result = self.build_only()

        if dry_run:
            logging.debug("Dry-run mode enabled; skipping storage integration.")
            return result

        if self.neo4j_loader is not None:
            logging.info(
                "Writing %s nodes and %s relationships to Neo4j.",
                len(result.graph_nodes),
                len(result.graph_relationships),
            )
            self.neo4j_loader.upsert(result.graph_nodes, result.graph_relationships)

        if self.chroma_loader is not None and result.vector_chunks:
            logging.info("Writing %s vector chunks to Chroma.", len(result.vector_chunks))
            self.chroma_loader.upsert(result.vector_chunks)

        return result

    def build_only(self) -> PipelineResult:
        """Perform parsing and transformation without writing to storage."""

        artifacts = self._load_or_parse()
        category_count = self._count_categories(artifacts.root_category)
        topic_count = sum(1 for _ in artifacts.root_category.iter_topics())
        logging.info("Parsed %s categories and %s topics", category_count, topic_count)

        graph_nodes, graph_relationships = self._build_graph_payloads(artifacts.root_category)
        vector_chunks = self._build_vector_chunks(artifacts.root_category)
        return PipelineResult(artifacts, graph_nodes, graph_relationships, vector_chunks)

    def _cache_path(self) -> Path:
        cache_dir = self.config.cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / "index_parse.json"

    def _load_or_parse(self) -> ParsedArtifacts:
        cache_file = self._cache_path()
        if cache_file.exists():
            logging.debug("Loading cached help artifacts from %s", cache_file)
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            root = self._deserialize_category(data["categories"])
            diagnostics = data.get("diagnostics", {})
            return ParsedArtifacts(root_category=root, diagnostics=diagnostics)

        logging.info("Parsing help index from %s", self.config.index_file or "default index.txt")
        index_path = self.config.index_file or (self.config.source_root / "index.txt")
        index_parser = HelpIndexParser(index_path, encoding=self.config.encoding)
        root_category = index_parser.parse()

        diagnostics: dict[str, Any] = {
            "index_errors": list(index_parser.iter_errors()),
        }

        diagnostics["html_samples"] = self._collect_html_diagnostics()

        cache_file.write_text(
            json.dumps(
                {
                    "categories": self._serialize_category(root_category),
                    "diagnostics": diagnostics,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        logging.debug("Cached parsed artifacts at %s", cache_file)
        return ParsedArtifacts(root_category=root_category, diagnostics=diagnostics)

    def _build_graph_payloads(self, root: HelpCategory) -> tuple[list[dict], list[dict]]:
        nodes = self.graph_builder.build_nodes(root)
        relationships = self.graph_builder.build_relationships(root)
        logging.debug("Graph payload generated: %s nodes, %s relationships", len(nodes), len(relationships))
        return nodes, relationships

    def _build_vector_chunks(self, root: HelpCategory) -> list[dict]:
        chunks: list[dict] = []
        for section in self._iter_sections(root):
            chunks.extend(self.vector_generator.build_chunks(section))
        
        # Apply embeddings if OpenAI model is configured
        if self.config.openai_model:
            logging.info("Generating embeddings using model: %s", self.config.openai_model)
            embedded_chunks = list(self.vector_generator.embed_chunks(
                chunks, 
                openai_model=self.config.openai_model
            ))
            chunks = embedded_chunks
            
        logging.debug("Vector payload generated: %s chunks", len(chunks))
        return chunks

    def _iter_sections(self, root: HelpCategory) -> Iterable[HelpSection]:
        html_parser = HelpHTMLParser(self.config.source_root, encoding=self.config.encoding)
        for topic in root.iter_topics():
            if not topic.sections:
                sections = self._section_cache.get(topic.source_path)
                if sections is None:
                    try:
                        sections = list(html_parser.parse_file(topic.source_path))
                    except FileNotFoundError:
                        logging.warning("Help topic source not found: %s", topic.source_path)
                        sections = []
                    self._section_cache[topic.source_path] = sections
                topic.sections.extend(sections)
            for section in topic.sections:
                yield section

    def _collect_html_diagnostics(self) -> list[dict[str, str]]:
        html_parser = HelpHTMLParser(self.config.source_root, encoding=self.config.encoding)
        sample_files = sorted(self.config.source_root.glob("*.html"))[:3]
        diagnostics: list[dict[str, str]] = []
        for html_path in sample_files:
            _, diag = html_parser.read_normalized_html(html_path)
            diagnostics.append(
                {
                    "path": str(html_path),
                    "encoding": diag.selected_encoding,
                    "fallback": str(diag.fallback_used),
                    "bom": str(diag.had_bom),
                }
            )
        if not diagnostics:
            logging.warning("No HTML files discovered in %s for diagnostics.", self.config.source_root)
        return diagnostics

    def _serialize_category(self, category: HelpCategory) -> dict[str, Any]:
        return {
            "category_id": category.category_id,
            "name": category.name,
            "topics": [
                {
                    "topic_id": topic.topic_id,
                    "title": topic.title,
                    "source_path": str(topic.source_path),
                }
                for topic in category.topics
            ],
            "children": [self._serialize_category(child) for child in category.children],
        }

    def _deserialize_category(self, data: dict[str, Any]) -> HelpCategory:
        category = HelpCategory(
            category_id=data["category_id"],
            name=data["name"],
            topics=[],
            children=[],
        )
        for topic_data in data.get("topics", []):
            category.topics.append(self._deserialize_topic(topic_data))
        for child_data in data.get("children", []):
            category.children.append(self._deserialize_category(child_data))
        return category

    def _deserialize_topic(self, data: dict[str, Any]) -> HelpTopic:
        return HelpTopic(
            topic_id=data["topic_id"],
            title=data["title"],
            source_path=Path(data["source_path"]),
            sections=[],
            related=[],
        )

    @staticmethod
    def _count_categories(root: HelpCategory) -> int:
        count = 0
        stack = [root]
        while stack:
            current = stack.pop()
            count += len(current.children)
            stack.extend(current.children)
        return count
