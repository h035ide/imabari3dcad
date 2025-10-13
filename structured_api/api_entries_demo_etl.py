#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ETL utility that loads API entry metadata into Neo4j."""

from __future__ import annotations

import argparse
import copy
import json
import logging
import logging.handlers
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from dotenv import load_dotenv


LOGGER = logging.getLogger("api_entries_etl")

log_file_path = Path(__file__).with_name("api_entries_demo_etl.log")

console_handler = logging.StreamHandler(sys.stdout)
console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
console_handler.setFormatter(console_formatter)
console_handler.setLevel(logging.INFO)
LOGGER.addHandler(console_handler)

file_handler = logging.handlers.RotatingFileHandler(
    log_file_path,
    maxBytes=10 * 1024 * 1024,
    backupCount=3,
    mode="a",
    encoding="utf-8",
)
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
file_handler.setLevel(logging.DEBUG)
LOGGER.addHandler(file_handler)

LOGGER.setLevel(logging.DEBUG)
LOGGER.debug(
    "ログ設定完了 - ファイル: %s, コンソール: INFO以上, ファイル: DEBUG以上", log_file_path
)
LOGGER.info("ログファイルに保存中: %s", log_file_path)


MANAGED_TAG = "api_entries_etl"


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return str(value)


def _safe_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return _stringify(value)


@dataclass(frozen=True)
class Node:
    label: str
    uid: str
    props: Dict[str, Any]


@dataclass(frozen=True)
class Relation:
    src_uid: str
    rel_type: str
    dst_uid: str
    props: Optional[Dict[str, Any]] = None


@dataclass
class GraphElement:
    nodes: List[Node] = field(default_factory=list)
    relations: List[Relation] = field(default_factory=list)

    def extend(self, other: "GraphElement") -> None:
        self.nodes.extend(other.nodes)
        self.relations.extend(other.relations)

    def merge(self, *elements: "GraphElement") -> "GraphElement":
        merged = GraphElement(nodes=list(self.nodes), relations=list(self.relations))
        for element in elements:
            merged.nodes.extend(element.nodes)
            merged.relations.extend(element.relations)
        return merged


@dataclass
class SourceSpec:
    text: Optional[str] = None
    path: Optional[str] = None

    @classmethod
    def from_raw(cls, raw: Any) -> "SourceSpec":
        if not isinstance(raw, dict):
            return cls()
        text = raw.get("text")
        path = raw.get("path")
        return cls(
            text=_stringify(text) if text is not None else None,
            path=_stringify(path) if path is not None else None,
        )

    def is_empty(self) -> bool:
        return not (self.text or self.path)


@dataclass
class ParameterCase:
    name: str
    description: Optional[str] = None

    @classmethod
    def from_items(cls, key: Any, value: Any) -> "ParameterCase":
        return cls(name=_stringify(key), description=_stringify(value) if value is not None else None)


@dataclass
class ParameterSpec:
    name: str
    param_type: Optional[str]
    position: int
    description: Optional[str]
    cases: List[ParameterCase] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: Dict[str, Any], index: int) -> "ParameterSpec":
        raw_copy = copy.deepcopy(raw)
        name = raw_copy.get("name")
        name_str = _stringify(name).strip() if name is not None else ""
        if not name_str:
            name_str = f"param_{index}"
        param_type = raw_copy.get("type")
        param_type_str = _stringify(param_type) if param_type is not None else None
        description = raw_copy.get("description")
        description_str = _stringify(description) if description is not None else None
        position = raw_copy.get("position", index)
        cases_raw = raw_copy.get("case")
        cases: List[ParameterCase] = []
        if isinstance(cases_raw, dict):
            for key, value in cases_raw.items():
                cases.append(ParameterCase.from_items(key, value))
        return cls(
            name=name_str,
            param_type=param_type_str,
            position=position,
            description=description_str,
            cases=cases,
            raw=raw_copy,
        )


@dataclass
class ReturnSpec:
    return_type: Optional[str]
    description: Optional[str]
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: Any) -> Optional["ReturnSpec"]:
        if not isinstance(raw, dict):
            return None
        raw_copy = copy.deepcopy(raw)
        return cls(
            return_type=_stringify(raw_copy.get("type")) if raw_copy.get("type") is not None else None,
            description=_stringify(raw_copy.get("description")) if raw_copy.get("description") is not None else None,
            raw=raw_copy,
        )


