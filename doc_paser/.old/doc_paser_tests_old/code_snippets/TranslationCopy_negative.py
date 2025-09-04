# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.TranslationCopy(
    [element_1, element_2],               # コピーする要素（配列）
    1,               # コピーする数
    (1.0, 0.0, 0.0),               # コピーする方向
    100.0,               # 移動距離
    # Missing the last argument: ReferMethod
)