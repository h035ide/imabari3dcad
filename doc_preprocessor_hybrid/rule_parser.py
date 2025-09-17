from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, List, Tuple

from .config import PipelineConfig
from .schemas import ApiBundle, ApiEntry, Parameter, ReturnSpec, TypeDefinition


HEADER_RE = re.compile(r"^■(.+?)(?:のメソッド)?$")
TITLE_RE = re.compile(r"^〇(.+)$")
RETURN_RE = re.compile(r"^返り値[:：]\s*(.+)$")
METHOD_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*\($")
PARAM_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*,?\s*//\s*([^:：]+)[:：]\s*(.+)$")
CLOSING_RE = re.compile(r"\)\s*;?(?:\s*//.*)?$")
ARRAY_MARKERS = ("(配列)", "[]", "(array)")


def _normalize_text(text: str) -> str:
    text = text.replace("\ufeff", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return text


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _clean_type_name(raw: str) -> Tuple[str, bool]:
    name = raw.strip()
    is_array = any(marker in name for marker in ARRAY_MARKERS)
    if is_array:
        for marker in ARRAY_MARKERS:
            name = name.replace(marker, "")
        name = name.replace("(配列)", "")
    name = re.sub(r"\s*\(.+\)$", "", name).strip()
    mapping = {
        "string": "文字列",
        "text": "文字列",
        "str": "文字列",
        "float": "浮動小数点",
        "double": "浮動小数点",
        "number": "浮動小数点",
        "int": "整数",
        "integer": "整数",
        "bool": "bool",
        "boolean": "bool",
    }
    key = name.lower()
    name = mapping.get(key, name)
    return name, is_array


def _is_required(desc: str) -> bool:
    desc = desc or ""
    if "空欄不可" in desc or "必須" in desc:
        return True
    if "空欄可" in desc or "任意" in desc:
        return False
    return False


def _build_parameter(name: str, raw_type: str, description: str, position: int) -> Parameter:
    cleaned, is_array = _clean_type_name(raw_type)
    param = Parameter(
        name=name,
        type=cleaned,
        description=description.strip(),
        is_required=_is_required(description),
        position=position,
        raw_type=raw_type.strip(),
    )
    if is_array:
        param.type = f"{param.type}[]"
    return param


def _guess_return_type(desc: str) -> str:
    desc = desc or ""
    if re.search(r"\bID\b", desc, flags=re.IGNORECASE) or "要素ID" in desc:
        return "ID"
    return "不明"


def parse_type_definitions(text: str) -> List[TypeDefinition]:
    definitions: List[TypeDefinition] = []
    current_name = None
    current_lines: List[str] = []
    for line in _normalize_text(text).split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("■"):
            if current_name and current_lines:
                definitions.append(
                    TypeDefinition(name=current_name, description="\n".join(current_lines))
                )
            current_name = stripped.replace("■", "", 1).strip()
            current_lines = []
        elif current_name:
            current_lines.append(stripped)
    if current_name and current_lines:
        definitions.append(TypeDefinition(name=current_name, description="\n".join(current_lines)))
    return definitions


def _finalize_entry(entry: ApiEntry, entries: List[ApiEntry]) -> None:
    if entry.returns is None:
        entry.returns = ReturnSpec()
    entries.append(entry)


def parse_api_specs(text: str) -> List[ApiEntry]:
    entries: List[ApiEntry] = []
    lines = _normalize_text(text).split("\n")
    current_object = ""
    current_title = ""
    current_return = ""
    collecting = False
    current_entry: ApiEntry | None = None
    param_index = 0

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        header_match = HEADER_RE.match(line)
        if header_match:
            current_object = header_match.group(1).strip()
            i += 1
            continue
        title_match = TITLE_RE.match(line)
        if title_match:
            current_title = title_match.group(1).strip()
            i += 1
            if i < len(lines):
                ret_match = RETURN_RE.match(lines[i].strip())
                if ret_match:
                    current_return = ret_match.group(1).strip()
                    i += 1
            continue
        method_match = METHOD_RE.match(line)
        if method_match:
            method_name = method_match.group(1)
            current_entry = ApiEntry(
                entry_type="function",
                name=method_name,
                description=current_title,
                category=current_object,
                object_name=current_object,
                title_jp=current_title,
                raw_return=current_return,
                returns=ReturnSpec(type=_guess_return_type(current_return), description=current_return),
            )
            collecting = True
            param_index = 0
            i += 1
            continue
        if collecting and current_entry:
            param_match = PARAM_RE.match(line)
            if param_match:
                pname, ptype, pdesc = param_match.groups()
                parameter = _build_parameter(pname, ptype, pdesc, param_index)
                current_entry.params.append(parameter)
                param_index += 1
                if CLOSING_RE.search(line):
                    _finalize_entry(current_entry, entries)
                    current_entry = None
                    collecting = False
                i += 1
                continue
            if CLOSING_RE.search(line):
                idx_close = line.rfind(")")
                before = line[:idx_close]
                candidate = before.split(",")[-1].strip()
                comment = ""
                if "//" in line:
                    comment = line.split("//", 1)[1].strip()
                synthetic = candidate
                if comment:
                    synthetic = f"{candidate} // {comment}"
                pm2 = PARAM_RE.match(synthetic)
                if pm2:
                    pname, ptype, pdesc = pm2.groups()
                    parameter = _build_parameter(pname, ptype, pdesc, param_index)
                    current_entry.params.append(parameter)
                _finalize_entry(current_entry, entries)
                current_entry = None
                collecting = False
                i += 1
                continue
        i += 1
    return entries


def parse_api_documents(api_doc_path: Path | None = None, api_arg_path: Path | None = None) -> ApiBundle:
    config = PipelineConfig()
    doc_path = Path(api_doc_path) if api_doc_path else config.api_doc_path
    arg_path = Path(api_arg_path) if api_arg_path else config.api_arg_path

    api_text = _read_text_file(doc_path)
    arg_text = _read_text_file(arg_path)

    types = parse_type_definitions(arg_text)
    entries = parse_api_specs(api_text)

    checklist = ["parsed_api_doc", "parsed_api_arg"]

    return ApiBundle(type_definitions=types, api_entries=entries, checklist=checklist)


def dump_bundle(bundle: ApiBundle, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def generate_vector_chunks(entries: Iterable[ApiEntry]) -> Iterable[dict]:
    for entry in entries:
        params = "\n".join(
            f"- {p.name} ({p.type}): {p.description}" for p in entry.params
        )
        payload = {
            "id": entry.name,
            "object": entry.object_name,
            "title_jp": entry.title_jp,
            "content": "\n".join(
                piece
                for piece in [
                    f"機能: {entry.description}",
                    f"カテゴリ: {entry.category}",
                    f"返り値: {entry.returns.description if entry.returns else ''}",
                    params,
                ]
                if piece
            ),
        }
        yield payload
