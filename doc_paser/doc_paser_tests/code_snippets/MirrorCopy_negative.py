# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.MirrorCopy(
    XY_PLANE                # ミラーコピーを行う平面（ドキュメントは "[in] BSTR plane" と記載）
    # Missing the last argument: ReferMethod
)