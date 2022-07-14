# https://pytest-docs-ru.readthedocs.io/ru/latest/contents.html


import sys
sys.path.append('..')
sys.path.append('../modules')


import pytest
from generator import is_appropriate
from modules.parser import Parser
from modules.kinds import Type, Typedef
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


def visitor_traverse_ast(parent, parser, writer, container):
    for cursor in parent.get_children():
        if is_appropriate(cursor, parser.currentUnit.spelling, [CursorKind.MACRO_DEFINITION]):
            type_instance = Type().get_instance(cursor, parser.currentUnit)
            assert type_instance.__class__.__name__ == "Macro"
            container.append(type_instance.cursor.displayname)
        visitor_traverse_ast(cursor, parser, None, container)


def test_traverse_ast(create_parser):
    parser = create_parser
    container = []
    for translation_unit in parser.parse_next_file():
        visitor_traverse_ast(translation_unit.cursor, parser, None, container)
    assert "SOURCE_DEFINE_test" in container
    assert "HEADER_DEFINE_test" in container
    assert "SKIP_DEFINE_test" not in container


def visitor_typedef_parsing_iteration(parent, parser, writer, container):
    for cursor in parent.get_children():
        if is_appropriate(cursor, parser.currentUnit.spelling, [CursorKind.TYPEDEF_DECL]):
            type_instance = Type().get_instance(cursor, parser.currentUnit)
            assert type_instance.__class__.__name__ == "Typedef"
            type_instance.handle()
            container.append((type_instance.alias, type_instance.underlying))
        visitor_typedef_parsing_iteration(cursor, parser, None, container)


def test_typedef_parsing_iteration(create_parser):
    parser = create_parser
    container = []
    for translation_unit in parser.parse_next_file():
        visitor_typedef_parsing_iteration(translation_unit.cursor, parser, None, container)
    assert ("Typedef_IncompleteStruct_test", "struct IncompleteStruct_test") in container
    assert ("u8_test", "uint8_t") in container
    assert ("bool_test", "bool") in container
    assert ("another_bool_test", "bool") in container
    assert len(Typedef._aliases) == 4           # aliases have unique names
    assert len(Typedef._underlyings) == 3       # one type might have different aliases
