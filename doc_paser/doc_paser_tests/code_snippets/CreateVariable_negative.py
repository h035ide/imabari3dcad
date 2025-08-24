# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.CreateVariable(
    "VariableName",               # 作成する変数名称（空文字不可）
    1.0,               # 変数の値
    "MM"                # 作成する変数の単位を指定
    # Missing the last argument: VariableElementGroup
)