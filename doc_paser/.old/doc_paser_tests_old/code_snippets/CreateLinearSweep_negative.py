# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.CreateLinearSweep(
    TargetSolidName_element,               # 押し出しフィーチャーを作成する対象のソリッド
    "+",               # ソリッドオペレーションのタイプを指定する
    "pParam_value",               # 押し出しパラメータオブジェクト
    # Missing the last argument: bUpdate
)