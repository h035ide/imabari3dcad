# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.CreateSketchLine(
    SketchPlane_element,               # 直線を作成するスケッチ要素
    "SketchLineName",               # 作成するスケッチ直線名称（空文字可）
    SketchLayer_element,               # 直線を作成するスケッチレイヤー（空文字可）
    (0.0, 0.0),               # 始点（点(2D)）
    (0.0, 0.0),               # 終点（点(2D)）
    True                # 更新フラグ（未実装、使用しない）
)