# Consolidated test cases for the CreateSolid function
from ..test_dsl import FunctionSpec, Param

# A list of test cases that the test runner will execute for this function.
test_cases = [
    {
        "test_name": "Positive case: Correct specification",
        "test_type": "positive",
        "spec": FunctionSpec(
            name="CreateSolid",
            description="空のソリッド要素を作成する。返り値:作成されたソリッドの要素ID",
            params=[
                Param(name="SolidName", position=0, type="文字列", description="作成するソリッド要素名称（空文字可）"),
                Param(name="ElementGroup", position=1, type="要素グループ", description="作成するソリッド要素を要素グループに入れる場合は要素グループを指定（空文字可）"),
                Param(name="MaterialName", position=2, type="材料", description="作成するソリッド要素の材質名称（空文字可）")
            ],
            return_type="要素",
            return_description="作成されたソリッドの要素ID"
        )
    },
    {
        "test_name": "Negative case: Incorrect parameter name",
        "test_type": "negative",
        "spec": FunctionSpec(
            name="CreateSolid",
            description="空のソリッド要素を作成する。返り値:作成されたソリッドの要素ID",
            params=[
                Param(name="WrongSolidName", position=0, type="文字列", description="作成するソリッド要素名称（空文字可）"), #<-- ERROR
                Param(name="ElementGroup", position=1, type="要素グループ", description="作成するソリッド要素を要素グループに入れる場合は要素グループを指定（空文字可）"),
                Param(name="MaterialName", position=2, type="材料", description="作成するソリッド要素の材質名称（空文字可）")
            ],
            return_type="要素",
            return_description="作成されたソリッドの要素ID"
        )
    }
]
