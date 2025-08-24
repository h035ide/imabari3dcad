# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.CreateSketchLayer(
    "SketchLayerName"                # 作成するスケッチレイヤー名称（空文字可）
    # Missing the last argument: SketchPlane
)