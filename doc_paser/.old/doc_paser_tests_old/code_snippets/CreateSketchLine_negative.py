# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.CreateSketchLine(
    SketchPlane_element,               # 直線を作成するスケッチ要素
    "SketchLineName_value",               # 作成するスケッチ直線名称（空文字可）
    SketchLayer_element,               # 直線を作成するスケッチレイヤー（空文字可）
    (0.0, 0.0),               # 始点（点(2D)）
    (0.0, 0.0),               # 終点（点(2D)）
    # Missing the last argument: bUpdate
)