@dataclass
class PropertyOption:
    name: Optional[str]
    value: Optional[str]
    description: Optional[str]
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: Any) -> Optional["PropertyOption"]:
        if not isinstance(raw, dict):
            return None
        raw_copy = copy.deepcopy(raw)
        name = raw_copy.get("name")
        value = raw_copy.get("value")
        description = raw_copy.get("description")
        return cls(
            name=_stringify(name).strip() if name is not None else None,
            value=_stringify(value) if value is not None else None,
            description=_stringify(description) if description is not None else None,
            raw=raw_copy,
        )


@dataclass
class PropertySpec:
    name: str
    property_type: Optional[str]
    unit: Optional[str]
    default: Any
    description: Optional[str]
    source: SourceSpec
    options: List[PropertyOption] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: Dict[str, Any], index: int) -> "PropertySpec":
        raw_copy = copy.deepcopy(raw)
        name = raw_copy.get("name")
        name_str = _stringify(name).strip() if name is not None else ""
        if not name_str:
            name_str = f"property_{index}"
        property_type = raw_copy.get("type")
        unit = raw_copy.get("unit")
        description = raw_copy.get("description")
        options_raw = raw_copy.get("options")
        options: List[PropertyOption] = []
        if isinstance(options_raw, list):
            for option_entry in options_raw:
                option = PropertyOption.from_raw(option_entry)
                if option:
                    options.append(option)
        return cls(
            name=name_str,
            property_type=_stringify(property_type) if property_type is not None else None,
            unit=_stringify(unit) if unit is not None else None,
            default=raw_copy.get("default"),
            description=_stringify(description) if description is not None else None,
            source=SourceSpec.from_raw(raw_copy.get("source")),
            options=options,
            raw=raw_copy,
        )


@dataclass
class ApiEntryRecord:
    index: int
    name: str
    category: Optional[str]
    entry_type: Optional[str]
    description: Optional[str]
    pseudo_code: Optional[str]
    parameters: List[ParameterSpec] = field(default_factory=list)
    returns: Optional[ReturnSpec] = None
    properties: List[PropertySpec] = field(default_factory=list)
    source: SourceSpec = field(default_factory=SourceSpec)
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, payload: Dict[str, Any], index: int) -> Optional["ApiEntryRecord"]:
        if not isinstance(payload, dict):
            return None
        raw_copy = copy.deepcopy(payload)
        name = raw_copy.get("name")
        name_str = _stringify(name).strip() if name is not None else ""
        if not name_str:
            return None
        category = raw_copy.get("category")
        entry_type = raw_copy.get("entry_type")
        description = raw_copy.get("description")
        pseudo_code = raw_copy.get("pseudo_code")

        parameters: List[ParameterSpec] = []
        params_raw = raw_copy.get("params")
        if isinstance(params_raw, list):
            for idx, param_entry in enumerate(params_raw):
                if isinstance(param_entry, dict):
                    parameters.append(ParameterSpec.from_raw(param_entry, idx))

        properties: List[PropertySpec] = []
        props_raw = raw_copy.get("properties")
        if isinstance(props_raw, list):
            for idx, prop_entry in enumerate(props_raw):
                if isinstance(prop_entry, dict):
                    properties.append(PropertySpec.from_raw(prop_entry, idx))

        return cls(
            index=index,
            name=name_str,
            category=_stringify(category).strip() if category else None,
            entry_type=_stringify(entry_type).strip() if entry_type else None,
            description=_stringify(description) if description is not None else None,
            pseudo_code=_stringify(pseudo_code) if pseudo_code is not None else None,
            parameters=parameters,
            returns=ReturnSpec.from_raw(raw_copy.get("returns")),
            properties=properties,
            source=SourceSpec.from_raw(raw_copy.get("source")),
            raw=raw_copy,
        )

    def primary_text(self) -> str:
        return MetadataProcessor.build_text(self.description or "", self.source.text or "")


