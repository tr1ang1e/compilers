# https://pytest-docs-ru.readthedocs.io/ru/latest/contents.html


import sys
sys.path.append('..')


import pytest
from modules.context import Context


@pytest.fixture
def create_context():
    context = Context(["--settings", "settings.json"])
    return context


def test_context_parse_args(create_context):
    context = create_context
    assert context._projectPath == "."
    assert context._parseFiles == ["samples/include/header.h", "samples/source.c"]
    assert context.outputFile == "generated.py"
    expected_clang_args = ["-D__linux__", "-U_WIN32", "-I./include"]
    for arg in expected_clang_args:
        assert arg in context._clangArgs


def test_context_parse_next(create_context):
    context = create_context
    parsed_files = []
    print("\nProcessing:")
    for translation_unit in context.parse_next_file():
        file = translation_unit.spelling
        print("  {}".format(file))
        parsed_files.append(file)
    assert parsed_files == context._parseFiles
