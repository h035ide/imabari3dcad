from pathlib import Path

from doc_preprocessor_hybrid.rule_parser import parse_api_documents, parse_type_definitions


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
