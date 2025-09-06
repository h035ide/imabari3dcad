# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.CreateOffsetSheet(
    "SheetName_value",               # 作成するシート要素名称（空文字可）
    ElementGroup_element,               # 作成するシート要素を要素グループに入れる場合は要素グループを指定（空文字可）
    "STEEL",               # 作成するシート要素の材質名称（空文字可）
    [surface_element_1, surface_element_2],               # オフセットする元シート要素、フェイス要素の指定文字列配列
    100.0,               # オフセット距離
    True,               # オフセット方向を反転するフラグ
    True                # 更新フラグ（未実装、使用しない）
)