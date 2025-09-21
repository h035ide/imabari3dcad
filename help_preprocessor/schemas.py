from __future__ import annotations

"""Structured data schemas for the help preprocessor."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional


@dataclass(slots=True)
class MediaAsset:
    """Represents a non-text resource referenced by the help documentation."""

    identifier: str
    path: Path
    media_type: str
    description: Optional[str] = None


@dataclass(slots=True)
class HelpLink:
    """Hyperlink reference extracted from a help document section."""

    href: str
    text: str
    target_id: Optional[str] = None


@dataclass(slots=True)
class HelpSection:
    """Fine-grained section of a help topic used for chunking and embeddings."""

    section_id: str
    title: Optional[str]
    content: str
    anchors: list[str] = field(default_factory=list)
    links: list[HelpLink] = field(default_factory=list)
    media: list[MediaAsset] = field(default_factory=list)


@dataclass(slots=True)
class HelpTopic:
    """Individual help page mapped to zero or more sections."""

    topic_id: str
    title: str
    source_path: Path
    sections: list[HelpSection] = field(default_factory=list)
    related: list[str] = field(default_factory=list)


@dataclass(slots=True)
class HelpCategory:
    """Hierarchical grouping for help topics based on index.txt definitions."""

    category_id: str
    name: str
    topics: list[HelpTopic] = field(default_factory=list)
    children: list["HelpCategory"] = field(default_factory=list)

    def iter_topics(self) -> Iterable[HelpTopic]:
        """Yield topics within this category recursively."""

        for topic in self.topics:
            yield topic
        for child in self.children:
            yield from child.iter_topics()
