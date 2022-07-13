# https://pytest-docs-ru.readthedocs.io/ru/latest/contents.html


import sys
sys.path.append('..')
sys.path.append('../modules')


import pytest
from generator import is_appropriate
from modules.parser import Parser
from modules.kinds import Type
from clang.cindex import CursorKind


@pytest.fixture
def create_parser():
    parser = Parser(["--settings", "settings.json"])
    return parser


def test_context_parse_args(create_parser):
    parser = create_parser
    assert parser._projectPath == "."
    assert parser._parseFiles == ["samples/include/header.h", "samples/source.c"]
    assert parser.outputFile == "generated.py"
    expected_clang_args = ["-D__linux__", "-U_WIN32", "-I./include"]
    for arg in expected_clang_args:
        assert arg in parser._clangArgs


def test_parser_parse_next(create_parser):
    parser = create_parser
    parsed_files = []
    print("\nProcessing log:")
    for translation_unit in parser.parse_next_file():
        file = translation_unit.spelling
        print("  {}".format(file))
        parsed_files.append(file)
    assert parsed_files == parser._parseFiles


def visitor(parent, parser, writer, container):
    for cursor in parent.get_children():
        if is_appropriate(cursor, parser.currentUnit.spelling, [CursorKind.MACRO_DEFINITION]):
            type_instance = Type().get_instance(cursor, parser.currentUnit)
            assert type_instance.__class__.__name__ == "Macro"
            container.append(type_instance.cursor.displayname)
        visitor(cursor, parser, None, container)


def test_traverse_ast(create_parser):
    parser = create_parser
    container = []
    for translation_unit in parser.parse_next_file():
        visitor(translation_unit.cursor, parser, None, container)
    assert "SOURCE_DEFINE_test" in container
    assert "HEADER_DEFINE_test" in container
    assert "SKIP_DEFINE_test" not in container
