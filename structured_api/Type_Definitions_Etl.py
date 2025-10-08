#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A-style ETL (決め打ち) で JSON の type_definitions を Neo4j のプロパティグラフへ投入するスクリプト。

特徴:
- LLM/JSONReader に依存せず、JSON を素直に読み込み → ノード/リレーションを明示マッピング
- 取り込み先は Neo4j（bolt/neo4j/s）を想定（ローカル/クラウドどちらでも可）
- 取り込み内容をデバッグしやすいように --dry-run / --export-triples-json を用意
- （任意）--create-property-graph-index で LlamaIndex から GraphStore に接続できるか簡易検証

使い方（例）:
    python type_definitions_etl.py \
      --json-path ./data/type_definitions.json \
      --neo4j-uri bolt://localhost:7687 \
      --neo4j-user neo4j \
      --neo4j-password password \
      --database neo4j \
      --project imabari3dcad \
      --export-triples-json ./data/typedef_triples.json \
      --create-property-graph-index

初回は --dry-run で件数だけ確認してから投入するのが安全です。

想定する JSON 形式:
{
  "type_definitions": [
    {
      "name": "要素",
      "canonical_type": "string",
      "description": "...",            # 任意
      "one_of": [ ... ],                # 任意（list[str|dict]）
      "variants": [ ... ],              # 任意（list[str|dict]）
      "examples": [ ... ],              # 任意（list[str|dict]）
      "source": {                       # 任意
        "text": "...",
        "path": "..."
      }
    },
    ...
  ]
}

投入するノード種別と関係:
- (:TypeDefinition {uid, raw_name, canonical_type, description, project, raw_json})
- (:CanonicalType {uid, value, project})
- (:Variant {uid, id, kind, description, project})
- (:Example {uid, value, value_json, explanation, variant, project})
- (:Source {uid, text, path, project})

- (:TypeDefinition)-[:HAS_CANONICAL_TYPE]->(:CanonicalType)
- (:TypeDefinition)-[:HAS_VARIANT]->(:Variant)
- (:TypeDefinition)-[:HAS_EXAMPLE]->(:Example)
- (:TypeDefinition)-[:FROM_SOURCE]->(:Source)

安全のため、すべてのノードに project プロパティを付与します。--wipe-project を使うと
その project に属するノード/リレーションのみを削除できます（危険操作）。
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv

# ---- ロギング ----
LOGGER = logging.getLogger("typedef_etl")
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("[%(levelname)s] %(message)s")
handler.setFormatter(formatter)
LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)


# ---- データモデル ----
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


# ---- ユーティリティ ----


def _to_str(value: Any) -> str:
    """人間可読な文字列化（例: list/dict は JSON 文字列）。"""
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return str(value)


def _slug(fragment: Any) -> str:
    """uid 生成のための簡易 slug（ファイルパスや日本語もそのまま許容）。"""
    s = _to_str(fragment)
    # uid 用に危険な改行やタブだけ潰す
    return s.replace("\n", " ").replace("\r", " ").replace("\t", " ")


# ---- JSON ロード & 正規化 ----


def load_type_definitions(json_path: Path) -> List[Dict[str, Any]]:
    """JSON を素直に読み、type_definitions 配列を返す。
    各定義に source.path が無ければ json_path を補完する。
    """
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
        if "path" not in src:
            src["path"] = str(json_path)
        td["source"] = src
        defs.append(td)
    return defs


# ---- ノード/リレーション構築 ----


