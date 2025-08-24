# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.BodySeparateBySubSolids(
    "pSeparateFeatureName",               # 作成する分割フィーチャー要素名称（空文字可）
    pTargetBody_element,               # 分割対象のボディ
    (1.0, 0.0, 0.0),               # 分割されたボディ要素の順番を整列させるのに使用する方向
    "GEOMETRIC"                # 要素の関連づけ方法の指定
    # Missing the last argument: bUpdate
)