class GraphBuilderConfig:
    def __init__(self, debug: bool = False):
        self.managed_tag = MANAGED_TAG
        self.debug = debug
        self.node_count = 0
        self.relation_count = 0
        self.created_nodes: Dict[str, Node] = {}
        self.created_relations: List[Relation] = []


class MetadataProcessor:
    @staticmethod
    def build_text(description: str, source_text: str) -> str:
        parts = [part.strip() for part in (description, source_text) if part]
        return "\n\n".join(parts)


class NodeFactory:
    def __init__(self, config: GraphBuilderConfig) -> None:
        self.config = config

    def normalize_uid(self, fragment: Any) -> str:
        text = _stringify(fragment)
        sanitized = text.replace("\r", " ").replace("\n", " ").replace("\t", " ").strip()
        if not sanitized:
            return "__empty__"
        return " ".join(sanitized.split())

    def create_node(self, label: str, uid: str, **props: Any) -> Node:
        normalized_uid = self.normalize_uid(uid)
        clean_props = {k: v for k, v in props.items() if v is not None}
        clean_props["managed_tag"] = self.config.managed_tag

        if self.config.debug:
            self.config.node_count += 1
            LOGGER.debug("[Node #%s] Created %s: %s", self.config.node_count, label, normalized_uid)
            for key, value in clean_props.items():
                if key == "managed_tag":
                    continue
                value_str = str(value)
                if len(value_str) > 120:
                    value_str = value_str[:117] + "..."
                LOGGER.debug("  %s: %s", key, value_str)

        node = Node(label=label, uid=normalized_uid, props=clean_props)

        if self.config.debug:
            self.config.created_nodes[normalized_uid] = node

        return node


class RelationFactory:
    def __init__(self, config: GraphBuilderConfig, node_factory: NodeFactory) -> None:
        self.config = config
        self.node_factory = node_factory

    def create_relation(self, src_uid: str, rel_type: str, dst_uid: str, **props: Any) -> Relation:
        rel_props = {k: v for k, v in props.items() if v is not None}
        rel_props.setdefault("managed_tag", self.config.managed_tag)

        normalized_src = self.node_factory.normalize_uid(src_uid)
        normalized_dst = self.node_factory.normalize_uid(dst_uid)

        if self.config.debug:
            self.config.relation_count += 1
            LOGGER.debug(
                "[Relation #%s] Created %s: %s -> %s",
                self.config.relation_count,
                rel_type,
                normalized_src,
                normalized_dst,
            )
            if normalized_src not in self.config.created_nodes:
                LOGGER.warning("Source node '%s' not found when creating relation", normalized_src)
            if normalized_dst not in self.config.created_nodes:
                LOGGER.warning("Destination node '%s' not found when creating relation", normalized_dst)

        relation = Relation(
            src_uid=normalized_src,
            rel_type=rel_type,
            dst_uid=normalized_dst,
            props=rel_props or None,
        )

        if self.config.debug:
            self.config.created_relations.append(relation)

        return relation


