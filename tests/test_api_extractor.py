from __future__ import annotations

from api_extractor import ApiExtractor, parse_type_definitions


type_text = """
■文字列
    通常の文字列

■bool
    真偽値

■長さ
    単位付きの距離
"""


def test_type_parser_extracts_all_definitions():
    definitions = parse_type_definitions(type_text)
    names = [definition.name for definition in definitions]
    assert names == ["文字列", "bool", "長さ"]
    assert definitions[2].description == "単位付きの距離"


def test_api_extractor_parses_functions_and_objects():
    api_text = """
■Applicationオブジェクトのメソッド
〇アプリを終了する
　返り値:なし
  Quit()
〇メインウィンドウを表示
　返り値:なし
  ShowMainWindow(
        bShow ) // bool: 表示する時はTrue (通常はFalse)
〇設定オブジェクト
  属性
    Name // 文字列: 名前（空文字可）
    Thickness // 長さ: 板厚
"""
    definitions = parse_type_definitions(type_text)
    extractor = ApiExtractor(definitions)
    entries = extractor.parse_api_text(api_text)
    assert [entry.name for entry in entries] == ["Quit", "ShowMainWindow", "設定オブジェクト"]
    quit_entry = entries[0]
    assert quit_entry.returns.type == "void"
    show_entry = entries[1]
    assert show_entry.params[0].name == "bShow"
    assert show_entry.params[0].type == "bool"
    assert show_entry.params[0].is_required is False
    assert show_entry.params[0].default_value == "False"
    obj_entry = entries[2]
    assert obj_entry.entry_type == "object"
    assert obj_entry.properties[0].type == "文字列"
    assert obj_entry.properties[0].description.startswith("名前")
