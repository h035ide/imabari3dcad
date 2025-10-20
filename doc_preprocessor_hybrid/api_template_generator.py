from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from .config import PipelineConfig


TITLE_MARK = "〇"
HEADER_MARK = "■"
FULL_WIDTH_SPACE = "\u3000"


@dataclass
class TemplateMethod:
    name: str
    section: Optional[str]
    title: str
    return_text: str
    parameters: List[str]


def _normalize_line(text: str) -> str:
    return text.replace(FULL_WIDTH_SPACE, " ").strip()


def _looks_like_param(line: str) -> bool:
    stripped = _normalize_line(line)
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s*,?\s*//", stripped))


def parse_methods_from_doc(path: Path) -> List[TemplateMethod]:
    lines = path.read_text(encoding="utf-8").splitlines()
    methods: List[TemplateMethod] = []
    section: Optional[str] = None
    i = 0
    while i < len(lines):
        raw = lines[i]
        normalized = _normalize_line(raw)
        if not normalized:
            i += 1
            continue
        if normalized.startswith(HEADER_MARK):
            section = normalized[len(HEADER_MARK):].strip() or None
            i += 1
            continue
        if normalized.startswith(TITLE_MARK):
            title = normalized[len(TITLE_MARK):].strip()
            j = i + 1
            return_text = ""
            while j < len(lines) and not _normalize_line(lines[j]):
                j += 1
            if j < len(lines) and "返り値" in lines[j]:
                return_text = _normalize_line(lines[j])
                j += 1
            while j < len(lines) and not _normalize_line(lines[j]):
                j += 1
            if j >= len(lines):
                i = j
                continue
            signature_line = lines[j]
            signature_norm = _normalize_line(signature_line)
            match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)", signature_norm)
            if not match:
                i = j + 1
                continue
            name = match.group(1)
            parameters: List[str] = []
            k = j + 1
            while k < len(lines):
                candidate = lines[k]
                candidate_norm = _normalize_line(candidate)
                if not candidate_norm:
                    break
                if candidate_norm.startswith(TITLE_MARK) or candidate_norm.startswith(
                    HEADER_MARK
                ):
                    break
                if _looks_like_param(candidate):
                    parameters.append(candidate)
                k += 1
            methods.append(
                TemplateMethod(
                    name=name,
                    section=section,
                    title=title,
                    return_text=return_text,
                    parameters=parameters,
                )
            )
            i = k
            continue
        i += 1
    return methods


def build_template_xml(methods: Iterable[TemplateMethod]) -> ET.Element:
    root = ET.Element("apiTemplate")
    for method in methods:
        node = ET.SubElement(root, "method", name=method.name)
        if method.section:
            node.set("section", method.section)
        ET.SubElement(node, "title").text = method.title
        ET.SubElement(node, "return").text = method.return_text
        params_node = ET.SubElement(node, "parameters")
        for raw in method.parameters:
            params_node.append(_parameter_from_line(raw))
    return root


def _parameter_from_line(line: str) -> ET.Element:
    element = ET.Element("parameter")
    normalized = _normalize_line(line)
    match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*,?\s*//\s*(.+)$", normalized)
    if match:
        element.set("name", match.group(1))
        element.text = match.group(2)
    else:
        element.text = normalized
    return element


def generate_template(doc_path: Path, output_path: Path) -> None:
    methods = parse_methods_from_doc(doc_path)
    root = build_template_xml(methods)
    tree = ET.ElementTree(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="APIテンプレートXML生成")
    config = PipelineConfig()
    parser.add_argument(
        "--api-doc", type=Path, default=config.api_doc_path, help="api.txt のパス"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("doc_preprocessor_hybrid/out/api_template.xml"),
        help="生成するテンプレートXMLのパス",
    )
    args = parser.parse_args(argv)
    generate_template(args.api_doc, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())