class ApiEntryTransformer:
    def __init__(
        self,
        node_factory: NodeFactory,
        relation_factory: RelationFactory,
        entry_index: Dict[str, ApiEntryRecord],
    ):
        self.node_factory = node_factory
        self.relation_factory = relation_factory
        self.entry_index = entry_index

    def to_graph_element(self, record: ApiEntryRecord) -> GraphElement:
        element = GraphElement()

        entry_uid = f"api_entry::{record.name}"
        entry_node = self.node_factory.create_node(
            "APIEntry",
            entry_uid,
            name=record.name,
            category=record.category,
            entry_type=record.entry_type,
            description=record.description,
            pseudo_code=record.pseudo_code,
            text=record.primary_text() or None,
            raw_json=_safe_json(record.raw),
            position=record.index,
        )
        element.nodes.append(entry_node)

        collection_uid = "api_entries::collection"
        element.relations.append(
            self.relation_factory.create_relation(collection_uid, "HAS_ENTRY", entry_uid)
        )

        if record.category:
            category_uid = f"category::{record.category}"
            category_node = self.node_factory.create_node(
                "Category", category_uid, name=record.category
            )
            element.nodes.append(category_node)
            element.relations.append(
                self.relation_factory.create_relation(entry_uid, "IN_CATEGORY", category_uid)
            )

        if record.entry_type:
            entry_type_uid = f"entry_type::{record.entry_type}"
            type_node = self.node_factory.create_node(
                "EntryType", entry_type_uid, name=record.entry_type
            )
            element.nodes.append(type_node)
            element.relations.append(
                self.relation_factory.create_relation(entry_uid, "HAS_ENTRY_TYPE", entry_type_uid)
            )

        param_lookup: Dict[str, str] = {}
        for param in record.parameters:
            param_uid = f"param::{record.name}::{param.name}"
            param_node = self.node_factory.create_node(
                "Parameter",
                param_uid,
                name=param.name or None,
                param_type=param.param_type,
                position=param.position,
                description=param.description,
                raw_json=_safe_json(param.raw),
            )
            element.nodes.append(param_node)
            element.relations.append(
                self.relation_factory.create_relation(entry_uid, "HAS_PARAMETER", param_uid)
            )

            if param.name:
                param_lookup[param.name.lower()] = param_uid

            for case in param.cases:
                case_uid = f"{param_uid}::case::{case.name}"
                case_node = self.node_factory.create_node(
                    "ParameterCase",
                    case_uid,
                    name=case.name,
                    description=case.description,
                )
                element.nodes.append(case_node)
                element.relations.append(
                    self.relation_factory.create_relation(param_uid, "HAS_CASE_OPTION", case_uid)
                )

        return_element = self._build_return(record, entry_uid)
        element.extend(return_element)

        pseudo_element = self._build_pseudo_code(record, entry_uid, param_lookup)
        element.extend(pseudo_element)

        property_element = self._build_properties(record, entry_uid)
        element.extend(property_element)

        if not record.source.is_empty():
            source_uid_fragment = record.source.path or "inline"
            source_uid = (
                f"source::{record.name}::{self.node_factory.normalize_uid(source_uid_fragment)}"
            )
            source_node = self.node_factory.create_node(
                "Source",
                source_uid,
                text=record.source.text,
                path=record.source.path,
            )
            element.nodes.append(source_node)
            element.relations.append(
                self.relation_factory.create_relation(entry_uid, "CITED_FROM", source_uid)
            )

        return element

    def _build_pseudo_code(
        self,
        record: ApiEntryRecord,
        entry_uid: str,
        param_lookup: Dict[str, str],
    ) -> GraphElement:
        element = GraphElement()
        pseudo_clean = (record.pseudo_code or "").strip()
        if not pseudo_clean:
            return element

        callee: Optional[str] = None
        args_list: List[str] = []
        match = re.match(r"^\s*([A-Za-z_][\w]*)\s*\((.*)\)\s*$", pseudo_clean)
        if match:
            callee = match.group(1)
            args_body = match.group(2).strip()
            if args_body:
                args_list = [arg.strip() for arg in args_body.split(",") if arg.strip()]
        else:
            callee = pseudo_clean

        pseudo_uid = f"pseudo_code::{record.name}"
        pseudo_node = self.node_factory.create_node(
            "PseudoCode",
            pseudo_uid,
            code=pseudo_clean,
            callee=callee,
            argument_count=len(args_list),
            arguments_json=_safe_json(args_list) if args_list else None,
        )
        element.nodes.append(pseudo_node)
        element.relations.append(
            self.relation_factory.create_relation(entry_uid, "HAS_PSEUDO_CODE", pseudo_uid)
        )

        for index, argument in enumerate(args_list):
            arg_uid = f"{pseudo_uid}::arg::{index}"
            normalized_arg = argument.lower()
            arg_node = self.node_factory.create_node(
                "PseudoCodeArgument",
                arg_uid,
                text=argument,
                position=index,
                normalized_text=normalized_arg,
            )
            element.nodes.append(arg_node)
            element.relations.append(
                self.relation_factory.create_relation(pseudo_uid, "HAS_ARGUMENT", arg_uid)
            )

            matched_param_uid = param_lookup.get(normalized_arg)
            if matched_param_uid:
                element.relations.append(
                    self.relation_factory.create_relation(
                        arg_uid,
                        "ARGUMENT_MATCHES_PARAMETER",
                        matched_param_uid,
                    )
                )

        return element

    def _build_return(self, record: ApiEntryRecord, entry_uid: str) -> GraphElement:
        element = GraphElement()
        if not record.returns:
            return element

        return_uid = f"return::{record.name}"
        return_node = self.node_factory.create_node(
            "ReturnValue",
            return_uid,
            return_type=record.returns.return_type,
            description=record.returns.description,
            raw_json=_safe_json(record.returns.raw),
        )
        element.nodes.append(return_node)
        element.relations.append(
            self.relation_factory.create_relation(entry_uid, "HAS_RETURN", return_uid)
        )

        target_uid = self._resolve_return_target(record)
        if target_uid:
            element.relations.append(
                self.relation_factory.create_relation(
                    return_uid,
                    "RETURNS_ENTRY",
                    target_uid,
                )
            )

        return element

    def _resolve_return_target(self, record: ApiEntryRecord) -> Optional[str]:
        candidates = [record.returns.return_type, record.returns.description if record.returns else None]
        for candidate in candidates:
            if not candidate:
                continue
            key = candidate.strip().lower()
            if not key:
                continue
            target = self.entry_index.get(key)
            if target:
                return f"api_entry::{target.name}"
        return None

    def _build_properties(self, record: ApiEntryRecord, entry_uid: str) -> GraphElement:
        element = GraphElement()
        property_uid_map: Dict[int, str] = {}

        for prop_index, prop in enumerate(record.properties):
            prop_uid = f"property::{record.name}::{prop.name}"
            property_node = self.node_factory.create_node(
                "Property",
                prop_uid,
                name=prop.name or None,
                property_type=prop.property_type,
                unit=prop.unit,
                default_value=_stringify(prop.default)
                if prop.default is not None
                else None,
                default_json=_safe_json(prop.default)
                if prop.default is not None
                else None,
                description=prop.description,
                raw_json=_safe_json(prop.raw),
                position=prop_index,
            )
            element.nodes.append(property_node)
            property_uid_map[prop_index] = property_node.uid
            element.relations.append(
                self.relation_factory.create_relation(entry_uid, "HAS_PROPERTY", property_node.uid)
            )

            if not prop.source.is_empty():
                source_uid_fragment = prop.source.path or prop.name or f"property_{prop_index}"
                source_uid = (
                    f"source::{record.name}::property::{self.node_factory.normalize_uid(source_uid_fragment)}"
                )
                source_node = self.node_factory.create_node(
                    "Source",
                    source_uid,
                    text=prop.source.text,
                    path=prop.source.path,
                )
                element.nodes.append(source_node)
                element.relations.append(
                    self.relation_factory.create_relation(property_node.uid, "CITED_FROM", source_uid)
                )

        if (record.entry_type or "").lower() == "object":
            for prop_index, prop in enumerate(record.properties):
                property_uid = property_uid_map.get(prop_index)
                if not property_uid:
                    continue
                for opt_index, option in enumerate(prop.options):
                    option_uid = f"{property_uid}::option::{option.name or f'option_{opt_index}'}"
                    option_node = self.node_factory.create_node(
                        "PropertyOption",
                        option_uid,
                        name=option.name,
                        description=option.description,
                        value=option.value,
                        position=opt_index,
                        raw_json=_safe_json(option.raw),
                    )
                    element.nodes.append(option_node)
                    element.relations.append(
                        self.relation_factory.create_relation(property_uid, "HAS_OPTION", option_uid)
                    )

        return element


