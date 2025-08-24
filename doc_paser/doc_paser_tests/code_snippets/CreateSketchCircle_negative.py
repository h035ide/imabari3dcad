# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.CreateSketchCircle(
    SketchPlane_element,               # 円を作成するスケッチ要素
    "SketchArcName",               # 作成するスケッチ円名称（空文字可）
    SketchLayer_element,               # 円を作成するスケッチレイヤー（空文字可）
    (0.0, 0.0),               # 中心点（点(2D)）
    100.0,               # 半径または直径（長さ）
    True,               # 直径を指定する場合は True
    True                # 円の回転方向。True の場合は反時計回り
    # Missing the last argument: bUpdate
)