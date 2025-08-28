"""
Automatically extend sys.path so that `code_parser` is importable as a top-level package
without relying on environment variables or test runner cwd.

This makes `from simple_utils import ...` and similar imports work from tests.
"""
import os
import sys

try:
    project_root = os.path.dirname(os.path.abspath(__file__))
    code_parser_path = os.path.join(project_root, "code_parser")
    if os.path.isdir(code_parser_path) and code_parser_path not in sys.path:
        sys.path.insert(0, code_parser_path)
except Exception:
    # Fail silently to avoid disrupting runtime even if path probing fails
    pass