class GraphBuilder:
    def __init__(self, debug: bool = False):
        self.config = GraphBuilderConfig(debug)
        self.node_factory = NodeFactory(self.config)
        self.relation_factory = RelationFactory(self.config, self.node_factory)
        self.transformer: Optional[ApiEntryTransformer] = None

    def build_graph_elements(
        self, records: Sequence[ApiEntryRecord]
    ) -> Tuple[List[Node], List[Relation]]:
        LOGGER.debug("GraphBuilder.build_graph_elements開始: %s件のエントリ", len(records))
        nodes_map: Dict[str, Node] = {}
        relations: List[Relation] = []

        collection_uid = "api_entries::collection"
        collection_node = self.node_factory.create_node(
            "ApiEntryCollection",
            collection_uid,
            name="api_entries",
        )
        nodes_map[collection_uid] = collection_node

        entry_index = {
            record.name.strip().lower(): record
            for record in records
            if record.name.strip()
        }
        self.transformer = ApiEntryTransformer(
            self.node_factory,
            self.relation_factory,
            entry_index,
        )

        for record in records:
            if self.config.debug:
                LOGGER.debug("Processing API entry #%s: %s", record.index + 1, record.name)
            element = self.transformer.to_graph_element(record)
            for node in element.nodes:
                nodes_map[node.uid] = node
            relations.extend(element.relations)

        final_nodes = list(nodes_map.values())

        LOGGER.debug(
            "GraphBuilder.build_graph_elements完了: ノード%s件, リレーション%s件",
            len(final_nodes),
            len(relations),
        )

        if self.config.debug:
            LOGGER.debug(
                "デバッグ統計: ノード作成数=%s, リレーション作成数=%s",
                self.config.node_count,
                self.config.relation_count,
            )

        return final_nodes, relations