def build_graph_elements(
    definitions: List[Dict[str, Any]], *, project: str
) -> Tuple[List[Node], List[Relation]]:
    nodes_map: Dict[str, Node] = {}
    rels: List[Relation] = []

    def add_node(label: str, uid: str, **props: Any) -> None:
        uid_s = _slug(uid)
        props_with_proj = {k: v for k, v in props.items()}
        props_with_proj["project"] = project
        node = Node(label=label, uid=uid_s, props=props_with_proj)
        # 既存なら上書き（同一 uid の集約）
        nodes_map[uid_s] = node

    def add_rel(src_uid: str, rel_type: str, dst_uid: str, **props: Any) -> None:
        rels.append(
            Relation(
                src_uid=_slug(src_uid),
                rel_type=rel_type,
                dst_uid=_slug(dst_uid),
                props=props or None,
            )
        )

    for td in definitions:
        name = td.get("name") or td.get("type_name")
        if not name:
            LOGGER.warning("name の無い型定義をスキップ: %s", td)
            continue

        canonical = td.get("canonical_type", "")
        description = td.get("description", td.get("desc", ""))
        raw_json = json.dumps(td, ensure_ascii=False, separators=(",", ":"))

        t_uid = f"type::{name}"
        add_node(
            "TypeDefinition",
            t_uid,
            raw_name=name,
            canonical_type=_to_str(canonical),
            description=_to_str(description),
            raw_json=raw_json,
        )

        # CanonicalType
        if canonical:
            c_uid = f"canonical::{canonical}"
            add_node("CanonicalType", c_uid, value=_to_str(canonical))
            add_rel(t_uid, "HAS_CANONICAL_TYPE", c_uid)

        # Variants: one_of / variants の両方に対応
        for kind_key in ("one_of", "variants"):
            for v in td.get(kind_key, []) or []:
                if isinstance(v, dict):
                    vid = (
                        v.get("id")
                        or v.get("variant")
                        or v.get("value")
                        or v.get("name")
                        or _to_str(v)
                    )
                    vdesc = v.get("description", v.get("desc", ""))
                else:
                    vid = _to_str(v)
                    vdesc = ""
                v_uid = f"variant::{name}::{vid}"
                add_node(
                    "Variant",
                    v_uid,
                    id=_to_str(vid),
                    kind=kind_key,
                    description=_to_str(vdesc),
                )
                add_rel(t_uid, "HAS_VARIANT", v_uid)

        # Examples: 文字列 or dict(value, explanation, variant)
        for ex in td.get("examples", []) or []:
            if isinstance(ex, dict):
                val = ex.get("value")
                explanation = ex.get("explanation", "")
                vref = ex.get("variant", "")
            else:
                val = ex
                explanation = ""
                vref = ""
            e_uid = f"example::{name}::{_slug(val)}"
            add_node(
                "Example",
                e_uid,
                value=_to_str(val),
                value_json=_to_str(val),
                explanation=_to_str(explanation),
                variant=_to_str(vref),
            )
            add_rel(t_uid, "HAS_EXAMPLE", e_uid)

        # Source
        src = td.get("source") or {}
        if src:
            s_text = src.get("text", "")
            s_path = src.get("path", "")
            s_uid = f"source::{name}::{_slug(s_path) or 'inline'}"
            add_node("Source", s_uid, text=_to_str(s_text), path=_to_str(s_path))
            add_rel(t_uid, "FROM_SOURCE", s_uid)

    return list(nodes_map.values()), rels

# ---- URI 正規化 ----


def normalize_neo4j_uri(uri: str) -> str:
    """bolt/neo4j スキームを強制。例えば "localhost:7687" → "bolt://localhost:7687"。
    Windows でコピペ時の全角/空白も掃除します。
    """
    if not uri:
        return uri
    u = str(uri).strip().replace("　", " ")  # 全角空白除去
    # 余計な引用符を除去
    if (u.startswith("\"") and u.endswith("\"")) or (u.startswith("'") and u.endswith("'")):
        u = u[1:-1]
    if "://" not in u:
        # スキームが無ければ bolt:// を付与
        u = f"bolt://{u}"
    return u


# ---- Neo4j への保存 ----


def persist_to_neo4j(
    *,
    uri: str,
    username: str,
    password: str,
    database: Optional[str],
    nodes: List[Node],
    relations: List[Relation],
    project: str,
    wipe_project: bool = False,
) -> Tuple[int, int]:
    """Neo4j にノード/リレーションを投入。戻り値は (作成/更新ノード数, 関係数)。"""
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(uri, auth=(username, password))

    def run(tx, query: str, **params: Any):
        return tx.run(query, **params)

    with driver.session(database=database) as sess:
        # インデックス/制約（uid をユニーク）
        constraint_queries = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:TypeDefinition) REQUIRE t.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:CanonicalType) REQUIRE c.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (v:Variant) REQUIRE v.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Example) REQUIRE e.uid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Source) REQUIRE s.uid IS UNIQUE",
        ]
        for query in constraint_queries:
            sess.run(query)

        if wipe_project:
            LOGGER.warning(
                "--wipe-project により project=%s のデータを削除します", project
            )
            # 関係を含めて該当ノードを一括削除
            sess.run(
                """
                MATCH (n)
                WHERE n.project = $project
                DETACH DELETE n
                """,
                project=project,
            )

        # ノード投入（MERGE uid, SET props）
        node_count = 0
        for n in nodes:
            query = f"MERGE (n:{n.label} {{uid:$uid}}) SET n += $props RETURN n"
            sess.run(query, uid=n.uid, props=n.props)
            node_count += 1

        # リレーション投入
        rel_count = 0
        for r in relations:
            query = (
                "MATCH (a {uid:$src_uid, project:$project}), (b {uid:$dst_uid, project:$project})\n"
                "MERGE (a)-[rel:%s]->(b) SET rel += $props RETURN rel" % r.rel_type
            )
            sess.run(
                query,
                src_uid=r.src_uid,
                dst_uid=r.dst_uid,
                props=r.props or {},
                project=project,
            )
            rel_count += 1

    driver.close()
    return node_count, rel_count


