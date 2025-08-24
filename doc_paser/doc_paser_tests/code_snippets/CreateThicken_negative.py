# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.CreateThicken(
    "ThickenFeatureName",               # 作成する厚みづけフィーチャー要素名称（空文字可）
    TargetSolidName_element,               # 厚みづけフィーチャーを作成する対象のソリッド
    "UNION",               # ソリッドオペレーションのタイプを指定（ボディ演算の記号）
    "SINGLE",               # 厚み付けタイプ
    100.0,               # 板厚（厚み1）
    100.0,               # 板厚2（厚み付けタイプが2方向のときに使用）
    100.0,               # 厚みづけをするシート、フェイス要素のオフセット距離
    "GEOMETRIC"                # 要素の関連づけ方法の指定
    # Missing the last argument: bUpdate
)