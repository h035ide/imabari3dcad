# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.CreateSketchNURBSCurve(
    SketchPlane_element,               # ＮＵＲＢＳ線を作成するスケッチ要素
    "SketchArcName_value",               # 作成するスケッチＮＵＲＢＳ線名称（空文字可）
    SketchLayer_element,               # ＮＵＲＢＳ線を作成するスケッチレイヤー（空文字可）
    1,               # ＮＵＲＢＳ線の次数
    True,               # 閉じたＮＵＲＢＳ線の場合 True
    True,               # 周期ＮＵＲＢＳ線の場合 True
    (0.0, 0.0),               # 制御点（点の配列）
    1.0,               # 重み（浮動小数点の配列）
    1.0,               # ノットベクトル（浮動小数点の配列）
    (0.0, 2*3.14159),               # トリム範囲
    # Missing the last argument: bUpdate
)