def load_api_entries(json_path: Path) -> List[ApiEntryRecord]:
    LOGGER.debug("APIエントリJSONファイルを読み込み開始: %s", json_path)
    with json_path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)

    entries_raw = payload.get("api_entries") if isinstance(payload, dict) else None
    if not isinstance(entries_raw, list):
        raise ValueError("JSON のトップレベルに 'api_entries' (list) が必要です")

    records: List[ApiEntryRecord] = []
    for index, raw_entry in enumerate(entries_raw):
        record = ApiEntryRecord.from_raw(raw_entry, index)
        if record:
            records.append(record)
        else:
            LOGGER.warning("Skipping invalid API entry at index %s: %s", index, raw_entry)

    LOGGER.debug("APIエントリ読み込み完了: %s件", len(records))
    return records


def normalize_neo4j_uri(uri: str) -> str:
    if not uri:
        return uri
    trimmed = str(uri).strip().replace("　", " ")
    if (trimmed.startswith("\"") and trimmed.endswith("\"")) or (
        trimmed.startswith("'") and trimmed.endswith("'")
    ):
        trimmed = trimmed[1:-1]
    if "://" not in trimmed:
        trimmed = f"bolt://{trimmed}"
    return trimmed


def persist_to_neo4j(
    *,
    uri: str,
    username: str,
    password: str,
    database: Optional[str],
    nodes: List[Node],
    relations: List[Relation],
    wipe: bool = False,
    add_entity_label: bool = True,
) -> Tuple[int, int]:
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(uri, auth=(username, password))

    session_kwargs: Dict[str, Any] = {}
    if database:
        session_kwargs["database"] = database

    with driver.session(**session_kwargs) as session:
        constraint_queries = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:APIEntry) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Parameter) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:ReturnValue) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Category) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:EntryType) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:ParameterCase) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Source) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:ApiEntryCollection) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:PseudoCode) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:PseudoCodeArgument) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Property) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:PropertyOption) REQUIRE n.uid IS UNIQUE",
        ]
        for query in constraint_queries:
            session.run(query)

        if wipe:
            LOGGER.warning("--wipe により過去のノード/リレーションを削除します")
            session.run(
                """
                MATCH (n {managed_tag: $tag})
                DETACH DELETE n
                """,
                tag=MANAGED_TAG,
            )

        entity_labels = {
            "APIEntry",
            "Parameter",
            "ReturnValue",
            "Category",
            "EntryType",
            "ParameterCase",
            "PseudoCode",
            "PseudoCodeArgument",
            "Property",
            "PropertyOption",
        }

        node_count = 0
        for node in nodes:
            session.run(
                f"MERGE (n:{node.label} {{uid:$uid}}) SET n += $props",
                uid=node.uid,
                props=node.props,
            )
            if add_entity_label and node.label in entity_labels:
                session.run(
                    f"MATCH (n:{node.label} {{uid:$uid}}) SET n:__Entity__",
                    uid=node.uid,
                )
            node_count += 1

        rel_count = 0
        for rel in relations:
            session.run(
                (
                    "MATCH (a {uid:$src_uid}), (b {uid:$dst_uid}) "
                    f"MERGE (a)-[r:{rel.rel_type}]->(b) SET r += $props"
                ),
                src_uid=rel.src_uid,
                dst_uid=rel.dst_uid,
                props=rel.props or {"managed_tag": MANAGED_TAG},
            )
            rel_count += 1

    driver.close()
    return node_count, rel_count


