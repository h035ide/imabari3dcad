#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
type_definitions.json を Neo4j のグラフへ投入し、GraphRAG/LlamaIndex で利活用しやすい
構造へ正規化する ETL スクリプト。

主な特徴:
- JSON を読み込み、型定義・Python 型メタ情報・バリアント制約を複数ノードへ分解
- CanonicalType を Python の型情報と結び付け、型体系の知識グラフ化を支援
- Variant の value_kind や制約スキーマ、列挙値をノード化し LLM が参照しやすく整理
- Source, Alias, Example などの補助情報を保持し、GraphRAG で根拠提示を可能に
- --dry-run / --export-triples-json で投入内容を検証、--wipe で既存データを安全に削除

利用例:
    uv run --with neo4j ./type_definitions_etl.py \
      --json-path ./type_definitions.json \
      --neo4j-uri bolt://localhost:7687 \
      --neo4j-user neo4j \
      --neo4j-password password \
      --database neo4j
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


def _to_str(value: Any) -> str:
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
        return _to_str(value)


def _normalize_uid(fragment: Any) -> str:
    s = _to_str(fragment)
    sanitized = (
        s.replace("\r", " ")
        .replace("\n", " ")
        .replace("\t", " ")
        .strip()
    )
    if not sanitized:
        return "__empty__"
    return " ".join(sanitized.split())


def _build_text(description: str, source_text: str) -> str:
    parts = [part.strip() for part in (description, source_text) if part]
    return "\n\n".join(parts)


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


def _ensure_canonical_type(
    *,
    canonical: str,
    meta: Dict[str, Dict[str, Any]],
    add_node,
    add_rel,
) -> None:
    if not canonical:
        return
    c_uid = f"canonical::{canonical}"
    meta_entry = meta.get(canonical, {})
    python_meta = meta_entry.get("python_type") if isinstance(meta_entry, dict) else None
    py_module = py_name = py_qual = py_description = None
    if isinstance(python_meta, dict) and python_meta.get("name"):
        py_module = python_meta.get("module", "builtins")
        py_name = python_meta.get("name", "")
        py_qual = python_meta.get("qualname") or (
            f"{py_module}.{py_name}" if py_module and py_name else py_name
        )
        py_description = _to_str(python_meta.get("description", ""))

    add_node(
        "CanonicalType",
        c_uid,
        name=canonical,
        description=_to_str(meta_entry.get("description", "")),
        python_module=_to_str(py_module) if py_module else None,
        python_name=_to_str(py_name) if py_name else None,
        python_qualname=_to_str(py_qual) if py_qual else None,
        python_description=py_description,
    )


