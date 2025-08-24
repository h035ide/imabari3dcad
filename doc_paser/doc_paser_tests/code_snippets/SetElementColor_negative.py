# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.SetElementColor(
    Element_element,               # 色を設定する要素
    1,               # 赤色の値 (0-255)
    1,               # 緑色の値 (0-255)
    1                # 青色の値 (0-255)
    # Missing the last argument: Transparency
)