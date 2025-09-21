from pathlib import Path

import pytest

from help_preprocessor.html_parser import HelpHTMLParser


@pytest.fixture()
def temp_html(tmp_path: Path) -> Path:
    file_path = tmp_path / "sample.html"
    html = "<html><body><p>Test</p></body></html>"
    file_path.write_bytes(html.encode("shift_jis"))
    return file_path


def test_read_normalized_html_shift_jis(temp_html: Path) -> None:
    parser = HelpHTMLParser(source_root=temp_html.parent)
    normalized, diag = parser.read_normalized_html(temp_html)

    assert "Test" in normalized
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


def test_parse_file_sections(tmp_path: Path) -> None:
    source_root = tmp_path
    media_dir = source_root / "media"
    media_dir.mkdir()
    (media_dir / "image.png").write_bytes(b"fake")

    html_content = """
    <html>
      <head><title>Doc Title</title></head>
      <body>
        <p>Intro text before headings.</p>
        <h2 id="overview">Overview</h2>
        <p>Overview paragraph with <a href="#details">details link</a>.</p>
        <h3>Details</h3>
        <p>More text <img src="media/image.png" /></p>
      </body>
    </html>
    """
    html_path = source_root / "doc.html"
    html_path.write_bytes(html_content.encode("shift_jis"))

    parser = HelpHTMLParser(source_root)
    sections = parser.parse_file(html_path)

    assert len(sections) == 3
    intro, overview, details = sections
    assert intro.section_id == "doc#intro"
    assert "Intro text" in intro.content
    assert overview.section_id == "doc#overview"
    assert overview.title == "Overview"
    assert overview.links and overview.links[0].href == "#details"
    assert details.section_id.startswith("doc#details")
    assert details.media and details.media[0].path.name == "image.png"


