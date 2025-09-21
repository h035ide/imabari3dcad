from pathlib import Path

from doc_preprocessor_hybrid.rule_parser import (
    ApiBundle,
    ApiEntry,
    Parameter,
    ReturnSpec,
    TypeDefinition,
    dump_bundle,
    load_bundle,
)


def test_load_bundle_roundtrip(tmp_path):
    bundle = ApiBundle(
        type_definitions=[
            TypeDefinition(
                name="長さ",
                description="mm単位の数値のいずれか。",
                examples=["10.0"],
                canonical_type="length",
                py_type="str",
                one_of=["millimeter_literal"],
            )
        ],
        api_entries=[
            ApiEntry(
                entry_type="function",
                name="Foo",
                description="demo",
                category="Test",
                params=[
                    Parameter(
                        name="Value",
                        type="長さ",
                        description="長さ",
                        is_required=True,
                        position=0,
                        raw_type="long",
                    )
                ],
                properties=[],
                returns=ReturnSpec(type="void", description=""),
                notes=None,
                implementation_status="implemented",
                object_name="TestObject",
                title_jp="テスト",
                raw_return="",
            )
        ],
        checklist=["parsed_api_doc"],
    )

    out_path = tmp_path / "bundle.json"
    dump_bundle(bundle, out_path)
    loaded = load_bundle(out_path)

    assert loaded.checklist == ["parsed_api_doc"]
    assert loaded.type_definitions[0].name == "長さ"
    assert loaded.type_definitions[0].py_type == "str"
    assert loaded.api_entries[0].params[0].metadata()["position"] == 0
    assert loaded.api_entries[0].returns.type == "void"
