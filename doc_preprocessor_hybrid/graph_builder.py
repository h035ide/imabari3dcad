from __future__ import annotations

from typing import Dict, List, Set

from .schemas import ApiBundle, ApiEntry


def _collect_type_nodes(entry: ApiEntry, nodes: Dict[str, Dict[str, object]]) -> None:
    def ensure_type(name: str) -> None:
        if not name:
            return
        if name.endswith("[]"):
            clean = name[:-2]
        else:
            clean = name
        if clean not in nodes:
            nodes[clean] = {"id": clean, "label": "Type", "properties": {"name": clean}}

    if entry.returns and entry.returns.type:
        ensure_type(entry.returns.type)
    for param in entry.params + entry.properties:
        ensure_type(param.type)


def build_graph_payload(bundle: ApiBundle) -> Dict[str, List[Dict[str, object]]]:
    nodes: Dict[str, Dict[str, object]] = {}
    relationships: List[Dict[str, object]] = []
    seen_objects: Set[str] = set()

    for entry in bundle.api_entries:
        if entry.object_name and entry.object_name not in seen_objects:
            nodes[entry.object_name] = {
                "id": entry.object_name,
                "label": "Object",
                "properties": {"name": entry.object_name},
            }
            seen_objects.add(entry.object_name)

        nodes.setdefault(
            entry.name,
            {
                "id": entry.name,
                "label": "Method",
                "properties": {
                    "name": entry.name,
                    "description": entry.description,
                    "category": entry.category,
                },
            },
        )

        if entry.object_name:
            relationships.append(
                {
                    "type": "BELONGS_TO",
                    "start": entry.name,
                    "end": entry.object_name,
                }
            )

        _collect_type_nodes(entry, nodes)

        if entry.returns and entry.returns.type:
            relationships.append(
                {
                    "type": "RETURNS",
                    "start": entry.name,
                    "end": entry.returns.type.rstrip("[]"),
                    "properties": {"raw_type": entry.returns.raw_type or entry.returns.type},
                }
            )

        for param in entry.params:
            param_node_id = f"{entry.name}:{param.name}"
            param_properties = {"name": param.name}
            if param.description:
                param_properties["description"] = param.description
            metadata = param.metadata() if hasattr(param, "metadata") else {}
            if metadata:
                param_properties["metadata"] = metadata
            nodes.setdefault(
                param_node_id,
                {
                    "id": param_node_id,
                    "label": "Parameter",
                    "properties": param_properties,
                },
            )
            relationships.append(
                {
                    "type": "HAS_PARAMETER",
                    "start": entry.name,
                    "end": param_node_id,
                }
            )
            relationships.append(
                {
                    "type": "HAS_TYPE",
                    "start": param_node_id,
                    "end": param.type.rstrip("[]"),
                }
            )

    # Add type_definitions as dedicated nodes (no source field)
    for typedef in getattr(bundle, "type_definitions", []) or []:
        if typedef.name and typedef.name not in nodes:
            nodes[typedef.name] = {
                "id": typedef.name,
                "label": "TypeDef",
                "properties": {
                    "name": typedef.name,
                    "description": typedef.description or "",
                },
            }

    return {"nodes": list(nodes.values()), "relationships": relationships}
