import win32com.client

# --- コンフィグ設定 ---
class CylinderConfig:
    """円柱作成の設定値を管理するクラス"""

    def __init__(self, radius_mm=50.0, height_mm=50.0):
        # 円柱の基本パラメータ
        self.radius_mm = radius_mm
        self.height_mm = height_mm

        # 座標設定
        self.center_point = "0.0,0.0"  # 円の中心点（2D座標）
        self.plane_offset = "0.0"      # スケッチ平面のオフセット距離

        # 平面設定
        self.sketch_plane = "PL,Z"     # XY平面を指定

        # 要素名設定
        self.sketch_plane_name = "SketchPlane1"
        self.circle_name = "Circle1"
        self.solid_name = "Cylinder1"
        self.sweep_name = "CylinderSweep"

        # スケッチレイヤー設定
        self.sketch_layer = "デフォルト"

        # 押し出し設定
        self.direction_type = "N"      # スイープ方向（N:順方向, R:反対方向）
        self.sweep_direction = "+Z"    # スイープ方向（Z軸正方向）
        self.operation_type = "+"      # オペレーションタイプ（+:和）

        # スケッチ設定
        self.use_diameter = False      # 直径指定フラグ（False=半径指定）
        self.counter_clockwise = True  # 反時計回りフラグ
        self.update_flag = False       # 更新フラグ

        # 平面作成設定
        self.plane_reverse = True      # 平面反転フラグ
        self.uv_swap = False           # UV軸交換フラグ
        self.default_axis_x = True     # デフォルト軸をX軸にする
        self.default_axis_flag = False  # デフォルト軸フラグ

# --- 初期化処理 ---
def initialize_evoship():
    evoship = win32com.client.DispatchEx("EvoShip.Application")
    evoship.ShowMainWindow(True)
    doc = evoship.Create3DDocument()
    part = doc.GetPart()
    return evoship, doc, part

# --- スケッチ平面作成 ---
def create_sketch_plane(part, config):
    return part.CreateSketchPlane(
        config.sketch_plane_name,    # 要素名
        "",                          # 要素グループ（空文字）
        config.sketch_plane,         # 平面指定
        config.plane_offset,         # オフセット距離
        config.plane_reverse,        # 平面反転フラグ
        config.uv_swap,              # UV軸交換フラグ
        config.default_axis_flag,    # デフォルト軸フラグ
        "",                          # 注記スタイル
        "",                          # 原点
        "",                          # 軸方向
        config.default_axis_x,       # デフォルト軸をX軸にする
        False                        # 更新フラグ
    )

# --- 円スケッチ作成 ---
def create_circle(part, sketch_plane_id, config):
    return part.CreateSketchCircle(
        sketch_plane_id,             # スケッチ平面
        config.circle_name,          # 円の名称
        config.sketch_layer,         # スケッチレイヤー
        config.center_point,         # 中心点（原点）
        str(config.radius_mm),       # 半径
        config.use_diameter,         # 直径指定フラグ（False=半径指定）
        config.counter_clockwise,    # 反時計回り
        config.update_flag           # 更新フラグ
    )

# --- ソリッド要素作成 ---
def create_solid(part, config):
    return part.CreateSolid(config.solid_name, "", "")

# --- 押し出しパラメータ作成 ---
def create_sweep_param(part, circle_id, config):
    sweep_param = part.CreateLinearSweepParam()
    sweep_param.Name = config.sweep_name
    sweep_param.AddProfile(circle_id)
    sweep_param.DirectionType = config.direction_type
    sweep_param.DirectionParameter1 = str(config.height_mm)
    sweep_param.SweepDirection = config.sweep_direction
    return sweep_param

# --- 押し出し実行 ---
def create_linear_sweep(part, solid_id, sweep_param, config):
    return part.CreateLinearSweep(str(solid_id), config.operation_type, sweep_param, False)

# --- 要素非表示 ---
def blank_element(part, element_id):
    part.BlankElement(element_id, True)

# --- メイン処理 ---
def main():
    # デフォルト設定で円柱を作成
    config = CylinderConfig()
    evoship, doc, part = initialize_evoship()
    sketch_plane_id = create_sketch_plane(part, config)
    blank_element(part, sketch_plane_id)
    circle_id = create_circle(part, sketch_plane_id, config)
    solid_id = create_solid(part, config)
    sweep_param = create_sweep_param(part, circle_id, config)
    cylinder_feature_id = create_linear_sweep(
        part, solid_id, sweep_param, config)
    blank_element(part, circle_id)

    print(f"半径{config.radius_mm}mmの円を長さ{config.height_mm}mmで押し出した円柱を生成しました")
    print(f"スケッチ平面ID: {sketch_plane_id}")
    print(f"円ID: {circle_id}")
    print(f"ソリッドID: {solid_id}")
    print(f"円柱フィーチャーID: {cylinder_feature_id}")


if __name__ == "__main__":
    main()
