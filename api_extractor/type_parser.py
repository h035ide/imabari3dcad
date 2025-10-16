"""Parsers responsible for reading type definitions from ``api_arg.txt``."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, List

from .models import TypeDefinition

_TYPE_HEADER_RE = re.compile(r"^■\s*(?P<name>.+?)\s*$")


@dataclass(slots=True)
class _TypeAccumulator:
    name: str
    description_lines: List[str]

    def build(self) -> TypeDefinition:
        description = " ".join(line.strip() for line in self.description_lines if line.strip())
        return TypeDefinition(name=self.name.strip(), description=description)


def _iter_lines(text: str) -> Iterable[str]:
    for raw_line in text.splitlines():
        yield raw_line.replace("\ufeff", "").rstrip("\n")


def parse_type_definitions(text: str) -> List[TypeDefinition]:
    """Parse ``api_arg.txt`` content into :class:`TypeDefinition` objects."""

    accumulator: _TypeAccumulator | None = None
    definitions: List[TypeDefinition] = []

    for line in _iter_lines(text):
        normalized = line.replace("\u3000", " ")
        stripped = normalized.strip()
        if not stripped:
            if accumulator:
                accumulator.description_lines.append("")
            continue

        header_match = _TYPE_HEADER_RE.match(stripped)
        if header_match:
            if accumulator:
                definitions.append(accumulator.build())
            accumulator = _TypeAccumulator(name=header_match.group("name"), description_lines=[])
            continue

        if accumulator is None:
            # Skip preamble text prior to the first header.
            continue

        accumulator.description_lines.append(stripped)

    if accumulator:
        definitions.append(accumulator.build())

    return definitions
