from pathlib import Path

from doc_preprocessor_hybrid.rule_parser import parse_api_documents


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_set_element_color_params_and_return():
    bundle = parse_api_documents(
        PROJECT_ROOT / "data" / "src" / "api.txt",
        PROJECT_ROOT / "data" / "src" / "api_arg.txt",
    )
    entry = next(item for item in bundle.api_entries if item.name == "SetElementColor")

    assert [param.name for param in entry.params] == [
        "Element",
        "RValue",
        "GValue",
        "BValue",
        "Transparency",
    ]

    assert [param.type for param in entry.params] == [
        "要素",
        "整数",
        "整数",
        "整数",
        "浮動小数点",
    ]

    assert entry.raw_return == ""
    assert entry.returns is not None
    assert entry.returns.type == "void"
    assert entry.returns.description == ""
    assert entry.returns.is_array is False