# ---- トリプル JSON のエクスポート（デバッグ用） ----


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


# ---- LlamaIndex の簡易疎通（任意） ----


def try_build_property_graph_index(
    uri: str, username: str, password: str, database: Optional[str]
) -> None:
    """LlamaIndex の Neo4jGraphStore に接続できるかの簡易検証（失敗しても処理続行）。"""
    try:
        from llama_index.graph_stores.neo4j import Neo4jGraphStore

        store = None
        try:
            store = Neo4jGraphStore(
                uri=uri, username=username, password=password, database=database
            )
        except TypeError:
            # 一部のバージョンは url 引数
            store = Neo4jGraphStore(
                url=uri, username=username, password=password, database=database
            )
        # 軽いクエリ
        # 注意: LlamaIndex の API は頻繁に変わるため、ここでは疎通だけ確認
        LOGGER.info("LlamaIndex Neo4jGraphStore に接続できました: %s", type(store))
    except Exception as e:
        LOGGER.warning("LlamaIndex の GraphStore 接続はスキップ/失敗しました: %s", e)


# ---- CLI ----


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="type_definitions.json を Neo4j に ETL")
    p.add_argument(
        "--json-path",
        type=Path,
        default=Path(__file__).with_name("type_definitions.json"),
        help="入力 JSON (type_definitions.json)",
    )
    p.add_argument(
        "--neo4j-uri",
        type=str,
        default=os.getenv("NEO4J_URI"),
        help="Neo4j URI (bolt://...) または neo4j://",
    )
    p.add_argument("--neo4j-user", type=str, default=os.getenv("NEO4J_USERNAME"), help="Neo4j ユーザ名")
    p.add_argument("--neo4j-password", type=str, default=os.getenv("NEO4J_PASSWORD"), help="Neo4j パスワード")
    p.add_argument(
        "--database",
        type=str,
        default="demo",
        help="データベース名（未指定でデフォルト DB）",
    )
    p.add_argument(
        "--project",
        type=str,
        default="type_definitions",
        help="project ラベル用の論理名（削除等のスコープに使う）",
    )
    p.add_argument(
        "--wipe-project",
        action="store_true",
        help="project に属する既存データを削除してから投入（危険）",
    )
    p.add_argument(
        "--export-triples-json",
        type=Path,
        default=None,
        help="投入前にトリプルを JSON に書き出し",
    )
    p.add_argument(
        "--dry-run", action="store_true", help="Neo4j には書き込まず件数だけ確認"
    )
    p.add_argument(
        "--create-property-graph-index",
        action="store_true",
        help="LlamaIndex GraphStore への疎通確認を行う",
    )
    p.add_argument("--verbose", action="store_true")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    load_dotenv()
    args = parse_args(argv)
    if args.verbose:
        LOGGER.setLevel(logging.DEBUG)

    LOGGER.info("JSON を読み込み: %s", args.json_path)
    definitions = load_type_definitions(args.json_path)
    LOGGER.info("定義の件数: %d", len(definitions))

    nodes, rels = build_graph_elements(definitions, project=args.project)
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
        LOGGER.error("Neo4j URI が指定されていません (--neo4j-uri か NEO4J_URI を設定してください)")
        return 3

    if args.dry_run:
        LOGGER.info("--dry-run のため Neo4j への書き込みはスキップします")
    else:
        n_count, r_count = persist_to_neo4j(
            uri=neo4j_uri,
            username=args.neo4j_user,
            password=args.neo4j_password,
            database=args.database,
            nodes=nodes,
            relations=rels,
            project=args.project,
            wipe_project=args.wipe_project,
        )
        LOGGER.info("Neo4j へ投入完了: ノード %d, リレーション %d", n_count, r_count)

    if args.create_property_graph_index:
        try_build_property_graph_index(
            neo4j_uri, args.neo4j_user, args.neo4j_password, args.database
        )

    LOGGER.info("完了")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