def build_graph_elements(
    definitions: List[Dict[str, Any]], *, canonical_meta: Dict[str, Dict[str, Any]]
) -> Tuple[List[Node], List[Relation]]:
    nodes_map: Dict[str, Node] = {}
    rels: List[Relation] = []

    collection_uid = "type_definitions::collection"

    def add_node(label: str, uid: str, **props: Any) -> None:
        uid_s = _normalize_uid(uid)
        clean_props = {k: v for k, v in props.items() if v is not None}
        clean_props["managed_tag"] = MANAGED_TAG
        node = Node(label=label, uid=uid_s, props=clean_props)
        nodes_map[uid_s] = node

    add_node("TypeDefinitions", collection_uid, name="type_definitions")

    def add_rel(src_uid: str, rel_type: str, dst_uid: str, **props: Any) -> None:
        rel_props = {k: v for k, v in props.items() if v is not None}
        rel_props.setdefault("managed_tag", MANAGED_TAG)
        rels.append(
            Relation(
                src_uid=_normalize_uid(src_uid),
                rel_type=rel_type,
                dst_uid=_normalize_uid(dst_uid),
                props=rel_props or None,
            )
        )

    for index, td in enumerate(definitions):
        name = (td.get("name") or td.get("type_name") or "").strip()
        if not name:
            LOGGER.warning("name の無い型定義をスキップ: %s", td)
            continue

        canonical = (td.get("canonical_type") or "").strip()
        description = td.get("description") or td.get("desc") or ""
        source = td.get("source") or {}
        source_text = source.get("text", "")
        source_path = source.get("path")
        raw_json = _safe_json(td)
        primary_text = _build_text(_to_str(description), _to_str(source_text))

        td_uid = f"type::{name}"
        add_node(
            "TypeDefinition",
            td_uid,
            name=name,
            description=_to_str(description),
            text=primary_text,
            raw_json=raw_json,
            position=index,
        )
        add_rel(collection_uid, "HAS_TYPE_DEFINITION", td_uid)

        if canonical:
            _ensure_canonical_type(
                canonical=canonical,
                meta=canonical_meta,
                add_node=add_node,
                add_rel=add_rel,
            )
            add_rel(td_uid, "HAS_TYPE", f"canonical::{canonical}")

        aliases = td.get("alias") or td.get("aliases") or []
        if isinstance(aliases, (str, int, float)):
            aliases = [aliases]
        alias_list: List[Tuple[str, Dict[str, Any]]] = []
        if isinstance(aliases, list):
            for alias_idx, alias_value in enumerate(aliases):
                alias_str = _to_str(alias_value).strip()
                if not alias_str:
                    continue
                alias_uid = f"alias::{name}::{alias_str}"
                props = {
                    "name": alias_str,
                    "origin": "type_definition",
                    "position": alias_idx,
                }
                add_node("Alias", alias_uid, **props)
                add_rel(td_uid, "HAS_ALIAS", alias_uid)
                alias_list.append((alias_uid, props))

        origin_rel_map = {"one_of": "HAS_ONE_OF", "variants": "HAS_VARIANTS"}
        for origin_key in ("one_of", "variants"):
            variant_entries = td.get(origin_key) or []
            if not isinstance(variant_entries, list):
                continue
            for v_idx, entry in enumerate(variant_entries):
                if isinstance(entry, dict):
                    identifier = (
                        entry.get("id")
                        or entry.get("variant")
                        or entry.get("value")
                        or entry.get("name")
                        or _to_str(entry)
                    )
                    description_v = entry.get("description") or entry.get("desc") or ""
                    value_kind = entry.get("value_kind")
                    constraints = entry.get("constraints") if isinstance(entry.get("constraints"), dict) else None
                    metadata = {
                        k: v
                        for k, v in entry.items()
                        if k not in {"id", "description", "desc"}
                    }
                else:
                    identifier = _to_str(entry)
                    description_v = ""
                    value_kind = None
                    constraints = None
                    metadata = {"literal": identifier}

                identifier_str = _to_str(identifier)
                if not identifier_str:
                    identifier_str = f"variant_{v_idx}"
                variant_uid = f"variant::{name}::{identifier_str}"
                variant_props: Dict[str, Any] = {
                    "identifier": identifier_str,
                    "origin": origin_key,
                    "description": _to_str(description_v),
                    "position": v_idx,
                }
                if metadata:
                    variant_props["metadata_json"] = _safe_json(metadata)
                add_node("Variant", variant_uid, **variant_props)
                rel_type = origin_rel_map.get(origin_key, "HAS_VARIANT")
                add_rel(td_uid, rel_type, variant_uid, list_origin=origin_key)
                if alias_list:
                    alias_match = next(
                        (
                            alias_uid
                            for alias_uid, alias_props in alias_list
                            if alias_props.get("position") == v_idx
                        ),
                        None,
                    )
                    if alias_match:
                        add_rel(alias_match, "ALIAS_OF_VARIANT", variant_uid)

                if value_kind:
                    value_kind_str = _to_str(value_kind)
                    if canonical_meta.get(value_kind_str):
                        _ensure_canonical_type(
                            canonical=value_kind_str,
                            meta=canonical_meta,
                            add_node=add_node,
                            add_rel=add_rel,
                        )
                        add_rel(
                            variant_uid,
                            "CONSTRAINED_BY_CANONICAL_TYPE",
                            f"canonical::{value_kind_str}",
                        )

                if constraints:
                    constraint_uid = f"constraint::{variant_uid}"
                    add_node(
                        "Constraint",
                        constraint_uid,
                        kind=_to_str(constraints.get("kind", "structured")),
                        notes=_to_str(constraints.get("notes", "")),
                        length=constraints.get("length"),
                        raw_json=_safe_json(constraints),
                    )
                    add_rel(variant_uid, "HAS_CONSTRAINT", constraint_uid)

                    schema_items = constraints.get("schema")
                    if isinstance(schema_items, list):
                        for s_idx, raw_item in enumerate(schema_items):
                            schema_uid = f"{constraint_uid}::schema::{s_idx}"
                            add_node(
                                "ConstraintSchemaItem",
                                schema_uid,
                                index=s_idx,
                                value=_to_str(raw_item),
                            )
                            add_rel(constraint_uid, "HAS_SCHEMA_ITEM", schema_uid)

                            if isinstance(raw_item, str) and "|" in raw_item:
                                for enum_chunk in [chunk.strip() for chunk in raw_item.split("|") if chunk.strip()]:
                                    enum_uid = f"{schema_uid}::enum::{enum_chunk}"
                                    add_node(
                                        "EnumerationValue",
                                        enum_uid,
                                        value=enum_chunk,
                                    )
                                    add_rel(schema_uid, "ALLOWS_VALUE", enum_uid)

        examples = td.get("examples") or []
        if isinstance(examples, list):
            for ex_idx, ex in enumerate(examples):
                if isinstance(ex, dict):
                    val = ex.get("value")
                    explanation = ex.get("explanation", "")
                    variant_ref = ex.get("variant")
                    metadata = {
                        k: v
                        for k, v in ex.items()
                        if k not in {"value", "explanation", "variant"}
                    }
                else:
                    val = ex
                    explanation = ""
                    variant_ref = None
                    metadata = {}

                ex_uid = f"example::{name}::{ex_idx}"
                add_node(
                    "Example",
                    ex_uid,
                    value=_to_str(val),
                    value_json=_safe_json(val),
                    explanation=_to_str(explanation),
                    position=ex_idx,
                    metadata_json=_safe_json(metadata) if metadata else None,
                )
                add_rel(td_uid, "HAS_EXAMPLE", ex_uid)

                if variant_ref:
                    variant_ref_uid = f"variant::{name}::{_to_str(variant_ref)}"
                    add_rel(ex_uid, "ILLUSTRATES_VARIANT", variant_ref_uid)

        if source_text or source_path:
            source_uid = f"source::{name}::{_normalize_uid(source_path or 'inline')}"
            source_props = {
                "text": _to_str(source_text),
            }
            if source_path:
                source_props["path"] = _to_str(source_path)
            add_node(
                "Source",
                source_uid,
                **source_props,
            )
            add_rel(td_uid, "CITED_FROM", source_uid)

    return list(nodes_map.values()), rels


def normalize_neo4j_uri(uri: str) -> str:
    if not uri:
        return uri
    u = str(uri).strip().replace("　", " ")
    if (u.startswith('"') and u.endswith('"')) or (u.startswith("'") and u.endswith("'")):
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

        entity_labels = {"TypeDefinition", "CanonicalType", "Variant"}

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
        "nodes": [
            {"label": n.label, "uid": n.uid, "props": n.props} for n in nodes
        ],
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
        LOGGER.warning("--clear-force が指定されていないためデータベースのクリアをスキップします")
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
                    LOGGER.info("データベース '%s' が存在しないため作成します", database)
                    system_session.run(f"CREATE DATABASE `{database}`")
        except Exception as exc:
            LOGGER.debug("データベース存在確認でエラーが発生しましたが処理を継続します: %s", exc)

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
    nodes, rels = build_graph_elements(definitions, canonical_meta=canonical_meta)
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
            neo4j_uri, args.neo4j_user or "neo4j", args.neo4j_password or "neo4j", args.database
        )

    LOGGER.info("完了")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
