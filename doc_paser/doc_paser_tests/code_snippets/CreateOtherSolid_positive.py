# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.CreateOtherSolid(
    "OtherSolidFeatureName",               # 作成する別ソリッドフィーチャー要素名称（空文字可）
    TargetSolidName_element,               # 別ソリッドフィーチャーを作成する対象のソリッド
    "UNION",               # ソリッドオペレーションのタイプを指定する
    SourceSolid_element,               # 別ソリッドフィーチャーとするソリッド要素
    "GEOMETRIC",               # 要素の関連づけ方法の指定
    True                # 更新フラグ（未実装、使用しない）
)