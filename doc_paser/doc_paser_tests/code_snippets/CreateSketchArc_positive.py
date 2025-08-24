# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.CreateSketchArc(
    SketchPlane_element,               # 円弧を作成するスケッチ要素
    "SketchArcName",               # 作成するスケッチ円弧名称（空文字可）
    SketchLayer_element,               # 円弧を作成するスケッチレイヤー（空文字可）
    (0.0, 0.0),               # 中心点（点(2D)）
    (0.0, 0.0),               # 始点（点(2D)）
    (0.0, 0.0),               # 終点（点(2D)）
    True,               # 円弧の回転方向。True の場合は反時計回り
    True                # 更新フラグ（未実装、使用しない）
)