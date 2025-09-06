# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.CreateLinearSweepParam(
    "extra_value"    # 引数が不要なのに追加
)