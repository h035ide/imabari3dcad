# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.CreateSketchArc3Pts(
    SketchPlane_element,               # 円弧を作成するスケッチ要素
    "SketchArcName_value",               # 作成するスケッチ円弧名称（空文字可）
    SketchLayer_element,               # 円弧を作成するスケッチレイヤー（空文字可）
    (0.0, 0.0),               # 始点（点(2D)）
    (0.0, 0.0),               # 通過点（点(2D)）
    (0.0, 0.0),               # 終点（点(2D)）
    # Missing the last argument: bUpdate
)