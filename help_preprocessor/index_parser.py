from __future__ import annotations

"""Parser for EVOSHIP help index definitions."""

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

from .schemas import HelpCategory, HelpTopic


@dataclass(slots=True)
class _ParsedLine:
    """Internal representation of parsed index.txt line tokens."""

    kind: str  # "category" | "topic"
    level: int
    title: str
    identifier: str | None


class HelpIndexParser:
    """Build hierarchical category metadata from index.txt files."""

    def __init__(self, index_path: Path, encoding: str = "shift_jis") -> None:
        self.index_path = index_path
        self.encoding = encoding
        self._errors: list[str] = []
        self._topic_ids: set[str] = set()
        self._category_ids: set[str] = set()

    def parse(self) -> HelpCategory:
        """Return the root category parsed from the index file."""

        if not self.index_path.exists():  # pragma: no cover - defensive guard
            raise FileNotFoundError(f"Index file not found: {self.index_path}")

        root = HelpCategory(category_id="root", name="root")
        stack: list[tuple[int, HelpCategory]] = [(0, root)]

        for lineno, raw in enumerate(self._iter_lines(), start=1):
            entry = self._classify_line(raw, lineno)
            if entry is None:
                continue

            if entry.kind == "category":
                parent = self._resolve_parent(stack, entry.level)
                category_id = self._ensure_unique_id(
                    entry.identifier or self._slugify(entry.title),
                    self._category_ids,
                    prefix="category",
                    lineno=lineno,
                )
                category = HelpCategory(category_id=category_id, name=entry.title)
                parent.children.append(category)
                stack.append((entry.level, category))
            else:  # topic
                parent = stack[-1][1]
                topic_id = self._ensure_unique_id(
                    entry.identifier or self._slugify(entry.title),
                    self._topic_ids,
                    prefix="topic",
                    lineno=lineno,
                )
                title = entry.title or topic_id
                source_path = self._resolve_topic_path(topic_id)
                topic = HelpTopic(
                    topic_id=topic_id,
                    title=title,
                    source_path=source_path,
                )
                parent.topics.append(topic)

        return root

    def iter_errors(self) -> Iterable[str]:
        """Yield human readable parsing diagnostics."""

        return iter(self._errors)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _iter_lines(self) -> Iterator[str]:
        text = self.index_path.read_text(encoding=self.encoding)
        for line in text.splitlines():
            yield line.rstrip()

    def _classify_line(self, line: str, lineno: int) -> _ParsedLine | None:
        stripped = line.strip()
        if not stripped:
            return None
        if stripped.startswith("#"):
            return None

        if stripped.startswith("*"):
            star_count = len(stripped) - len(stripped.lstrip("*"))
            title = stripped[star_count:].strip()
            if not title:
                self._errors.append(f"Line {lineno}: Empty category title.")
                return None
            identifier = self._extract_parenthetical_identifier(title)
            if identifier:
                title = title[: title.rfind("(")].strip()
            return _ParsedLine("category", star_count, title, identifier)

        identifier = self._extract_topic_identifier(stripped)
        title = stripped
        if identifier:
            if stripped.endswith(")") and "(" in stripped:
                title = stripped[: stripped.rfind("(")].strip()
            else:
                idx = stripped.rfind(identifier)
                title = stripped[:idx].rstrip()
        if not title:
            title = identifier or f"Untitled {lineno}"
            self._errors.append(f"Line {lineno}: Missing topic title, using '{title}'.")
        if identifier is None:
            self._errors.append(
                f"Line {lineno}: Missing topic identifier for '{title}'. Generating fallback."
            )
        level = self._infer_topic_level(line)
        return _ParsedLine("topic", level, title.strip(), identifier)

    def _infer_topic_level(self, original_line: str) -> int:
        whitespace = original_line[: len(original_line) - len(original_line.lstrip(" 	"))]
        if not whitespace:
            return 1
        tab_count = whitespace.count("	")
        if tab_count:
            return tab_count + 1
        space_count = len(whitespace)
        if space_count >= 4:
            return space_count // 4 + 1
        return 1

    def _extract_parenthetical_identifier(self, text: str) -> str | None:
        if text.endswith(")") and "(" in text:
            start = text.rfind("(")
            candidate = text[start + 1 : -1].strip()
            if candidate:
                return candidate
        return None

    def _extract_topic_identifier(self, text: str) -> str | None:
        paren = self._extract_parenthetical_identifier(text)
        if paren:
            return paren
        match = re.search(r"([A-Za-z0-9_.\-\/]+)$", text)
        if match:
            return match.group(1)
        return None

    def _slugify(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKC", text)
        normalized = normalized.lower()
        normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
        normalized = normalized.strip("_")
        return normalized or "item"

    def _ensure_unique_id(
        self,
        base_identifier: str,
        seen: set[str],
        *,
        prefix: str,
        lineno: int,
    ) -> str:
        candidate = base_identifier or prefix
        candidate = candidate.strip()
        if not candidate:
            candidate = prefix
        if candidate not in seen:
            seen.add(candidate)
            return candidate

        suffix = 2
        while f"{candidate}_{suffix}" in seen:
            suffix += 1
        new_identifier = f"{candidate}_{suffix}"
        seen.add(new_identifier)
        self._errors.append(
            f"Line {lineno}: Duplicate {prefix} identifier '{candidate}', using '{new_identifier}'."
        )
        return new_identifier

    def _resolve_parent(
        self,
        stack: list[tuple[int, HelpCategory]],
        level: int,
    ) -> HelpCategory:
        while stack and stack[-1][0] >= level:
            stack.pop()
        return stack[-1][1]

    def _resolve_topic_path(self, topic_id: str) -> Path:
        if topic_id.endswith(".html") or topic_id.endswith(".htm"):
            filename = topic_id
        else:
            filename = f"{topic_id}.html"
        return (self.index_path.parent / filename).resolve()
