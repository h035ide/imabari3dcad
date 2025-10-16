"""Structured parser for EvoShip API documentation (``api.txt``)."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, List, Optional

from .models import (
    ApiEntry,
    ApiExtractionResult,
    ArrayInfo,
    ParameterDefinition,
    PropertyDefinition,
    ReturnDefinition,
    TypeDefinition,
)
from .type_parser import parse_type_definitions

_RETURN_PREFIX = re.compile(r"^返り値[:：]\s*(?P<body>.+)$")
_SECTION_PREFIX = re.compile(r"^■\s*(?P<body>.+)$")
_ENTRY_PREFIX = re.compile(r"^〇\s*(?P<body>.+)$")
_PROPERTY_HEADER = re.compile(r"^属性\s*$")
_COMMENT_SPLIT = re.compile(r"//+")
_OPTIONAL_KEYWORDS = ("空文字可", "省略可", "省略可能", "任意", "optional", "不要な場合", "指定しない場合")
_DEFAULT_PATTERNS = (
    re.compile(r"通常は\s*(?P<value>[^)）]+)"),
    re.compile(r"デフォルト(?:は|値)?\s*(?P<value>[^)）]+)"),
    re.compile(r"既定(?:値)?\s*(?P<value>[^)）]+)"),
)
_ARRAY_HINT = re.compile(r"配列")
_TYPE_IN_PAREN = re.compile(r"(?P<base>.+?)\((?P<qualifier>[^()]+)\)")


@dataclass(slots=True)
class _RawEntry:
    category: Optional[str] = None
    description: Optional[str] = None
    return_text: Optional[str] = None
    signature_lines: Optional[List[str]] = None
    property_lines: Optional[List[str]] = None

    def __post_init__(self) -> None:
        if self.signature_lines is None:
            self.signature_lines = []
        if self.property_lines is None:
            self.property_lines = []


class TypeRegistry:
    """Normalizes type names using the parsed type definitions."""

    def __init__(self, definitions: Iterable[TypeDefinition]):
        self._definitions = list(definitions)
        self._lookup = {
            self._normalize_key(defn.name): defn.name for defn in self._definitions
        }
        self._aliases = {
            "なし": "void",
            "void": "void",
            "bool": "bool",
            "boolean": "bool",
            "string": "文字列",
            "str": "文字列",
            "int": "整数",
            "integer": "整数",
            "float": "浮動小数点",
        }

    @staticmethod
    def _normalize_key(name: str) -> str:
        key = name.replace("\u3000", " ").strip().lower()
        key = key.replace("（", "(").replace("）", ")")
        return key

    def normalize(self, raw: Optional[str]) -> Optional[str]:
        if raw is None:
            return None
        candidate = raw.strip()
        if not candidate:
            return None
        candidate = candidate.replace("\u3000", " ")
        candidate = candidate.replace("（", "(").replace("）", ")")
        key = self._normalize_key(candidate)
        if key in self._aliases:
            return self._aliases[key]
        if key in self._lookup:
            return self._lookup[key]
        return candidate.strip()

    def extract_type(self, raw: Optional[str]) -> tuple[Optional[str], Optional[ArrayInfo]]:
        if raw is None:
            return None, None
        text = raw.strip()
        if not text:
            return None, None
        qualifier = None
        paren_match = _TYPE_IN_PAREN.match(text)
        if paren_match:
            text = paren_match.group("base").strip()
            qualifier = paren_match.group("qualifier").strip()
        if _ARRAY_HINT.search(raw):
            qualifier = "配列"
        normalized = self.normalize(text)
        array_info = ArrayInfo(qualifier=qualifier) if qualifier else None
        return normalized, array_info


class ApiExtractor:
    """High level helper that extracts structured API data."""

    def __init__(self, type_definitions: Iterable[TypeDefinition]):
        self.type_registry = TypeRegistry(type_definitions)

    @classmethod
    def from_documents(cls, api_text: str, type_text: str) -> ApiExtractionResult:
        type_defs = parse_type_definitions(type_text)
        extractor = cls(type_defs)
        entries = extractor.parse_api_text(api_text)
        return ApiExtractionResult(type_definitions=type_defs, api_entries=entries)

    def parse_api_text(self, text: str) -> List[ApiEntry]:
        raw_entries = self._collect_entries(text)
        entries: List[ApiEntry] = []
        for raw_entry in raw_entries:
            if raw_entry.property_lines and not raw_entry.signature_lines:
                entries.append(self._build_object_entry(raw_entry))
            else:
                entries.append(self._build_function_entry(raw_entry))
        return entries

    def _collect_entries(self, text: str) -> List[_RawEntry]:
        current_category: Optional[str] = None
        current_entry: Optional[_RawEntry] = None
        entries: List[_RawEntry] = []
        in_properties = False

        for raw_line in self._iter_lines(text):
            normalized = raw_line.replace("\u3000", " ")
            stripped = normalized.strip()
            if not stripped:
                if current_entry and current_entry.signature_lines:
                    current_entry.signature_lines.append("")
                continue

            section_match = _SECTION_PREFIX.match(stripped)
            if section_match:
                current_category = self._normalize_category(section_match.group("body"))
                continue

            entry_match = _ENTRY_PREFIX.match(stripped)
            if entry_match:
                if current_entry:
                    entries.append(current_entry)
                current_entry = _RawEntry(category=current_category, description=entry_match.group("body").strip())
                in_properties = False
                continue

            if current_entry is None:
                continue

            return_match = _RETURN_PREFIX.match(stripped)
            if return_match:
                current_entry.return_text = return_match.group("body").strip()
                continue

            if _PROPERTY_HEADER.match(stripped):
                in_properties = True
                continue

            if in_properties:
                if current_entry.property_lines is None:
                    current_entry.property_lines = []
                current_entry.property_lines.append(normalized.strip())
            else:
                if current_entry.signature_lines is None:
                    current_entry.signature_lines = []
                current_entry.signature_lines.append(normalized.rstrip())

        if current_entry:
            entries.append(current_entry)

        return entries

    @staticmethod
    def _normalize_category(text: str) -> str:
        text = text.strip()
        for token in ("のメソッド", "メソッド", "のプロパティ", "オブジェクト", "一覧"):
            if text.endswith(token):
                text = text[: -len(token)]
                break
        return text.replace("\u3000", " ").strip()

    @staticmethod
    def _iter_lines(text: str) -> Iterable[str]:
        for raw_line in text.splitlines():
            yield raw_line.replace("\ufeff", "")

    def _build_function_entry(self, raw: _RawEntry) -> ApiEntry:
        name, params = self._parse_signature(raw.signature_lines or [])
        returns = self._parse_return(raw.return_text)
        return ApiEntry(
            entry_type="function",
            name=name or (raw.description or ""),
            description=raw.description,
            category=raw.category,
            params=params,
            returns=returns,
            notes=None,
            implementation_status="implemented",
            properties=[],
        )

    def _build_object_entry(self, raw: _RawEntry) -> ApiEntry:
        properties = self._parse_properties(raw.property_lines or [])
        return ApiEntry(
            entry_type="object",
            name=self._extract_object_name(raw),
            description=raw.description,
            category=raw.category,
            params=[],
            returns=None,
            notes=None,
            implementation_status=None,
            properties=properties,
        )

    def _extract_object_name(self, raw: _RawEntry) -> str:
        if raw.signature_lines:
            candidate, _ = self._parse_signature(raw.signature_lines or [])
            if candidate:
                return candidate
        return raw.description or ""

    def _parse_signature(self, lines: List[str]) -> tuple[Optional[str], List[ParameterDefinition]]:
        header_line: Optional[str] = None
        params: List[ParameterDefinition] = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if header_line is None:
                header_line = stripped
                continue
            parsed_param = self._parse_parameter_line(stripped, len(params))
            if parsed_param:
                params.append(parsed_param)
        if header_line is None:
            return None, []
        name = header_line
        if "(" in header_line:
            name = header_line.split("(", 1)[0].strip()
        name = name.rstrip("();")
        return name, params

    def _parse_parameter_line(self, line: str, position: int) -> Optional[ParameterDefinition]:
        line = line.strip()
        if not line or line in {";", ")", ");"}:
            return None
        comment = None
        comment_match = _COMMENT_SPLIT.split(line, maxsplit=1)
        if len(comment_match) > 1:
            main_part = comment_match[0]
            comment = line[line.index("//") + 2:]
        else:
            main_part = line
        main_part = main_part.rstrip(",); ")
        main_part = main_part.strip()
        if not main_part:
            return None
        tokens = main_part.split()
        name = tokens[-1]
        raw_type = " ".join(tokens[:-1]) or None
        if comment:
            type_text, description = self._parse_comment(comment)
        else:
            type_text, description = None, None
        if type_text:
            raw_type = type_text
        normalized_type, array_info = self.type_registry.extract_type(raw_type)
        description = description or (comment.strip() if comment else None)
        is_required, default_value = self._infer_requirement(description)
        return ParameterDefinition(
            name=name.rstrip(","),
            position=position,
            type=normalized_type,
            description=description,
            is_required=is_required,
            default_value=default_value,
            array_info=array_info,
        )

    def _parse_properties(self, lines: List[str]) -> List[PropertyDefinition]:
        properties: List[PropertyDefinition] = []
        for line in lines:
            comment = None
            if "//" in line:
                before, after = line.split("//", 1)
                comment = after
                name = before.strip()
            else:
                name = line.strip()
            name = name.rstrip(":")
            type_text, description = self._parse_comment(comment) if comment else (None, None)
            normalized_type, array_info = self.type_registry.extract_type(type_text)
            description = description or (comment.strip() if comment else None)
            if not name:
                continue
            properties.append(
                PropertyDefinition(
                    name=name,
                    type=normalized_type,
                    description=description,
                    array_info=array_info,
                )
            )
        return properties

    def _parse_return(self, return_text: Optional[str]) -> ReturnDefinition:
        if not return_text or return_text.strip() == "なし":
            return ReturnDefinition(type="void", description="なし", is_array=False)
        text = return_text.strip()
        normalized_text = text.replace("\u3000", " ")
        is_array = bool(_ARRAY_HINT.search(normalized_text))
        type_candidate = normalized_text
        if "の配列" in normalized_text:
            type_candidate = normalized_text.rsplit("の配列", 1)[0]
        type_candidate = type_candidate.rstrip("配列").strip()
        normalized_type, _ = self.type_registry.extract_type(type_candidate)
        return ReturnDefinition(
            type=normalized_type or type_candidate,
            description=text,
            is_array=is_array,
        )

    @staticmethod
    def _parse_comment(comment: str) -> tuple[Optional[str], Optional[str]]:
        if comment is None:
            return None, None
        text = comment.replace("\u3000", " ").strip()
        text = text.replace("：", ":")
        if ":" in text:
            type_text, desc = text.split(":", 1)
            return type_text.strip(), desc.strip() or None
        return text.strip() or None, None

    @staticmethod
    def _infer_requirement(description: Optional[str]) -> tuple[bool, Optional[str]]:
        if not description:
            return True, None
        desc = description
        normalized = desc.replace("\u3000", " ")
        default_value: Optional[str] = None
        for pattern in _DEFAULT_PATTERNS:
            match = pattern.search(normalized)
            if match:
                value = match.group("value")
                value = value.strip().rstrip("。.")
                value = value.rstrip(")")
                value = value.rstrip("）")
                default_value = value
                break
        is_required = True
        if default_value:
            is_required = False
        else:
            if any(keyword in normalized for keyword in _OPTIONAL_KEYWORDS):
                is_required = False
        return is_required, default_value
