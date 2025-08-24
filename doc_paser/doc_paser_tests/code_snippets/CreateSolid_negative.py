# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.CreateSolid(
    "SolidName",               # 作成するソリッド要素名称（空文字可）
    ElementGroup_element                # 作成するソリッド要素を要素グループに入れる場合は要素グループを指定（空文字可）
    # Missing the last argument: MaterialName
)