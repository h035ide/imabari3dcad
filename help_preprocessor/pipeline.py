from __future__ import annotations

"""High-level orchestration for the help preprocessor pipeline."""

from dataclasses import dataclass
import json
import logging
from pathlib import Path
from typing import Any

from .config import HelpPreprocessorConfig
from .html_parser import HelpHTMLParser
from .index_parser import HelpIndexParser
from .schemas import HelpCategory, HelpTopic


@dataclass(slots=True)
class ParsedArtifacts:
    """Container for parsed index and HTML normalization results."""

    root_category: HelpCategory
    diagnostics: dict[str, Any]


@dataclass(slots=True)
class HelpPreprocessorPipeline:
    """Coordinate parsing, graph building, and storage steps."""

    config: HelpPreprocessorConfig

    def run(self, dry_run: bool = False) -> None:
        """Execute the end-to-end pipeline."""

        artifacts = self._load_or_parse()
        category_count = self._count_categories(artifacts.root_category)
        topic_count = sum(1 for _ in artifacts.root_category.iter_topics())
        logging.info("Parsed %s categories and %s topics", category_count, topic_count)

        if dry_run:
            logging.debug("Dry-run mode enabled; skipping storage integration.")
            return

        raise NotImplementedError("Storage integration will be implemented in Phase 4.")

    def build_only(self) -> ParsedArtifacts:
        """Perform parsing and transformation without writing to storage."""

        return self._load_or_parse()

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
