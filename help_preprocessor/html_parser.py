from __future__ import annotations

"""HTML parsing utilities for the help preprocessor."""

from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
import logging
import re
from pathlib import Path
from typing import Iterable, Sequence

from .schemas import HelpLink, HelpSection, MediaAsset


_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class HTMLDecodeDiagnostics:
    """Metadata describing how a help HTML file was decoded."""

    path: Path
    attempted_encodings: Sequence[str]
    selected_encoding: str
    had_bom: bool
    fallback_used: bool
    errors: dict[str, str]


class _TextExtractor(HTMLParser):
    """Simple HTML to text converter ignoring script/style tags."""

    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:  # pragma: no cover - HTMLParser base
        if tag in {"script", "style"}:
            self._skip_depth += 1
        if self._skip_depth == 0 and tag in {"br", "p", "li", "div"}:
            self._chunks.append('\n')

    def handle_endtag(self, tag: str) -> None:  # pragma: no cover - HTMLParser base
        if tag in {"script", "style"} and self._skip_depth:
            self._skip_depth -= 1
        if self._skip_depth == 0 and tag in {"p", "li", "div"}:
            self._chunks.append('\n')

    def handle_data(self, data: str) -> None:  # pragma: no cover - HTMLParser base
        if self._skip_depth:
            return
        text = data.strip()
        if text:
            self._chunks.append(unescape(text))

    def get_text(self) -> str:
        joined = ' '.join(chunk for chunk in self._chunks if chunk)
        joined = re.sub(r'\s+', ' ', joined)
        return joined.strip()

class HelpHTMLParser:
    """Parse Shift_JIS encoded EVOSHIP help HTML into structured sections."""

    def __init__(self, source_root: Path, encoding: str = "shift_jis") -> None:
        self.source_root = source_root
        self.encoding = encoding

    # ------------------------------------------------------------------
    # Normalization utilities
    # ------------------------------------------------------------------
    def read_normalized_html(self, html_path: Path) -> tuple[str, HTMLDecodeDiagnostics]:
        """Return UTF-8-ready HTML text and diagnostics for the source file."""

        raw = html_path.read_bytes()
        attempted = list(self._candidate_encodings())
        errors: dict[str, str] = {}
        decoded_text: str | None = None
        selected: str | None = None

        for enc in attempted:
            try:
                decoded_text = raw.decode(enc)
            except UnicodeDecodeError as exc:  # pragma: no cover - error path
                errors[enc] = f"decode error at byte {exc.start}: {exc.reason}"
            else:
                selected = enc
                break

        if decoded_text is None or selected is None:  # pragma: no cover - error path
            detail = ', '.join(f"{enc}: {msg}" for enc, msg in errors.items())
            raise UnicodeDecodeError(
                selected or self.encoding,
                raw,
                len(raw) - 1,
                len(raw),
                f"Unable to decode {html_path} using candidates {attempted}. Details: {detail}",
            )

        normalized = self._normalize_html(decoded_text)
        bom = raw.startswith(b'\xef\xbb\xbf')
        fallback = selected != self.encoding

        diagnostics = HTMLDecodeDiagnostics(
            path=html_path,
            attempted_encodings=attempted,
            selected_encoding=selected,
            had_bom=bom,
            fallback_used=fallback,
            errors=errors,
        )

        self._log_diagnostics(diagnostics)
        return normalized, diagnostics

    def _candidate_encodings(self) -> Sequence[str]:
        """Return ordered candidate encodings for Shift_JIS-like documents."""

        return (self.encoding, "cp932", "utf-8", "euc-jp")

    @staticmethod
    def _normalize_html(text: str) -> str:
        """Apply newline normalization to decoded HTML text."""
        return text.replace('\r\n', '\n').replace('\r', '\n')
    def _log_diagnostics(self, diagnostics: HTMLDecodeDiagnostics) -> None:

        """Emit debug-level logging for decode diagnostics."""

        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug(
                "Decoded %s using %s (fallback=%s, BOM=%s, attempts=%s, errors=%s)",
                diagnostics.path,
                diagnostics.selected_encoding,
                diagnostics.fallback_used,
                diagnostics.had_bom,
                diagnostics.attempted_encodings,
                diagnostics.errors,
            )

    # ------------------------------------------------------------------
    # Parsing utilities
    # ------------------------------------------------------------------
    def parse_file(self, html_path: Path) -> list[HelpSection]:
        """Return structured sections for a single HTML document."""

        if not html_path.exists():  # pragma: no cover - defensive
            raise FileNotFoundError(html_path)

        normalized, _ = self.read_normalized_html(html_path)
        title = self._extract_title(normalized) or html_path.stem
        text = self._extract_text(normalized)
        anchors = self._extract_anchors(normalized)
        links = self._extract_links(normalized)
        media = self._extract_media(html_path, normalized)

        section = HelpSection(
            section_id=f"{html_path.stem}#body",
            title=title,
            content=text,
            anchors=anchors,
            links=links,
            media=media,
        )
        return [section]

    def collect_media(self, html_path: Path) -> list[MediaAsset]:
        """Return media assets referenced within a help HTML document."""

        if not html_path.exists():  # pragma: no cover - defensive
            return []
        normalized, _ = self.read_normalized_html(html_path)
        return self._extract_media(html_path, normalized)

    def _extract_title(self, html: str) -> str | None:
        title_pattern = re.compile(r'<title[^>]*>(.*?)</title>', re.IGNORECASE | re.DOTALL)
        match = title_pattern.search(html)
        if match:
            return unescape(match.group(1).strip())
        heading_pattern = re.compile(r'<h1[^>]*>(.*?)</h1>', re.IGNORECASE | re.DOTALL)
        match = heading_pattern.search(html)
        if match:
            text = re.sub(r'<[^>]+>', ' ', match.group(1))
            return unescape(text).strip()
        return None

    def _extract_text(self, html: str) -> str:
        parser = _TextExtractor()
        parser.feed(html)
        return parser.get_text()

    def _extract_anchors(self, html: str) -> list[str]:
        pattern = re.compile(r'id="([^"]+)"', re.IGNORECASE)
        return sorted(set(pattern.findall(html)))

    def _extract_links(self, html: str) -> list[HelpLink]:
        pattern = re.compile(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
        links: list[HelpLink] = []
        for href, text in pattern.findall(html):
            clean_text = unescape(re.sub(r'<[^>]+>', ' ', text)).strip()
            target_id = href.split('#', 1)[1] if '#' in href else None
            links.append(HelpLink(href=href.strip(), text=clean_text or href.strip(), target_id=target_id))
        return links

    def _extract_media(self, html_path: Path, html: str) -> list[MediaAsset]:
        pattern = re.compile(r'<(img|video|audio|source)[^>]+(src|data)="([^"]+)"', re.IGNORECASE)
        media: list[MediaAsset] = []
        for tag, _, src in pattern.findall(html):
            asset_path = (html_path.parent / src).resolve()
            media.append(
                MediaAsset(
                    identifier=f"{html_path.stem}:{src}",
                    path=asset_path,
                    media_type=tag.lower(),
                )
            )
        return media
