# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.CreateOtherSolid(
    "OtherSolidFeatureName_value",               # 作成する別ソリッドフィーチャー要素名称（空文字可）
    TargetSolidName_element,               # 別ソリッドフィーチャーを作成する対象のソリッド
    "+",               # ソリッドオペレーションのタイプを指定する
    SourceSolid_element,               # 別ソリッドフィーチャーとするソリッド要素
    "GEOMETRIC",               # 要素の関連づけ方法の指定
    # Missing the last argument: bUpdate
)