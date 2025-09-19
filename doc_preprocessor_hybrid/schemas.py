from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


@dataclass
class TypeDefinition:
    name: str
    description: str
    examples: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        data: Dict[str, object] = {"name": self.name, "description": self.description}
        if self.examples:
            data["examples"] = self.examples
        return data


@dataclass
class Parameter:
    name: str
    type: str
    description: str = ""
    is_required: bool = False
    default_value: Optional[str] = None
    position: int = 0
    raw_type: Optional[str] = None

    def metadata(self) -> Dict[str, object]:
        meta: Dict[str, object] = {"position": self.position}
        if self.is_required:
            meta["is_required"] = self.is_required
        if self.default_value is not None:
            meta["default_value"] = self.default_value
        if self.raw_type and self.raw_type != self.type:
            meta["raw_type"] = self.raw_type
        return meta

    def to_dict(self) -> Dict[str, object]:
        data: Dict[str, object] = {
            "name": self.name,
            "type": self.type,
        }
        if self.description:
            data["description"] = self.description
        metadata = self.metadata()
        if metadata:
            data["metadata"] = metadata
        return data


@dataclass
class ReturnSpec:
    type: str = "void"
    description: str = ""
    is_array: bool = False
    raw_type: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass
class ApiEntry:
    entry_type: str
    name: str
    description: str = ""
    category: str = ""
    params: List[Parameter] = field(default_factory=list)
    properties: List[Parameter] = field(default_factory=list)
    returns: Optional[ReturnSpec] = None
    notes: Optional[str] = None
    implementation_status: str = "implemented"
    object_name: Optional[str] = None
    title_jp: Optional[str] = None
    raw_return: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        data = {
            "entry_type": self.entry_type,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "params": [p.to_dict() for p in self.params],
            "properties": [p.to_dict() for p in self.properties],
            "returns": self.returns.to_dict() if self.returns else None,
            "notes": self.notes,
            "implementation_status": self.implementation_status,
        }
        if self.object_name:
            data["object_name"] = self.object_name
        if self.title_jp:
            data["title_jp"] = self.title_jp
        if self.raw_return:
            data["raw_return"] = self.raw_return
        return data


@dataclass
class ApiBundle:
    type_definitions: List[TypeDefinition]
    api_entries: List[ApiEntry]
    checklist: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "checklist": self.checklist,
            "type_definitions": [t.to_dict() for t in self.type_definitions],
            "api_entries": [e.to_dict() for e in self.api_entries],
        }
