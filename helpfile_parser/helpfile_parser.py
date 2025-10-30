from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator, List, Optional

from bs4 import BeautifulSoup, Tag


_HEADING_PATTERN = re.compile(r"^h([1-4])$", re.IGNORECASE)


@dataclass(slots=True)
class Section:
    heading: str
    level: int
    content: str


@dataclass(slots=True)
class HelpDocument:
    source_path: Path
    title: str
    sections: List[Section] = field(default_factory=list)
    headings: List[str] = field(default_factory=list)
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    last_modified: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "source_path": str(self.source_path),
            "title": self.title,
            "headings": self.headings,
            "extracted_at": self.extracted_at.isoformat(timespec="seconds"),
            "last_modified": self.last_modified.isoformat(timespec="seconds")
            if self.last_modified
            else None,
            "sections": [asdict(section) for section in self.sections],
        }


def normalize_text(value: str) -> str:
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _decompose_noise_tags(soup: BeautifulSoup) -> None:
    for tag_name in ("script", "style", "noscript", "template"):
        for tag in soup.find_all(tag_name):
            tag.decompose()

    removable_media_tags = {
        "img",
        "video",
        "audio",
        "canvas",
        "iframe",
        "object",
        "embed",
        "source",
    }
    for tag_name in removable_media_tags:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    for tag in soup.find_all(src=True):
        if "media/" in tag["src"]:
            tag.decompose()

    for tag in soup.find_all(href=True):
        if "media/" in tag["href"]:
            tag.decompose()


def _extract_title(soup: BeautifulSoup) -> str:
    first_heading = soup.find(_HEADING_PATTERN)
    if isinstance(first_heading, Tag):
        text = normalize_text(first_heading.get_text(" ", strip=True))
        if text:
            return text

    title_tag = soup.find("title")
    if title_tag:
        text = normalize_text(title_tag.get_text(" ", strip=True))
        if text:
            return text

    body = soup.body or soup
    text = normalize_text(body.get_text(" ", strip=True))
    return text[:120] if text else "Untitled"


def _extract_sections(soup: BeautifulSoup) -> List[Section]:
    headings = soup.find_all(_HEADING_PATTERN)
    if not headings:
        body = soup.body or soup
        body_text = normalize_text(body.get_text(" ", strip=True))
        return [Section(heading="Body", level=0, content=body_text)] if body_text else []

    sections: List[Section] = []
    for heading in headings:
        if not isinstance(heading, Tag):
            continue
        level = int(heading.name[1])
        heading_text = normalize_text(heading.get_text(" ", strip=True))
        if not heading_text:
            continue

        content_parts: List[str] = []
        for sibling in heading.next_siblings:
            if isinstance(sibling, Tag):
                match = _HEADING_PATTERN.match(sibling.name or "")
                if match and int(match.group(1)) <= level:
                    break
                text = normalize_text(sibling.get_text(" ", strip=True))
            else:
                text = normalize_text(str(sibling))

            if text:
                content_parts.append(text)

        content = "\n".join(part for part in content_parts if part)
        sections.append(Section(heading=heading_text, level=level, content=content))

    return sections


def parse_help_html(source_path: Path, html_text: str) -> HelpDocument:
    soup = BeautifulSoup(html_text, "html.parser")
    _decompose_noise_tags(soup)

    body = soup.body or soup
    for br in body.find_all("br"):
        br.replace_with("\n")

    title = _extract_title(soup)
    sections = _extract_sections(soup)
    headings = [section.heading for section in sections]

    doc = HelpDocument(
        source_path=source_path,
        title=title,
        sections=sections,
        headings=headings,
    )
    return doc


def extract_help_document(path: Path, encoding: str = "utf-8") -> HelpDocument:
    html_text = path.read_text(encoding=encoding, errors="ignore")
    document = parse_help_html(path, html_text)
    try:
        stat = path.stat()
    except OSError:
        stat = None
    if stat:
        document.last_modified = datetime.utcfromtimestamp(stat.st_mtime)
    return document


def iter_help_documents(root: Path) -> Iterator[HelpDocument]:
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")

    patterns = ("*.html", "*.htm")
    for pattern in patterns:
        for path in sorted(root.rglob(pattern)):
            if any(part == "media" for part in path.parts):
                continue
            if path.is_dir():
                continue
            yield extract_help_document(path)


def _run_sample_unit_tests() -> None:
    sample_html = """
    <html>
      <head><title>Sample Doc</title></head>
      <body>
        <h1>Overview</h1>
        <p>This is an introduction.</p>
        <script>var noise = 1;</script>
        <h2>Details</h2>
        <p>Media content should vanish.</p>
        <img src="media/picture.png" alt="pic" />
      </body>
    </html>
    """
    document = parse_help_html(Path("sample.html"), sample_html)

    assert document.title == "Overview", "First heading should be used as title"
    assert len(document.sections) == 2, "Expected two sections"
    assert all("noise" not in section.content for section in document.sections)
    assert "picture" not in "\n".join(section.content for section in document.sections)
    assert document.sections[0].heading == "Overview"
    assert document.sections[1].heading == "Details"


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract structured text from EVOSHIP help HTML files."
    )
    subparsers = parser.add_subparsers(dest="command")

    extract_parser = subparsers.add_parser(
        "extract", help="Parse all HTML files under the given directory"
    )
    extract_parser.add_argument(
        "root",
        type=Path,
        help="Path to the EVOSHIP_HELP_FILES directory",
    )
    extract_parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write JSON output (defaults to stdout)",
    )

    subparsers.add_parser("self-test", help="Run built-in smoke tests")
    return parser


def _handle_extract_command(root: Path, output_path: Optional[Path]) -> int:
    documents = [doc.to_dict() for doc in iter_help_documents(root)]
    payload = json.dumps(documents, ensure_ascii=False, indent=2)

    if output_path:
        output_path.write_text(payload, encoding="utf-8")
    else:
        print(payload)
    return 0


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "self-test":
        _run_sample_unit_tests()
        print("Self-test passed.")
        return 0

    if args.command == "extract":
        try:
            return _handle_extract_command(args.root, args.output)
        except FileNotFoundError as exc:
            parser.error(str(exc))

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
