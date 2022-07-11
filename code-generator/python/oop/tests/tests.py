# https://pytest-docs-ru.readthedocs.io/ru/latest/contents.html


import sys
sys.path.append('..')
sys.path.append('../modules')


import pytest
from modules.context import Context
from modules.handler import Handler
from generator import is_appropriate


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
    print("\nProcessing log:")
    for translation_unit in context.parse_next_file():
        file = translation_unit.spelling
        print("  {}".format(file))
        parsed_files.append(file)
    assert parsed_files == context._parseFiles


def visitor(parent, unit_spelling, container):
    for cursor in parent.get_children():
        if is_appropriate(cursor, unit_spelling):
            type_data = Handler.handle_cursor(cursor)
            container.append(type_data.name)
        visitor(cursor, unit_spelling, container)


def test_type_data_common(create_context):
    context = create_context
    container = []
    for translation_unit in context.parse_next_file():
        visitor(translation_unit.cursor, translation_unit.spelling, container)
    assert "SOURCE_DEFINE_test" in container
    assert "HEADER_DEFINE_test" in container
    assert "SKIP_DEFINE_test" not in container
