"""
Pytest configuration for code_parser tests.

Ensures that modules inside this directory (e.g., simple_utils, vector_search)
are importable without package prefix by adding this folder to sys.path on test startup.
"""
import os
import sys

try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
except Exception:
    pass


