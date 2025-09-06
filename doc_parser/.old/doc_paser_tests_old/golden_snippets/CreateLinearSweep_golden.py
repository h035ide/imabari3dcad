# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.CreateLinearSweep(
    TargetSolidName_element,               # 押し出しフィーチャーを作成する対象のソリッド
    "+",               # ソリッドオペレーションのタイプを指定する
    "pParam_value",               # 押し出しパラメータオブジェクト
    True                # 更新フラグ（未実装、使用しない）
)