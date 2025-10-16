"""Data models used by the EvoShip API extractor."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass(slots=True)
class TypeDefinition:
    """Represents a single type definition derived from ``api_arg.txt``."""

    name: str
    description: str


@dataclass(slots=True)
class ArrayInfo:
    """Captures supplemental information when a field represents an array."""

    qualifier: Optional[str] = None


@dataclass(slots=True)
class ParameterDefinition:
    """Represents a single function parameter."""

    name: str
    position: int
    type: Optional[str]
    description: Optional[str]
    is_required: bool
    default_value: Optional[str]
    array_info: Optional[ArrayInfo] = None


@dataclass(slots=True)
class ReturnDefinition:
    """Represents the return value for a function."""

    type: Optional[str]
    description: Optional[str]
    is_array: bool = False


@dataclass(slots=True)
class PropertyDefinition:
    """Represents a property belonging to an object-style entry."""

    name: str
    type: Optional[str]
    description: Optional[str]
    array_info: Optional[ArrayInfo] = None


@dataclass(slots=True)
class ApiEntry:
    """Represents a function or object entry extracted from the API documentation."""

    entry_type: str
    name: str
    description: Optional[str]
    category: Optional[str]
    params: List[ParameterDefinition] = field(default_factory=list)
    returns: Optional[ReturnDefinition] = None
    notes: Optional[str] = None
    implementation_status: Optional[str] = None
    properties: List[PropertyDefinition] = field(default_factory=list)


@dataclass(slots=True)
class ApiExtractionResult:
    """Container for the full extraction output."""

    type_definitions: List[TypeDefinition]
    api_entries: List[ApiEntry]

    def to_dict(self) -> dict:
        """Convert the dataclass tree into a plain ``dict`` suitable for JSON serialization."""

        return asdict(self)
