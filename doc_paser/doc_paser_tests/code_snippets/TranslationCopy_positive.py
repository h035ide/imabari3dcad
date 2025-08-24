# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.TranslationCopy(
    1,               # コピーする数
    (1.0, 0.0, 0.0),               # コピーする方向
    100.0,               # 移動距離
    "GEOMETRIC"                # 要素の関連づけ方法の指定
)