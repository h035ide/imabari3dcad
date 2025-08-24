# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.CreateSketchPlane(
    "ElementName",               # 作成するスケッチ平面名称（空文字可）
    ElementGroup_element,               # 作成するスケッチ平面を要素グループに入れる場合は要素グループを指定（空文字可）
    XY_PLANE,               # スケッチ平面を作成する平面を指定する
    100.0,               # 平面からのオフセット距離を指定
    True,               # スケッチ平面を反転するかどうかのフラグ
    True,               # スケッチ平面のX,Y軸を交換するかどうかのフラグ
    True,               # ドキュメント上の名称が "謎" とされているパラメータ（型は bool と記載）。詳細不明
    "DEFAULT_STYLE",               # スケッチ平面に適用する注記スタイル名称（空文字可）
    (0.0, 0.0),               # スケッチ平面の原点を指定（空文字可）
    (1.0, 0.0, 0.0),               # スケッチ平面の軸方向を指定（空文字可）
    True                # スケッチ平面のX軸を指定する場合は True
    # Missing the last argument: bUpdate
)