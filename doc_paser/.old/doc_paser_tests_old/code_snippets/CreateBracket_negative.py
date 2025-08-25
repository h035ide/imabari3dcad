# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.CreateBracket(
    ParamObj_element,               # ブラケットパラメータオブジェクト
    # Missing the last argument: bUpdate
)