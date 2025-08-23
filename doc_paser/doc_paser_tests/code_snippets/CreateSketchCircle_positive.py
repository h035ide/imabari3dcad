# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.CreateSketchCircle(
    sketch_plane_id,             # スケッチ平面
    config.circle_name,          # 円の名称
    config.sketch_layer,         # スケッチレイヤー
    config.center_point,         # 中心点（原点）
    str(config.radius_mm),       # 半径
    config.use_diameter,         # 直径指定フラグ（False=半径指定）
    config.counter_clockwise,    # 反時計回り
    config.update_flag           # 更新フラグ
)
