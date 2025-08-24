# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.CreateOffsetSheet(
    "SheetName",               # 作成するシート要素名称（空文字可）
    ElementGroup_element,               # 作成するシート要素を要素グループに入れる場合は要素グループを指定（空文字可）
    "STEEL",               # 作成するシート要素の材質名称（空文字可）
    100.0,               # オフセット距離
    True                # オフセット方向を反転するフラグ
    # Missing the last argument: bUpdate
)