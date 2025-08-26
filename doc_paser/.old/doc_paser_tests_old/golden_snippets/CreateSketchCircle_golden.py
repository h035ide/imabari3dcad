# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.CreateSketchCircle(
    SketchPlane_element,               # 円を作成するスケッチ要素
    "SketchArcName_value",               # 作成するスケッチ円名称（空文字可）
    SketchLayer_element,               # 円を作成するスケッチレイヤー（空文字可）
    (0.0, 0.0),               # 中心点（点(2D)）
    100.0,               # 半径または直径（長さ）
    True,               # 直径を指定する場合は True
    True,               # 円の回転方向。True の場合は反時計回り
    True                # 更新フラグ（未実装、使用しない）
)