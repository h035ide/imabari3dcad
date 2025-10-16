"""Utilities for normalizing and resolving EvoShip API types."""

from __future__ import annotations

from typing import Iterable, Optional

from .models import ArrayInfo, TypeDefinition


class TypeRegistry:
    """Helper that normalizes raw type hints using known definitions."""

    __slots__ = ("definitions", "_lookup", "_aliases")

    def __init__(self, definitions: Iterable[TypeDefinition]):
        self.definitions = list(definitions)
        self._lookup = {
            self._normalize_key(defn.name): defn.name for defn in self.definitions
        }
        # Known aliases collected from API documents and historical output.
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
            # English to Japanese normalization often emitted by LLM
            "number": "浮動小数点",
            "length": "長さ",
            "object": "オブジェクト",
            "array": "配列",
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
        # Detect array notation like "Xの配列" or "X(配列)"
        qualifier: Optional[str] = None
        base = text
        if "の配列" in base:
            qualifier = "配列"
            base = base.replace("の配列", "")
        if "(配列)" in base:
            qualifier = "配列"
            base = base.replace("(配列)", "")
        # Normalize base type after trimming decorations like whitespace and full-width parens
        base = base.strip()
        normalized = self.normalize(base)
        array_info = ArrayInfo(qualifier=qualifier) if qualifier else None
        return normalized, array_info


__all__ = ["TypeRegistry"]
