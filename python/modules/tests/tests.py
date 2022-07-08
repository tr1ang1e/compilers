import sys
sys.path.append('..')

import pytest
from context import Context


def test_context_parse_args():
    context = Context(["--settings", "settings.json"])
    assert context._projectPath == "."
    assert context._parseFiles == ["header.h", "source.c"]
    assert context._outputFile == "test_wrapper.py"
    expected_clang_args = ["-D__linux__", "-U_WIN32", "-I./include"]
    for arg in expected_clang_args:
        assert arg in context._clangArgs

