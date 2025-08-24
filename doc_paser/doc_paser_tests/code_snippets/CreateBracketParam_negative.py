# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.CreateBracketParam(
    "extra_value",           # Extra argument that should cause failure
    "another_extra_value"    # Another extra argument
)