# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.CreateVariable(
    "VariableName",               # 作成する変数名称（空文字不可）
    1.0,               # 変数の値
    "MM",               # 作成する変数の単位を指定
    VariableElementGroup_element                # 作成する変数要素を要素グループに入れる場合は要素グループを指定（空文字可）
)