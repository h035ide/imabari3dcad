import os
from pathlib import Path

import pytest

from help_preprocessor.html_parser import HelpHTMLParser


@pytest.fixture()
def temp_html(tmp_path: Path) -> Path:
    file_path = tmp_path / "sample.html"
    shift_jis_content = "テストタイトル".encode("shift_jis") + b"\r\n<body>\r\n<p>\x83e\x83X\x83g</p>\r\n</body>"
    file_path.write_bytes(shift_jis_content)
    return file_path


def test_read_normalized_html_shift_jis(temp_html: Path) -> None:
    parser = HelpHTMLParser(source_root=temp_html.parent)
    normalized, diag = parser.read_normalized_html(temp_html)

    assert "テストタイトル" in normalized
    assert diag.selected_encoding == "shift_jis"
    assert not diag.fallback_used
    assert diag.had_bom is False


def test_read_normalized_html_fallback(temp_html: Path) -> None:
    file_path = temp_html
    raw = "タイトル".encode("cp932") + b"\r\n<body>fallback</body>"
    file_path.write_bytes(raw)

    parser = HelpHTMLParser(source_root=file_path.parent, encoding="utf-8")
    normalized, diag = parser.read_normalized_html(file_path)

    assert "fallback" in normalized
    assert diag.selected_encoding == "cp932"
    assert diag.fallback_used is True


def test_read_normalized_html_bom(temp_html: Path) -> None:
    file_path = temp_html
    content = "<html>bom</html>".encode("utf-8")
    file_path.write_bytes(b"\xef\xbb\xbf" + content)

    parser = HelpHTMLParser(source_root=file_path.parent, encoding="shift_jis")
    normalized, diag = parser.read_normalized_html(file_path)

    assert "bom" in normalized
    assert diag.selected_encoding == "utf-8"
    assert diag.had_bom is True
