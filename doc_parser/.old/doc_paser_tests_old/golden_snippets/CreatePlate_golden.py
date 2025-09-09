# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.CreatePlate(
    "PlateName_value",               # 作成するプレートソリッド要素名称（空文字可）
    ElementGroup_element,               # 作成するソリッド要素を要素グループに入れる場合は要素グループを指定（空文字可）
    "STEEL",               # 作成するソリッド要素の材質名称（空文字可）
    "PL,Z",               # プレートの平面位置
    100.0,               # 平面のオフセット距離
    100.0,               # 板厚
    "+",               # モールド位置
    100.0,               # モールド位置のオフセット距離
    BoundSolid_element,               # プレートソリッドの境界となるソリッド要素
    100.0,               # 平面上の方向1の境界位置の座標値1
    100.0,               # 平面上の方向1の境界位置の座標値2
    100.0,               # 平面上の方向2の境界位置の座標値1
    100.0,               # 平面上の方向2の境界位置の座標値2
    True                # 更新フラグ（未実装、使用しない）
)