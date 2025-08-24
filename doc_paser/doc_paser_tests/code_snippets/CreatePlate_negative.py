# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.CreatePlate(
    "PlateName",               # 作成するプレートソリッド要素名称（空文字可）
    ElementGroup_element,               # 作成するソリッド要素を要素グループに入れる場合は要素グループを指定（空文字可）
    "STEEL",               # 作成するソリッド要素の材質名称（空文字可）
    XY_PLANE,               # プレートの平面位置
    100.0,               # 平面のオフセット距離
    100.0,               # 板厚
    "TOP",               # モールド位置
    100.0,               # モールド位置のオフセット距離
    BoundSolid_element,               # プレートソリッドの境界となるソリッド要素
    100.0,               # 平面上の方向1の境界位置の座標値1
    100.0,               # 平面上の方向1の境界位置の座標値2
    100.0,               # 平面上の方向2の境界位置の座標値1
    100.0                # 平面上の方向2の境界位置の座標値2
    # Missing the last argument: bUpdate
)