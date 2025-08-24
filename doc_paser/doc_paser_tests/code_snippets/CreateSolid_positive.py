# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.CreateSolid(
    "SolidName",               # 作成するソリッド要素名称（空文字可）
    ElementGroup_element,               # 作成するソリッド要素を要素グループに入れる場合は要素グループを指定（空文字可）
    "STEEL"                # 作成するソリッド要素の材質名称（空文字可）
)