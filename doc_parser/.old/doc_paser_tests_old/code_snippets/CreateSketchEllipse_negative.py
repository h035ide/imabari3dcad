# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.CreateSketchEllipse(
    SketchPlane_element,               # 楕円を作成するスケッチ要素
    "SketchArcName_value",               # 作成するスケッチ楕円名称（空文字可）
    SketchLayer_element,               # 楕円を作成するスケッチレイヤー（空文字可）
    (0.0, 0.0),               # 中心点（点(2D)）
    True,               # 楕円の回転方向。True の場合は反時計回り
    (1.0, 0.0, 0.0),               # 主軸方向を指定（方向(2D)）
    100.0,               # 主軸半径
    100.0,               # 副軸半径
    (0.0, 2*3.14159),               # 楕円の範囲（0-2pi等）
    # Missing the last argument: bUpdate
)