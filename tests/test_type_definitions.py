from pathlib import Path
import json
from types import SimpleNamespace
from typing import Any

import pytest

from doc_preprocessor_hybrid.rule_parser import parse_api_documents, parse_type_definitions
from structured_api import type_definitions as typedef_mod


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_type_definitions_have_canonical_metadata():
    text = (PROJECT_ROOT / "data" / "src" / "api_arg.txt").read_text(encoding="utf-8")
    definitions = parse_type_definitions(text)

    length_def = next(defn for defn in definitions if defn.canonical_type == "length")
    assert length_def.py_type == "str"
    assert length_def.one_of == ["millimeter_literal", "variable_reference", "expression"]
    assert "のいずれか" in length_def.description

    point_2d_def = next(defn for defn in definitions if defn.name.endswith("(2D)"))
    point_3d_def = next(defn for defn in definitions if defn.name.endswith("(3D)"))
    assert point_2d_def.canonical_type == "point"
    assert point_2d_def.py_type == "str"
    assert point_3d_def.one_of[0] == "cartesian_3d"

    element_def = next(defn for defn in definitions if defn.canonical_type == "element")
    for role in ["element_id", "element_group", "element_reference", "element_array"]:
        assert role in element_def.one_of
        assert role in element_def.description


def test_parameter_dimension_tags_match_point_definitions():
    bundle = parse_api_documents(
        PROJECT_ROOT / "data" / "src" / "api.txt",
        PROJECT_ROOT / "data" / "src" / "api_arg.txt",
    )
    sketch_line = next(entry for entry in bundle.api_entries if entry.name == "CreateSketchLine")
    point_types = [param.type for param in sketch_line.params if param.name in {"StartPoint", "EndPoint"}]
    assert all(pt.endswith("(2D)") for pt in point_types)

    line3d = next(entry for entry in bundle.api_entries if entry.name == "CreateLine")
    point3d_types = [param.type for param in line3d.params if param.name in {"StartPoint", "EndPoint"}]
    assert all(pt.endswith("(3D)") for pt in point3d_types)


@pytest.fixture
def sample_type_definition(tmp_path):
    payload = {
        "type_definitions": [
            {
                "name": "Foo",
                "canonical_type": "string",
                "description": "sample",
            }
        ]
    }
    json_path = tmp_path / "type_definitions.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return json_path


def test_load_type_definitions_json_reader_stub(sample_type_definition, monkeypatch):
    created = {}

    class StubDocument:
        def __init__(self, text: str, metadata: dict[str, Any] | None = None):
            self.text = text
            self.metadata = metadata or {}

    class StubJSONReader:
        def __init__(self, *, jq_schema: str, text_content: bool):
            created["jq_schema"] = jq_schema
            created["text_content"] = text_content

        def load_data(self, path):
            assert path == sample_type_definition
            return [StubDocument(json.dumps({"name": "Foo"}))]

    monkeypatch.setattr(typedef_mod, "JSONReader", StubJSONReader)
    definitions, raw_documents = typedef_mod.load_type_definitions(
        sample_type_definition, jq_schema=".type_definitions[]"
    )

    assert definitions[0]["name"] == "Foo"
    assert definitions[0]["source"]["path"] == str(sample_type_definition)
    assert created["jq_schema"] == ".type_definitions[]"
    assert created["text_content"] is True
    assert isinstance(raw_documents[0], StubDocument)


def test_load_type_definitions_fallback(monkeypatch, sample_type_definition):
    class BrokenJSONReader:
        def __init__(self, **_kwargs):
            pass

        def load_data(self, _path):
            raise RuntimeError("broken reader")

    monkeypatch.setattr(typedef_mod, "JSONReader", BrokenJSONReader)
    definitions, raw_documents = typedef_mod.load_type_definitions(sample_type_definition)

    assert definitions[0]["name"] == "Foo"
    assert raw_documents == []


def test_build_graph_elements_llm_enrichment(monkeypatch):
    typedefs = [
        {
            "name": "Foo",
            "alias": [],
            "variants": [],
            "examples": [],
        }
    ]
    documents = [SimpleNamespace(text="", metadata={"name": "Foo"})]

    class StubExtractor:
        def extract(self, _docs):
            return [SimpleNamespace(to_dict=lambda: {"aliases": ["Bar"]})]

    monkeypatch.setattr(typedef_mod, "_create_llm_path_extractor", lambda **_: StubExtractor())
    nodes, relations = typedef_mod.build_graph_elements(
        typedefs,
        documents=documents,
        use_llm_extractor=True,
        llm_model=None,
        llm_temperature=0.0,
    )

    assert relations == []
    primary = next(node for node in nodes if node.id == "type::Foo")
    assert primary.properties.get("llm_extractions") == {"aliases": ["Bar"]}


def test_persist_to_neo4j_property_graph(monkeypatch):
    recorded: dict[str, object] = {}

    class RecorderStore:
        def __init__(self, *, url: str, username: str, password: str, database):
            recorded["init"] = (url, username, password, database)
            self.nodes: list[typedef_mod.EntityNode] = []
            self.relations: list[typedef_mod.Relation] = []

        def upsert_nodes(self, nodes):
            self.nodes.extend(nodes)

        def upsert_relations(self, relations):
            self.relations.extend(relations)

    class StubStorageContext:
        def __init__(self, graph_store):
            self.graph_store = graph_store

        @classmethod
        def from_defaults(cls, *, graph_store=None, **_kwargs):
            return cls(graph_store)

    class RecorderGraphDocument:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class RecorderPropertyGraphIndex:
        @classmethod
        def from_graph_documents(cls, docs, storage_context, show_progress=False):
            recorded["graph_documents"] = docs
            recorded["storage_context"] = storage_context
            recorded["show_progress"] = show_progress

    monkeypatch.setattr(typedef_mod, "Neo4jPropertyGraphStore", RecorderStore)
    monkeypatch.setattr(typedef_mod, "StorageContext", StubStorageContext)
    monkeypatch.setattr(typedef_mod, "GraphDocument", RecorderGraphDocument)
    monkeypatch.setattr(typedef_mod, "PropertyGraphIndex", RecorderPropertyGraphIndex)

    node = typedef_mod.EntityNode(
        id="type::Foo",
        name="Foo",
        label="TypeDefinition",
        properties={"raw_name": "Foo"},
    )
    relation = typedef_mod.Relation(
        label="HAS_ALIAS",
        source_id="type::Foo",
        target_id="alias::Foo",
        properties={},
    )

    node_count, relation_count, built = typedef_mod.persist_to_neo4j(
        [node],
        [relation],
        uri="bolt://localhost:7687",
        username="neo4j",
        password="test",
        database=None,
        build_property_graph_index=True,
    )

    assert node_count == 1
    assert relation_count == 1
    assert built is True
    assert recorded["graph_documents"][0].kwargs["metadata"]["source"] == "type_definitions"
    assert recorded["show_progress"] is False
