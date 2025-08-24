# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.SheetAlignNormal(
    SheetElement_element,               # 方向を揃えるシート要素
    1.0,               # 方向ベクトルのX成分
    1.0                # 方向ベクトルのY成分
    # Missing the last argument: dirZ
)