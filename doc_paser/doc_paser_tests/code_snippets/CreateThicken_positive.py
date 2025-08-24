# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.CreateThicken(
    "ThickenFeatureName",               # 作成する厚みづけフィーチャー要素名称（空文字可）
    TargetSolidName_element,               # 厚みづけフィーチャーを作成する対象のソリッド
    "UNION",               # ソリッドオペレーションのタイプを指定（ボディ演算の記号）
    "SINGLE",               # 厚み付けタイプ
    100.0,               # 板厚（厚み1）
    100.0,               # 板厚2（厚み付けタイプが2方向のときに使用）
    100.0,               # 厚みづけをするシート、フェイス要素のオフセット距離
    "GEOMETRIC",               # 要素の関連づけ方法の指定
    True                # 更新フラグ（未実装、使用しない）
)