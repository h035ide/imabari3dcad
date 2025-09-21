from __future__ import annotations

from typing import Dict, Iterable, Optional

from neo4j import GraphDatabase, basic_auth

from ..schemas import ApiBundle, ApiEntry, Parameter, TypeDefinition
from .config import Neo4jConnectionConfig


def _clear_existing_graph(tx) -> None:
    tx.run("MATCH (n:API) DETACH DELETE n")
    tx.run("MATCH (n:Type) DETACH DELETE n")


def _merge_type_definitions(tx, definitions: Iterable[TypeDefinition]) -> None:
    for definition in definitions:
        tx.run(
            """
            MERGE (t:Type {name: $name})
            SET t.description = $description,
                t.canonical_type = $canonical,
                t.py_type = $py_type,
                t.examples = $examples,
                t.one_of = $one_of
            """,
            name=definition.name,
            description=definition.description or "",
            canonical=definition.canonical_type,
            py_type=definition.py_type,
            examples=definition.examples or [],
            one_of=definition.one_of or [],
        )


def _merge_api_entry(tx, entry: ApiEntry) -> None:
    tx.run(
        """
        MERGE (a:API {name: $name})
        SET a.description = $description,
            a.category = $category,
            a.object_name = $object_name,
            a.title_jp = $title_jp,
            a.raw_return = $raw_return,
            a.implementation_status = $status,
            a.notes = $notes
        """,
        name=entry.name,
        description=entry.description or "",
        category=entry.category or "",
        object_name=entry.object_name or "",
        title_jp=entry.title_jp or "",
        raw_return=entry.raw_return or "",
        status=entry.implementation_status or "unknown",
        notes=entry.notes,
    )


def _merge_return(tx, entry: ApiEntry) -> None:
    if entry.returns is None:
        tx.run(
            """
            MATCH (a:API {name: $api_name})
            OPTIONAL MATCH (a)-[r:RETURNS]->(:Return)
            DELETE r
            """,
            api_name=entry.name,
        )
        return

    payload = entry.returns
    tx.run(
        """
        MATCH (a:API {name: $api_name})
        MERGE (r:Return {api_name: $api_name})
        SET r.type = $type,
            r.description = $description,
            r.is_array = $is_array,
            r.raw_type = $raw_type
        MERGE (a)-[:RETURNS]->(r)
        """,
        api_name=entry.name,
        type=payload.type,
        description=payload.description or "",
        is_array=payload.is_array,
        raw_type=payload.raw_type or "",
    )


def _merge_parameter(tx, api_name: str, parameter: Parameter) -> None:
    tx.run(
        """
        MATCH (a:API {name: $api_name})
        MERGE (p:Parameter {api_name: $api_name, name: $name})
        SET p.description = $description,
            p.position = $position,
            p.type_label = $type_label,
            p.is_required = $is_required,
            p.default_value = $default_value,
            p.raw_type = $raw_type,
            p.dimension = $dimension
        MERGE (a)-[rel:HAS_PARAM]->(p)
        SET rel.position = $position
        """,
        api_name=api_name,
        name=parameter.name,
        description=parameter.description or "",
        position=parameter.position,
        type_label=parameter.type,
        is_required=parameter.is_required,
        default_value=parameter.default_value,
        raw_type=parameter.raw_type or "",
        dimension=parameter.dimension,
    )


def _link_parameter_type(tx, api_name: str, parameter_name: str, type_name: Optional[str]) -> None:
    if not type_name:
        return
    tx.run(
        """
        MATCH (p:Parameter {api_name: $api_name, name: $param_name})
        MATCH (t:Type {name: $type_name})
        MERGE (p)-[:OF_TYPE]->(t)
        """,
        api_name=api_name,
        param_name=parameter_name,
        type_name=type_name,
    )


def _link_return_type(tx, api_name: str, type_name: Optional[str]) -> None:
    if not type_name:
        return
    tx.run(
        """
        MATCH (r:Return {api_name: $api_name})
        MATCH (t:Type {name: $type_name})
        MERGE (r)-[:OF_TYPE]->(t)
        """,
        api_name=api_name,
        type_name=type_name,
    )


def _normalise_type_name(raw: str, available_types: Dict[str, TypeDefinition]) -> Optional[str]:
    if not raw:
        return None
    candidates = [raw]
    if raw.endswith("[]"):
        candidates.append(raw[:-2])
    if "(" in raw and raw.endswith(")"):
        base = raw.split("(", 1)[0]
        candidates.append(base)
    for candidate in candidates:
        if candidate in available_types:
            return candidate
    return None


def store_bundle(bundle: ApiBundle, config: Neo4jConnectionConfig) -> Dict[str, object]:
    if not config.enabled:
        raise ValueError("Neo4j configuration is incomplete; set NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD")

    driver = GraphDatabase.driver(
        config.uri,
        auth=basic_auth(config.username, config.password),
    )

    type_lookup = {definition.name: definition for definition in bundle.type_definitions}

    stats = {
        "types": len(type_lookup),
        "apis": len(bundle.api_entries),
    }

    def _write(tx):
        if config.clear_existing:
            _clear_existing_graph(tx)
        _merge_type_definitions(tx, bundle.type_definitions)
        for entry in bundle.api_entries:
            _merge_api_entry(tx, entry)
            _merge_return(tx, entry)
            return_type_name = _normalise_type_name(entry.returns.type if entry.returns else None, type_lookup)
            if return_type_name:
                _link_return_type(tx, entry.name, return_type_name)
            for parameter in entry.params:
                _merge_parameter(tx, entry.name, parameter)
                type_name = _normalise_type_name(parameter.type, type_lookup)
                if type_name:
                    _link_parameter_type(tx, entry.name, parameter.name, type_name)

    with driver.session(database=config.database or None) as session:
        session.execute_write(_write)

    driver.close()
    return stats
