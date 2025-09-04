# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.BodyDivideByElements(
    "drive_feature_name",               # 作成する分割フィーチャー要素名称（空文字可）
    pTargetBody_element,               # 分割対象のボディ
    [divide_element_1, divide_element_2],               # 分割をする要素（シートボディ、フェイス、平面要素）
    (1.0, 0.0, 0.0),               # 分割されたボディ要素の順番を整列させるのに使用する方向
    pWCS_element,               # 方向を定義する座標系（通常は指定しない）
    "GEOMETRIC",               # 要素の関連づけ方法の指定
    # Missing the last argument: bUpdate
)