def export_triples_json(path: Path, nodes: List[Node], relations: List[Relation]) -> None:
    payload = {
        "nodes": [{"label": n.label, "uid": n.uid, "props": n.props} for n in nodes],
        "relations": [
            {
                "src_uid": r.src_uid,
                "rel_type": r.rel_type,
                "dst_uid": r.dst_uid,
                "props": r.props or {},
            }
            for r in relations
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="api_entries_demo.json を Neo4j に投入しグラフ構造を構築"
    )
    parser.add_argument(
        "--json-path",
        type=Path,
        default=Path(__file__).with_name("data").joinpath("api_entries_demo.json"),
        help="入力 JSON (api_entries_demo.json)",
    )
    parser.add_argument(
        "--neo4j-uri",
        type=str,
        default=os.getenv("NEO4J_URI"),
        help="Neo4j URI (bolt://...)",
    )
    parser.add_argument(
        "--neo4j-user",
        type=str,
        default=os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER"),
        help="Neo4j ユーザ名",
    )
    parser.add_argument(
        "--neo4j-password",
        type=str,
        default=os.getenv("NEO4J_PASSWORD"),
        help="Neo4j パスワード",
    )
    parser.add_argument(
        "--database",
        type=str,
        default=os.getenv("NEO4J_DATABASE", "demo"),
        help="データベース名",
    )
    parser.add_argument(
        "--export-triples-json",
        type=Path,
        default=None,
        help="投入前にトリプルを JSON に書き出し",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Neo4j には書き込まず件数のみ確認",
    )
    parser.add_argument(
        "--wipe",
        action="store_true",
        help="この ETL が管理する既存ノード/リレーションを削除してから投入",
    )
    parser.add_argument(
        "--no-entity-label",
        action="store_true",
        help="__Entity__ ラベルを付与しない",
    )
    parser.add_argument(
        "--debug-graph",
        action="store_true",
        help="ノードとリレーションの作成を詳細にログ出力",
    )
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    LOGGER.debug("main関数開始")
    load_dotenv()
    args = parse_args(argv)

    if args.verbose:
        LOGGER.setLevel(logging.DEBUG)
        LOGGER.debug("verboseモードが有効になりました")

    LOGGER.info("JSON を読み込み: %s", args.json_path)
    records = load_api_entries(args.json_path)
    LOGGER.info("エントリ件数: %s", len(records))

    debug_mode = args.debug_graph or args.verbose
    graph_builder = GraphBuilder(debug=debug_mode)
    nodes, relations = graph_builder.build_graph_elements(records)
    LOGGER.info("生成ノード: %s, リレーション: %s", len(nodes), len(relations))

    if not nodes:
        LOGGER.error("ノードが 0 件です。JSON の 'api_entries' や 'name' を確認してください。")
        return 2

    if args.export_triples_json:
        export_triples_json(args.export_triples_json, nodes, relations)
        LOGGER.info("トリプルを書き出しました: %s", args.export_triples_json)

    neo4j_uri = normalize_neo4j_uri(args.neo4j_uri or "")
    if not neo4j_uri:
        LOGGER.error("Neo4j URI が指定されていません (--neo4j-uri を設定してください)")
        return 3

    if args.dry_run:
        LOGGER.info("--dry-run のため Neo4j への書き込みはスキップします")
        return 0

    node_count, relation_count = persist_to_neo4j(
        uri=neo4j_uri,
        username=args.neo4j_user or "neo4j",
        password=args.neo4j_password or "neo4j",
        database=args.database,
        nodes=nodes,
        relations=relations,
        wipe=args.wipe,
        add_entity_label=not args.no_entity_label,
    )
    LOGGER.info("Neo4j へ投入完了: ノード %s, リレーション %s", node_count, relation_count)

    LOGGER.info("完了")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
