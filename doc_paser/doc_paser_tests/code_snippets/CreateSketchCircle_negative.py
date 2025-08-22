# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments (7 instead of 8).
# The test itself should PASS if the validator correctly identifies this failure.

part.CreateSketchCircle(
    sketch_plane_id,             # スケッチ平面
    config.circle_name,          # 円の名称
    config.sketch_layer,         # スケッチレイヤー
    config.center_point,         # 中心点（原点）
    str(config.radius_mm),       # 半径
    config.use_diameter,         # 直径指定フラグ（False=半径指定）
    config.counter_clockwise     # 反時計回り
    # Missing the last argument: config.update_flag
)
