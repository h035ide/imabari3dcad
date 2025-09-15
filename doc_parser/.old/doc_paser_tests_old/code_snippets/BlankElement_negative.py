# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.BlankElement(
    Element_element,               # 表示状態を指定する要素
    # Missing the last argument: bBlank
)