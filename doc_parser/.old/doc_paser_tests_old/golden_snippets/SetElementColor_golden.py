# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.SetElementColor(
    Element_element,               # 色を設定する要素
    1,               # 赤色の値 (0-255)
    1,               # 緑色の値 (0-255)
    1,               # 青色の値 (0-255)
    1.0                # 透明度の指定 (0.0 = 不透明, 1.0 = 完全透明 として記載されているがドキュメントでは 0.0不透明-1.0透明 と表記)
)