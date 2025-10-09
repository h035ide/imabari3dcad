#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
リファクタリング版: type_definitions.json を Neo4j のグラフへ投入し、GraphRAG/LlamaIndex で利活用しやすい
構造へ正規化する ETL スクリプト。

主な改善点:
- クラスベースの設計により責任を明確化
- 巨大な関数を小さな関数に分割
- 重複コードの削減
- テスト容易性の向上
"""

from __future__ import annotations

import argparse
import copy
import json
import logging
import sys
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

LOGGER = logging.getLogger("typedef_etl")
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("[%(levelname)s] %(message)s")
handler.setFormatter(formatter)
LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)

MANAGED_TAG = "type_definitions_etl"

DEFAULT_CANONICAL_META: Dict[str, Dict[str, Any]] = {
    "string": {
        "description": "テキスト値を表す基本的な文字列型。",
        "python_type": {
            "module": "builtins",
            "name": "str",
            "qualname": "str",
            "description": "Python の Unicode 文字列型。",
        },
    },
    "float": {
        "description": "浮動小数点値 (double precision)。",
        "python_type": {
            "module": "builtins",
            "name": "float",
            "qualname": "float",
            "description": "倍精度の浮動小数点数。",
        },
    },
    "integer": {
        "description": "符号付き整数値。",
        "python_type": {
            "module": "builtins",
            "name": "int",
            "qualname": "int",
            "description": "任意精度整数。",
        },
    },
    "bool": {
        "description": "真偽値 (True / False)。",
        "python_type": {
            "module": "builtins",
            "name": "bool",
            "qualname": "bool",
            "description": "真偽値型。",
        },
    },
    "string[]": {
        "description": "文字列を要素とする配列/シーケンス。",
        "python_type": {
            "module": "typing",
            "name": "Sequence",
            "qualname": "typing.Sequence[str]",
            "description": "文字列を要素とするシーケンス型。",
        },
    },
}


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
    props: Dict[str, Any] | None = None


class GraphBuilderConfig:
    """グラフ構築の設定を管理するクラス"""

    def __init__(self, canonical_meta: Dict[str, Dict[str, Any]]):
        self.canonical_meta = canonical_meta
        self.managed_tag = MANAGED_TAG


class NodeBuilder:
    """ノード作成の共通処理を提供するクラス"""

    def __init__(self, config: GraphBuilderConfig):
        self.config = config

    def _normalize_uid(self, fragment: Any) -> str:
        s = self._to_str(fragment)
        sanitized = s.replace("\r", " ").replace("\n", " ").replace("\t", " ").strip()
        if not sanitized:
            return "__empty__"
        return " ".join(sanitized.split())

    def _to_str(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, (str, int, float, bool)):
            return str(value)
        try:
            return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        except Exception:
            return str(value)

    def _safe_json(self, value: Any) -> str:
        try:
            return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        except Exception:
            return self._to_str(value)

    def create_node(self, label: str, uid: str, **props: Any) -> Node:
        """ノードを作成する"""
        uid_s = self._normalize_uid(uid)
        clean_props = {k: v for k, v in props.items() if v is not None}
        clean_props["managed_tag"] = self.config.managed_tag
        return Node(label=label, uid=uid_s, props=clean_props)


class RelationBuilder:
    """リレーション作成の共通処理を提供するクラス"""

    def __init__(self, config: GraphBuilderConfig):
        self.config = config

    def create_relation(
        self, src_uid: str, rel_type: str, dst_uid: str, **props: Any
    ) -> Relation:
        """リレーションを作成する"""
        rel_props = {k: v for k, v in props.items() if v is not None}
        rel_props.setdefault("managed_tag", self.config.managed_tag)
        return Relation(
            src_uid=src_uid,
            rel_type=rel_type,
            dst_uid=dst_uid,
            props=rel_props or None,
        )


class MetadataProcessor:
    """メタデータ処理の共通処理を提供するクラス"""

    @staticmethod
    def is_regex_pattern(text: str) -> bool:
        """正規表現パターンかどうかを判定"""
        if not isinstance(text, str):
            return False
        regex_indicators = ["^", "$", "[", "]", "{", "}", "(", ")", "|", "+", "*", "?"]
        return any(indicator in text for indicator in regex_indicators)

    @staticmethod
    def build_text(description: str, source_text: str) -> str:
        """テキストを結合する"""
        parts = [part.strip() for part in (description, source_text) if part]
        return "\n\n".join(parts)


class TypeDefinitionProcessor:
    """型定義処理の責任を持つクラス"""

    def __init__(
        self,
        node_builder: NodeBuilder,
        relation_builder: RelationBuilder,
        config: GraphBuilderConfig,
    ):
        self.node_builder = node_builder
        self.relation_builder = relation_builder
        self.config = config
        self.metadata_processor = MetadataProcessor()

    def process_type_definition(
        self, td: Dict[str, Any], index: int
    ) -> Tuple[List[Node], List[Relation]]:
        """単一の型定義を処理する"""
        nodes = []
        relations = []

        name = (td.get("name") or td.get("type_name") or "").strip()
        if not name:
            LOGGER.warning("name の無い型定義をスキップ: %s", td)
            return nodes, relations

        # メインのTypeDefinitionノードを作成
        td_node, td_relations = self._create_type_definition_node(td, name, index)
        nodes.append(td_node)
        relations.extend(td_relations)

        # 各種サブノードを処理
        nodes.extend(self._process_canonical_type(td, name))
        nodes.extend(self._process_aliases(td, name))

        variant_nodes, variant_relations = self._process_variants(td, name)
        nodes.extend(variant_nodes)
        relations.extend(variant_relations)

        nodes.extend(self._process_examples(td, name))
        nodes.extend(self._process_source(td, name))

        return nodes, relations

    def _create_type_definition_node(
        self, td: Dict[str, Any], name: str, index: int
    ) -> Tuple[Node, List[Relation]]:
        """TypeDefinitionノードを作成する"""
        description = td.get("description") or td.get("desc") or ""
        source = td.get("source") or {}
        source_text = source.get("text", "")
        raw_json = self.node_builder._safe_json(td)
        primary_text = self.metadata_processor.build_text(
            self.node_builder._to_str(description),
            self.node_builder._to_str(source_text),
        )

        td_uid = f"type::{name}"
        node = self.node_builder.create_node(
            "TypeDefinition",
            td_uid,
            name=name,
            description=self.node_builder._to_str(description),
            text=primary_text,
            raw_json=raw_json,
            position=index,
        )

        collection_uid = "type_definitions::collection"
        relation = self.relation_builder.create_relation(
            collection_uid, "HAS_TYPE_DEFINITION", td_uid
        )

        return node, [relation]

    def _process_canonical_type(self, td: Dict[str, Any], name: str) -> List[Node]:
        """カノニカル型を処理する"""
        nodes = []
        canonical = (td.get("canonical_type") or "").strip()
        if not canonical:
            return nodes

        canonical_uid = f"canonical::{canonical}"
        meta_entry = self.config.canonical_meta.get(canonical, {})
        python_meta = (
            meta_entry.get("python_type") if isinstance(meta_entry, dict) else None
        )

        py_module = py_name = py_qual = py_description = None
        if isinstance(python_meta, dict) and python_meta.get("name"):
            py_module = python_meta.get("module", "builtins")
            py_name = python_meta.get("name", "")
            py_qual = python_meta.get("qualname") or (
                f"{py_module}.{py_name}" if py_module and py_name else py_name
            )
            py_description = self.node_builder._to_str(
                python_meta.get("description", "")
            )

        node = self.node_builder.create_node(
            "CanonicalType",
            canonical_uid,
            name=canonical,
            description=self.node_builder._to_str(meta_entry.get("description", "")),
            python_module=self.node_builder._to_str(py_module) if py_module else None,
            python_name=self.node_builder._to_str(py_name) if py_name else None,
            python_qualname=self.node_builder._to_str(py_qual) if py_qual else None,
            python_description=py_description,
        )
        nodes.append(node)

        return nodes

    def _process_aliases(self, td: Dict[str, Any], name: str) -> List[Node]:
        """エイリアスを処理する"""
        nodes = []
        aliases = td.get("alias") or td.get("aliases") or []
        if isinstance(aliases, (str, int, float)):
            aliases = [aliases]

        if isinstance(aliases, list):
            for alias_idx, alias_value in enumerate(aliases):
                alias_str = self.node_builder._to_str(alias_value).strip()
                if not alias_str:
                    continue

                alias_uid = f"alias::{name}::{alias_str}"
                node = self.node_builder.create_node(
                    "Alias",
                    alias_uid,
                    name=alias_str,
                    origin="type_definition",
                    position=alias_idx,
                )
                nodes.append(node)

        return nodes

    def _process_variants(
        self, td: Dict[str, Any], name: str
    ) -> Tuple[List[Node], List[Relation]]:
        """バリアントを処理する"""
        nodes = []
        relations = []
        origin_rel_map = {"one_of": "HAS_ONE_OF", "variants": "HAS_VARIANTS"}
        td_uid = f"type::{name}"

        for origin_key in ("one_of", "variants"):
            variant_entries = td.get(origin_key) or []
            if not isinstance(variant_entries, list):
                continue

            for v_idx, entry in enumerate(variant_entries):
                variant_nodes, variant_relations = self._process_single_variant(
                    entry, name, v_idx, origin_key
                )
                nodes.extend(variant_nodes)

                # バリアントからTypeDefinitionへのリレーションを追加
                if variant_nodes:
                    variant_uid = variant_nodes[
                        0
                    ].uid  # 最初のノードがメインのVariantノード
                    rel_type = origin_rel_map.get(origin_key, "HAS_VARIANT")
                    relation = self.relation_builder.create_relation(
                        td_uid, rel_type, variant_uid, list_origin=origin_key
                    )
                    relations.append(relation)

        return nodes, relations

    def _process_single_variant(
        self, entry: Any, name: str, v_idx: int, origin_key: str
    ) -> Tuple[List[Node], List[Relation]]:
        """単一のバリアントを処理する"""
        nodes = []
        relations = []

        if isinstance(entry, dict):
            identifier = (
                entry.get("id")
                or entry.get("variant")
                or entry.get("value")
                or entry.get("name")
                or self.node_builder._to_str(entry)
            )
            description_v = entry.get("description") or entry.get("desc") or ""
            # value_kind = entry.get("value_kind")  # 現在は未使用
            constraints = (
                entry.get("constraints")
                if isinstance(entry.get("constraints"), dict)
                else None
            )
            metadata = {
                k: v for k, v in entry.items() if k not in {"id", "description", "desc"}
            }
        else:
            identifier = self.node_builder._to_str(entry)
            description_v = ""
            # value_kind = None  # 現在は未使用
            constraints = None
            metadata = {"literal": identifier}

        identifier_str = self.node_builder._to_str(identifier)
        if not identifier_str:
            identifier_str = f"variant_{v_idx}"

        variant_uid = f"variant::{name}::{identifier_str}"
        variant_props = {
            "identifier": identifier_str,
            "origin": origin_key,
            "description": self.node_builder._to_str(description_v),
            "position": v_idx,
        }
        if metadata:
            variant_props["metadata_json"] = self.node_builder._safe_json(metadata)

        node = self.node_builder.create_node("Variant", variant_uid, **variant_props)
        nodes.append(node)

        # パターンノードの処理
        if metadata and metadata.get("pattern"):
            pattern_nodes, pattern_relations = self._process_pattern(
                metadata["pattern"], variant_uid
            )
            nodes.extend(pattern_nodes)
            relations.extend(pattern_relations)

        # 制約の処理
        if constraints:
            constraint_nodes, constraint_relations = self._process_constraints(
                constraints, variant_uid
            )
            nodes.extend(constraint_nodes)
            relations.extend(constraint_relations)

        return nodes, relations

    def _process_pattern(
        self, pattern: Any, variant_uid: str
    ) -> Tuple[List[Node], List[Relation]]:
        """パターンを処理する"""
        nodes = []
        relations = []
        pattern_str = self.node_builder._to_str(pattern)
        if pattern_str:
            pattern_uid = f"pattern::{variant_uid}"
            pattern_type = (
                "regex"
                if self.metadata_processor.is_regex_pattern(pattern_str)
                else "literal"
            )

            node = self.node_builder.create_node(
                "Pattern",
                pattern_uid,
                pattern=pattern_str,
                pattern_type=pattern_type,
            )
            nodes.append(node)

            # パターンからバリアントへのリレーション
            relation = self.relation_builder.create_relation(
                variant_uid, "HAS_PATTERN", pattern_uid
            )
            relations.append(relation)

        return nodes, relations

    def _process_constraints(
        self, constraints: Dict[str, Any], variant_uid: str
    ) -> Tuple[List[Node], List[Relation]]:
        """制約を処理する"""
        nodes = []
        relations = []
        constraint_uid = f"constraint::{variant_uid}"

        node = self.node_builder.create_node(
            "Constraint",
            constraint_uid,
            kind=self.node_builder._to_str(constraints.get("kind", "structured")),
            notes=self.node_builder._to_str(constraints.get("notes", "")),
            length=constraints.get("length"),
            raw_json=self.node_builder._safe_json(constraints),
        )
        nodes.append(node)

        # 制約からバリアントへのリレーション
        relation = self.relation_builder.create_relation(
            variant_uid, "HAS_CONSTRAINT", constraint_uid
        )
        relations.append(relation)

        # ConstraintPropertyノードの処理
        for prop_key, prop_value in constraints.items():
            if prop_key not in {"kind", "notes", "length", "schema"}:
                prop_uid = f"{constraint_uid}::property::{prop_key}"
                prop_node = self.node_builder.create_node(
                    "ConstraintProperty",
                    prop_uid,
                    property_name=self.node_builder._to_str(prop_key),
                    property_value=self.node_builder._to_str(prop_value),
                    property_type=(
                        "string"
                        if isinstance(prop_value, str)
                        else "boolean" if isinstance(prop_value, bool) else "other"
                    ),
                )
                nodes.append(prop_node)

                # プロパティから制約へのリレーション
                prop_relation = self.relation_builder.create_relation(
                    constraint_uid, "HAS_PROPERTY", prop_uid
                )
                relations.append(prop_relation)

        # スキーマアイテムの処理
        schema_items = constraints.get("schema")
        if isinstance(schema_items, list):
            schema_nodes, schema_relations = self._process_schema_items(
                schema_items, constraint_uid
            )
            nodes.extend(schema_nodes)
            relations.extend(schema_relations)

        return nodes, relations

    def _process_schema_items(
        self, schema_items: List[Any], constraint_uid: str
    ) -> Tuple[List[Node], List[Relation]]:
        """スキーマアイテムを処理する"""
        nodes = []
        relations = []

        for s_idx, raw_item in enumerate(schema_items):
            schema_uid = f"{constraint_uid}::schema::{s_idx}"
            schema_node = self.node_builder.create_node(
                "ConstraintSchemaItem",
                schema_uid,
                index=s_idx,
                value=self.node_builder._to_str(raw_item),
            )
            nodes.append(schema_node)

            # スキーマアイテムから制約へのリレーション
            schema_relation = self.relation_builder.create_relation(
                constraint_uid, "HAS_SCHEMA_ITEM", schema_uid
            )
            relations.append(schema_relation)

            if isinstance(raw_item, str):
                # 正規表現パターンの処理
                if self.metadata_processor.is_regex_pattern(raw_item):
                    regex_uid = f"{schema_uid}::regex"
                    regex_node = self.node_builder.create_node(
                        "RegexPattern",
                        regex_uid,
                        pattern=raw_item,
                        description=f"Schema item {s_idx} regex pattern",
                    )
                    nodes.append(regex_node)

                    # 正規表現からスキーマアイテムへのリレーション
                    regex_relation = self.relation_builder.create_relation(
                        schema_uid, "HAS_REGEX_PATTERN", regex_uid
                    )
                    relations.append(regex_relation)
                # 列挙値の処理（|で区切られた値）
                elif "|" in raw_item:
                    enum_nodes, enum_relations = self._process_enumeration_values(
                        raw_item, schema_uid
                    )
                    nodes.extend(enum_nodes)
                    relations.extend(enum_relations)
                # 単一の固定値
                else:
                    literal_uid = f"{schema_uid}::literal"
                    literal_node = self.node_builder.create_node(
                        "LiteralValue",
                        literal_uid,
                        value=raw_item,
                        value_type="string",
                    )
                    nodes.append(literal_node)

                    # リテラル値からスキーマアイテムへのリレーション
                    literal_relation = self.relation_builder.create_relation(
                        schema_uid, "HAS_LITERAL_VALUE", literal_uid
                    )
                    relations.append(literal_relation)

        return nodes, relations

    def _process_enumeration_values(
        self, enum_string: str, schema_uid: str
    ) -> Tuple[List[Node], List[Relation]]:
        """列挙値を処理する"""
        nodes = []
        relations = []
        for enum_chunk in [
            chunk.strip() for chunk in enum_string.split("|") if chunk.strip()
        ]:
            enum_uid = f"{schema_uid}::enum::{enum_chunk}"
            enum_node = self.node_builder.create_node(
                "EnumerationValue",
                enum_uid,
                value=enum_chunk,
            )
            nodes.append(enum_node)

            # 列挙値からスキーマアイテムへのリレーション
            enum_relation = self.relation_builder.create_relation(
                schema_uid, "ALLOWS_VALUE", enum_uid
            )
            relations.append(enum_relation)

        return nodes, relations

    def _process_examples(self, td: Dict[str, Any], name: str) -> List[Node]:
        """例を処理する"""
        nodes = []
        examples = td.get("examples") or []

        if isinstance(examples, list):
            for ex_idx, ex in enumerate(examples):
                if isinstance(ex, dict):
                    val = ex.get("value")
                    explanation = ex.get("explanation", "")
                    # variant_ref = ex.get("variant")  # 現在は未使用
                    metadata = {
                        k: v
                        for k, v in ex.items()
                        if k not in {"value", "explanation", "variant"}
                    }
                else:
                    val = ex
                    explanation = ""
                    # variant_ref = None  # 現在は未使用
                    metadata = {}

                ex_uid = f"example::{name}::{ex_idx}"
                node = self.node_builder.create_node(
                    "Example",
                    ex_uid,
                    value=self.node_builder._to_str(val),
                    value_json=self.node_builder._safe_json(val),
                    explanation=self.node_builder._to_str(explanation),
                    position=ex_idx,
                    metadata_json=(
                        self.node_builder._safe_json(metadata) if metadata else None
                    ),
                )
                nodes.append(node)

        return nodes

    def _process_source(self, td: Dict[str, Any], name: str) -> List[Node]:
        """ソースを処理する"""
        nodes = []
        source = td.get("source") or {}
        source_text = source.get("text", "")
        source_path = source.get("path")

        if source_text or source_path:
            source_uid = f"source::{name}::{self.node_builder._normalize_uid(source_path or 'inline')}"
            source_props = {
                "text": self.node_builder._to_str(source_text),
            }
            if source_path:
                source_props["path"] = self.node_builder._to_str(source_path)

            node = self.node_builder.create_node("Source", source_uid, **source_props)
            nodes.append(node)

        return nodes


class GraphBuilder:
    """グラフ構築の主要責任を持つクラス"""

    def __init__(self, canonical_meta: Dict[str, Dict[str, Any]]):
        self.config = GraphBuilderConfig(canonical_meta)
        self.node_builder = NodeBuilder(self.config)
        self.relation_builder = RelationBuilder(self.config)
        self.type_processor = TypeDefinitionProcessor(
            self.node_builder, self.relation_builder, self.config
        )

    def build_graph_elements(
        self, definitions: List[Dict[str, Any]]
    ) -> Tuple[List[Node], List[Relation]]:
        """グラフ要素を構築する"""
        nodes_map: Dict[str, Node] = {}
        relations: List[Relation] = []

        collection_uid = "type_definitions::collection"
        collection_node = self.node_builder.create_node(
            "TypeDefinitions", collection_uid, name="type_definitions"
        )
        nodes_map[collection_uid] = collection_node

        for index, td in enumerate(definitions):
            td_nodes, td_relations = self.type_processor.process_type_definition(
                td, index
            )

            for node in td_nodes:
                nodes_map[node.uid] = node

            relations.extend(td_relations)

            # 追加のリレーションを作成
            additional_relations = self._create_additional_relations(td, td_nodes)
            relations.extend(additional_relations)

        return list(nodes_map.values()), relations

    def _create_additional_relations(
        self, td: Dict[str, Any], nodes: List[Node]
    ) -> List[Relation]:
        """追加のリレーションを作成する"""
        relations = []
        name = (td.get("name") or td.get("type_name") or "").strip()
        if not name:
            return relations

        td_uid = f"type::{name}"

        # カノニカル型へのリレーション
        canonical = (td.get("canonical_type") or "").strip()
        if canonical:
            relations.append(
                self.relation_builder.create_relation(
                    td_uid, "HAS_TYPE", f"canonical::{canonical}"
                )
            )

        # エイリアスからバリアントへのリレーション
        aliases = td.get("alias") or td.get("aliases") or []
        if isinstance(aliases, (str, int, float)):
            aliases = [aliases]

        if isinstance(aliases, list):
            for alias_idx, alias_value in enumerate(aliases):
                alias_str = self.node_builder._to_str(alias_value).strip()
                if not alias_str:
                    continue

                alias_uid = f"alias::{name}::{alias_str}"

                # バリアントへのリレーション
                for origin_key in ("one_of", "variants"):
                    variant_entries = td.get(origin_key) or []
                    if isinstance(variant_entries, list) and alias_idx < len(
                        variant_entries
                    ):
                        entry = variant_entries[alias_idx]
                        if isinstance(entry, dict):
                            identifier = (
                                entry.get("id")
                                or entry.get("variant")
                                or entry.get("value")
                                or entry.get("name")
                                or self.node_builder._to_str(entry)
                            )
                        else:
                            identifier = self.node_builder._to_str(entry)

                        identifier_str = self.node_builder._to_str(identifier)
                        if not identifier_str:
                            identifier_str = f"variant_{alias_idx}"

                        variant_uid = f"variant::{name}::{identifier_str}"
                        relations.append(
                            self.relation_builder.create_relation(
                                alias_uid, "ALIAS_OF_VARIANT", variant_uid
                            )
                        )

        # バリアントからカノニカル型へのリレーション
        for origin_key in ("one_of", "variants"):
            variant_entries = td.get(origin_key) or []
            if isinstance(variant_entries, list):
                for v_idx, entry in enumerate(variant_entries):
                    if isinstance(entry, dict):
                        value_kind = entry.get("value_kind")
                        if value_kind and self.config.canonical_meta.get(
                            self.node_builder._to_str(value_kind)
                        ):
                            identifier = (
                                entry.get("id")
                                or entry.get("variant")
                                or entry.get("value")
                                or entry.get("name")
                                or self.node_builder._to_str(entry)
                            )
                            identifier_str = self.node_builder._to_str(identifier)
                            if not identifier_str:
                                identifier_str = f"variant_{v_idx}"

                            variant_uid = f"variant::{name}::{identifier_str}"
                            relations.append(
                                self.relation_builder.create_relation(
                                    variant_uid,
                                    "CONSTRAINED_BY_CANONICAL_TYPE",
                                    f"canonical::{value_kind}",
                                )
                            )

        # 例からバリアントへのリレーション
        examples = td.get("examples") or []
        if isinstance(examples, list):
            for ex_idx, ex in enumerate(examples):
                if isinstance(ex, dict):
                    variant_ref = ex.get("variant")
                    if variant_ref:
                        variant_ref_uid = (
                            f"variant::{name}::{self.node_builder._to_str(variant_ref)}"
                        )
                        ex_uid = f"example::{name}::{ex_idx}"
                        relations.append(
                            self.relation_builder.create_relation(
                                ex_uid, "ILLUSTRATES_VARIANT", variant_ref_uid
                            )
                        )

        # ソースへのリレーション
        source = td.get("source") or {}
        source_text = source.get("text", "")
        source_path = source.get("path")
        if source_text or source_path:
            source_uid = f"source::{name}::{self.node_builder._normalize_uid(source_path or 'inline')}"
            relations.append(
                self.relation_builder.create_relation(td_uid, "CITED_FROM", source_uid)
            )

        return relations


# 既存の関数群は残す（Neo4j操作、メイン処理など）
def load_type_definitions(json_path: Path) -> List[Dict[str, Any]]:
    with json_path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)

    if not isinstance(payload, dict) or not isinstance(
        payload.get("type_definitions"), list
    ):
        raise ValueError("JSON のトップレベルに 'type_definitions' (list) が必要です")

    defs: List[Dict[str, Any]] = []
    for td in payload["type_definitions"]:
        if not isinstance(td, dict):
            continue
        src = td.get("source") if isinstance(td.get("source"), dict) else {}
        if "path" in src:
            src = copy.deepcopy(src)
            src.pop("path", None)
        td["source"] = src
        defs.append(td)
    return defs


def load_canonical_meta(path: Optional[Path]) -> Dict[str, Dict[str, Any]]:
    meta: Dict[str, Dict[str, Any]] = copy.deepcopy(DEFAULT_CANONICAL_META)
    if not path:
        return meta
    if not path.exists():
        LOGGER.warning("canonical meta ファイルが見つかりません: %s", path)
        return meta

    with path.open("r", encoding="utf-8") as fp:
        user_meta = json.load(fp)

    if not isinstance(user_meta, dict):
        raise ValueError("canonical meta ファイルは JSON object である必要があります")

    for key, value in user_meta.items():
        if not isinstance(value, dict):
            continue
        base = meta.get(key, {})
        merged = copy.deepcopy(base)
        merged.update(value)
        meta[key] = merged
    return meta


def normalize_neo4j_uri(uri: str) -> str:
    if not uri:
        return uri
    u = str(uri).strip().replace("　", " ")
    if (u.startswith('"') and u.endswith('"')) or (
        u.startswith("'") and u.endswith("'")
    ):
        u = u[1:-1]
    if "://" not in u:
        u = f"bolt://{u}"
    return u


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

    with driver.session(**session_kwargs) as sess:
        constraint_queries = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:TypeDefinition) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:CanonicalType) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Variant) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:ValueKind) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Constraint) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:ConstraintSchemaItem) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:EnumerationValue) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Example) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Alias) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Source) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Pattern) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:ConstraintProperty) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:RegexPattern) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:LiteralValue) REQUIRE n.uid IS UNIQUE",
        ]
        for query in constraint_queries:
            sess.run(query)

        if wipe:
            LOGGER.warning("--wipe により過去のノード/リレーションを削除します")
            sess.run(
                """
                MATCH (n {managed_tag: $tag})
                DETACH DELETE n
                """,
                tag=MANAGED_TAG,
            )

        entity_labels = {
            "TypeDefinition",
            "CanonicalType",
            "Variant",
            "Pattern",
            "ConstraintProperty",
            "RegexPattern",
        }

        node_count = 0
        for node in nodes:
            sess.run(
                f"MERGE (n:{node.label} {{uid:$uid}}) SET n += $props",
                uid=node.uid,
                props=node.props,
            )
            if add_entity_label and node.label in entity_labels:
                sess.run(
                    f"MATCH (n:{node.label} {{uid:$uid}}) SET n:__Entity__",
                    uid=node.uid,
                )
            node_count += 1

        rel_count = 0
        for rel in relations:
            sess.run(
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


def export_triples_json(
    path: Path, nodes: List[Node], relations: List[Relation]
) -> None:
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


def try_build_property_graph_index(
    uri: str, username: str, password: str, database: Optional[str]
) -> None:
    try:
        from llama_index.graph_stores.neo4j import Neo4jGraphStore

        kwargs: Dict[str, Any] = {
            "uri": uri,
            "username": username,
            "password": password,
        }
        if database:
            kwargs["database"] = database
        try:
            Neo4jGraphStore(**kwargs)
        except TypeError:
            kwargs.pop("uri", None)
            kwargs["url"] = uri
            Neo4jGraphStore(**kwargs)
        LOGGER.info("LlamaIndex Neo4jGraphStore への接続検証に成功しました")
    except Exception as exc:
        LOGGER.warning("LlamaIndex GraphStore 接続検証はスキップ/失敗しました: %s", exc)


def clear_database_contents(
    *,
    uri: str,
    username: str,
    password: str,
    database: str,
    force: bool,
) -> bool:
    if not force:
        LOGGER.warning(
            "--clear-force が指定されていないためデータベースのクリアをスキップします"
        )
        return False

    from neo4j import GraphDatabase

    LOGGER.warning("データベース '%s' を完全にクリアします", database)
    driver = GraphDatabase.driver(uri, auth=(username, password))
    try:
        try:
            with driver.session(database="system") as system_session:
                result = system_session.run("SHOW DATABASES")
                db_names = {record["name"] for record in result}
                if database not in db_names:
                    LOGGER.info(
                        "データベース '%s' が存在しないため作成します", database
                    )
                    system_session.run(f"CREATE DATABASE `{database}`")
        except Exception as exc:
            LOGGER.debug(
                "データベース存在確認でエラーが発生しましたが処理を継続します: %s", exc
            )

        with driver.session(database=database) as session:
            session.run("MATCH ()-[r]-() DELETE r")
            session.run("MATCH (n) DELETE n")
            LOGGER.info("データベース '%s' のクリアが完了しました", database)
        return True
    except Exception as exc:
        LOGGER.error("データベースクリア中にエラー: %s", exc)
        return False
    finally:
        driver.close()


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="type_definitions.json を Neo4j に投入しグラフを整備"
    )
    parser.add_argument(
        "--json-path",
        type=Path,
        default=Path(__file__).with_name("type_definitions.json"),
        help="入力 JSON (type_definitions.json)",
    )
    parser.add_argument(
        "--canonical-meta-path",
        type=Path,
        default=None,
        help="canonical_type に付随する Python 型メタ情報の JSON (任意)",
    )
    parser.add_argument("--openai-api-key", default=os.getenv("OPENAI_API_KEY"))
    parser.add_argument(
        "--neo4j-uri",
        type=str,
        default=os.getenv("NEO4J_URI"),
        help="Neo4j URI (bolt://...) または neo4j://",
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
        help="データベース名 (Neo4j 5.x 以上で複数 DB を利用する場合)",
    )
    parser.add_argument(
        "--clear-before",
        action="store_true",
        help="投入前に対象データベースを完全にクリア",
    )
    parser.add_argument(
        "--clear-force",
        action="store_true",
        help="クリア処理を強制実行（確認なし）",
    )
    parser.add_argument(
        "--clear-db",
        type=str,
        default=None,
        help="クリア対象のデータベース名。未指定時は --database を利用",
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
        "--create-property-graph-index",
        action="store_true",
        help="LlamaIndex Neo4jGraphStore への疎通確認を行う",
    )
    parser.add_argument(
        "--no-entity-label",
        action="store_true",
        help="ノードに __Entity__ ラベルを付与しない",
    )
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    load_dotenv()
    args = parse_args(argv)
    if args.verbose:
        LOGGER.setLevel(logging.DEBUG)

    LOGGER.info("JSON を読み込み: %s", args.json_path)
    definitions = load_type_definitions(args.json_path)
    LOGGER.info("定義の件数: %d", len(definitions))

    canonical_meta = load_canonical_meta(args.canonical_meta_path)

    # リファクタリング版のGraphBuilderを使用
    graph_builder = GraphBuilder(canonical_meta)
    nodes, rels = graph_builder.build_graph_elements(definitions)

    add_entity_label = not args.no_entity_label
    LOGGER.info("生成ノード: %d, リレーション: %d", len(nodes), len(rels))

    if len(nodes) == 0:
        LOGGER.error(
            "ノードが 0 件です。JSON の 'type_definitions' や各要素の 'name' を確認してください。"
        )
        return 2

    if args.export_triples_json:
        export_triples_json(args.export_triples_json, nodes, rels)
        LOGGER.info("トリプルを書き出しました: %s", args.export_triples_json)

    neo4j_uri = normalize_neo4j_uri(args.neo4j_uri or "")
    if not neo4j_uri:
        LOGGER.error("Neo4j URI が指定されていません (--neo4j-uri を設定してください)")
        return 3

    if args.clear_before:
        if args.dry_run:
            LOGGER.warning("--dry-run 中のためデータベースクリアはスキップします")
        else:
            cleared = clear_database_contents(
                uri=neo4j_uri,
                username=args.neo4j_user or "neo4j",
                password=args.neo4j_password or "neo4j",
                database=args.clear_db or args.database,
                force=args.clear_force,
            )
            if not cleared:
                LOGGER.warning("データベースのクリアは実行されませんでした")

    if args.dry_run:
        LOGGER.info("--dry-run のため Neo4j への書き込みはスキップします")
    else:
        n_count, r_count = persist_to_neo4j(
            uri=neo4j_uri,
            username=args.neo4j_user or "neo4j",
            password=args.neo4j_password or "neo4j",
            database=args.database,
            nodes=nodes,
            relations=rels,
            wipe=args.wipe,
            add_entity_label=add_entity_label,
        )
        LOGGER.info("Neo4j へ投入完了: ノード %d, リレーション %d", n_count, r_count)

    if args.create_property_graph_index:
        try_build_property_graph_index(
            neo4j_uri,
            args.neo4j_user or "neo4j",
            args.neo4j_password or "neo4j",
            args.database,
        )

    LOGGER.info("完了")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
