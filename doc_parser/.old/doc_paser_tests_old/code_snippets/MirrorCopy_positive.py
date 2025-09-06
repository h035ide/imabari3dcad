# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.MirrorCopy(
    [element_1, element_2],               # コピーする要素（配列）
    "PL,Z",               # ミラーコピーを行う平面（ドキュメントは "[in] BSTR plane" と記載）
    "GEOMETRIC"                # 要素の関連づけ方法の指定
)