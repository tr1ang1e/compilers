# https://pytest-docs-ru.readthedocs.io/ru/latest/contents.html


import sys
sys.path.append('..')
sys.path.append('../modules')


import pytest
from generator import is_appropriate
from modules.parser import Parser
from modules.writer import Writer
from modules.kinds import Kinds, CommonTypeData, Type, Typedef, Enum, Struct
from clang.cindex import CursorKind


# +------------------------------------------------------+
# +     UTILITIES and VISITOR FUNCTIONS                  +
# +------------------------------------------------------+


def visitor_traverse_ast(parent, parser, container):
    for cursor in parent.get_children():
        if is_appropriate(cursor, parser.currentUnit.spelling, [CursorKind.MACRO_DEFINITION]):
            type_instance = Type().get_instance(cursor, parser.currentUnit)
            assert type_instance.__class__.__name__ == "Macro"
            type_instance.handle()
            container[type_instance.name] = type_instance.value
        visitor_traverse_ast(cursor, parser, container)


def visitor_typedef_parsing_iteration(parent, parser, container):
    for cursor in parent.get_children():
        if is_appropriate(cursor, parser.currentUnit.spelling, [CursorKind.TYPEDEF_DECL]):
            type_instance = Type().get_instance(cursor, parser.currentUnit)
            assert type_instance.__class__.__name__ == "Typedef"
            type_instance.handle()
            container.append((type_instance.name, type_instance.underlying))
        visitor_typedef_parsing_iteration(cursor, parser, container)


def visitor_handle_enums(parent, parser, container):
    for cursor in parent.get_children():
        if is_appropriate(cursor, parser.currentUnit.spelling, [CursorKind.ENUM_DECL]):
            type_instance = Type().get_instance(cursor, parser.currentUnit)
            assert type_instance.__class__.__name__ == "Enum"
            type_instance.handle()
            container.append((type_instance.name, type_instance.constants))
        visitor_typedef_parsing_iteration(cursor, parser, container)


def visitor_handle_functions(parent, parser, container):
    for cursor in parent.get_children():
        if is_appropriate(cursor, parser.currentUnit.spelling, [CursorKind.FUNCTION_DECL]):
            type_instance = Type().get_instance(cursor, parser.currentUnit)
            assert type_instance.__class__.__name__ == "Function"
            type_instance.handle()
            container.append((type_instance.name, type_instance.type, *type_instance.args))
        visitor_handle_functions(cursor, parser, container)


def visitor_handle_structures(parent, parser, container):
    for cursor in parent.get_children():
        if is_appropriate(cursor, parser.currentUnit.spelling, [CursorKind.STRUCT_DECL]):
            type_instance = Type().get_instance(cursor, parser.currentUnit)
            assert type_instance.__class__.__name__ == "Struct"
            type_instance.handle()
            container.append((type_instance.name, *type_instance.fields.items()))
        visitor_handle_structures(cursor, parser, container)


# +------------------------------------------------------+
# +     CANONICAL FUNCTIONS                              +
# +------------------------------------------------------+


def visitor_function(parent, parser, writer, kinds):
    for cursor in parent.get_children():
        if is_appropriate(cursor, parser.currentUnit.spelling, kinds):
            type_instance = Type().get_instance(cursor, parser.currentUnit)
            type_instance.handle()
            writer.update_containers(type_instance)
        visitor_function(cursor, parser, writer, kinds)


def traverse_ast(parser, writer, kinds):
    for translation_unit in parser.parse_next_file():
        visitor_function(translation_unit.cursor, parser, writer, kinds)


# +------------------------------------------------------+
# +     FIXTURES                                         +
# +------------------------------------------------------+


@pytest.fixture
def create_parser():
    parser = Parser(["--settings", "settings.json"])
    return parser


@pytest.fixture
def create_writer():
    return Writer()


@pytest.fixture
def parse_typedefs(create_parser):
    parser = create_parser
    container = []
    print()
    for translation_unit in parser.parse_next_file():
        visitor_typedef_parsing_iteration(translation_unit.cursor, parser, container)
    return parser


@pytest.fixture
def add_types_manually():
    Enum._enums.append("enum EnumWithoutTypedef_test")
    Enum._enums.append("enum EnumUnderlying_test")
    Struct._structs.append("struct S_test")
    Struct._structs.append("struct IncompleteStruct_test")
    Struct._structs.append("struct S_callback_test")


@pytest.fixture
def call_canonical():
    pass


# +------------------------------------------------------+
# +     TESTS                                            +
# +------------------------------------------------------+


def test_context_parse_args(create_parser):
    parser = create_parser
    assert parser._projectPath == "."
    assert parser._parseFiles == ["./samples/include/header.h", "./samples/source.c"]
    assert parser.outputFile == "generated.py"
    expected_clang_args = ["-D__linux__", "-U_WIN32", "-I./samples/include"]
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


def test_traverse_ast(create_parser):
    parser = create_parser
    container = {}
    for translation_unit in parser.parse_next_file():
        visitor_traverse_ast(translation_unit.cursor, parser, container)
    assert "SOURCE_DEFINE_test" in container.keys()
    assert "HEADER_DEFINE_test" in container.keys()
    assert "SKIP_DEFINE_test" not in container.keys()


def test_typedef_parsing_iteration(create_parser):
    parser = create_parser
    container = []
    for translation_unit in parser.parse_next_file():
        visitor_typedef_parsing_iteration(translation_unit.cursor, parser, container)
    assert ("Typedef_IncompleteStruct_test", "struct IncompleteStruct_test") in container
    assert ("u8_test", "uint8_t") in container
    assert ("bool_test", "bool") in container
    assert ("another_bool_test", "bool") in container
    assert ("EnumAlias_test", "enum EnumUnderlying_test") in container
    assert ('callback_test', 'int (int)') in container
    assert ('S_callback_test', 'struct S_callback_test') in container
    # assert len(Typedef._aliases) == ...           # aliases have unique names
    # assert len(Typedef._underlyings) == ...       # one type might have different aliases


def test_manage_qualifiers():
    assert CommonTypeData.manage_qualifiers("const int") == "int"
    assert CommonTypeData.manage_qualifiers("const volatile int") == "int"
    assert CommonTypeData.manage_qualifiers("const int restrict *") == "int  *"
    assert CommonTypeData.manage_qualifiers("const int* const") == "int*"


def test_manage_pointers():
    assert CommonTypeData.manage_pointers('int ') == ('int', 0)
    assert CommonTypeData.manage_pointers('int *') == ('int', 1)
    assert CommonTypeData.manage_pointers('int** ') == ('int', 2)


def test_manage_arrays():
    assert CommonTypeData.manage_arrays('int[1]') == ('int', [1], 0)
    assert CommonTypeData.manage_arrays('int[2][3]') == ('int', [2, 3], 0)
    assert CommonTypeData.manage_arrays('int[][4][5]') == ('int', [4, 5], 1)
    assert CommonTypeData.manage_arrays('int[]') == ('int', [], 1)


def test_get_base_type():
    assert CommonTypeData.get_base_type('int ') == ('int', 0, [])
    assert CommonTypeData.get_base_type('volatile const int*[][1] ') == ('int', 2, [1])
    assert CommonTypeData.get_base_type('int* const') == ('int', 1, [])
    assert CommonTypeData.get_base_type('const int* [1][2] ') == ('int', 1, [1, 2])
    assert CommonTypeData.get_base_type('const int[3][2] ') == ('int', 0, [3, 2])
    assert CommonTypeData.get_base_type('volatile const int* restrict * const[][1][2] ') == ('int', 3, [1, 2])


def test_get_ctype():
    print()
    assert CommonTypeData.get_ctype('uint8_t') == 'c_uint8'
    assert CommonTypeData.get_ctype('void') == 'c_void_p'
    assert CommonTypeData.get_ctype('void*') == 'c_void_p'
    assert CommonTypeData.get_ctype('void**') == 'POINTER(c_void_p)'
    assert CommonTypeData.get_ctype('char*') == 'c_char_p'
    assert CommonTypeData.get_ctype('char**') == 'POINTER(c_char_p)'
    assert CommonTypeData.get_ctype('const int* [4][4]') == 'POINTER(c_int32) * 4 * 4'
    assert CommonTypeData.get_ctype('unsigned int**') == 'POINTER(POINTER(c_uint32))'
    assert CommonTypeData.get_ctype('bool*[4]') == 'POINTER(c_bool) * 4'
    assert CommonTypeData.get_ctype('NonExistentType*') == 'POINTER(c_void_p)'  # plus warning message should appear


def test_handle_macros(create_parser):
    parser = create_parser
    container = {}
    for translation_unit in parser.parse_next_file():
        visitor_traverse_ast(translation_unit.cursor, parser, container)
    assert container["MACRO_INT1_test"] == "c_int(42)"
    assert container["MACRO_INT2_test"] == "c_int(123)"
    assert container["MACRO_STR_test"] == '"string"'
    assert "MACRO_EMPTY_test" not in container.keys()
    assert "MACRO_FUNC_test" not in container.keys()


def test_handle_enums(parse_typedefs):
    parser = parse_typedefs
    container = []
    print()
    for translation_unit in parser.parse_next_file():
        visitor_handle_enums(translation_unit.cursor, parser, container)
    assert ("EnumAlias_test", {"ZERO": 0, "ONE": 1}) in container
    assert ("enum EnumWithoutTypedef_test", {"NEGATIVE": -1, "MACRO": 42}) in container
    print(container)


def test_handle_functions(parse_typedefs, add_types_manually):
    parser = parse_typedefs
    container = []
    print()
    for translation_unit in parser.parse_next_file():
        visitor_handle_functions(translation_unit.cursor, parser, container)
    assert ("FunctionEmpty_test", "c_void_p") in container
    assert ("FunctionDefault_test", "c_int32", "POINTER(c_int32)", "POINTER(c_char_p)") in container
    assert ("FunctionAliases_test", "EnumAlias_test", "POINTER(POINTER(Typedef_IncompleteStruct_test))") in container
    assert ("FunctionUnknownEnum_test", "c_void_p", "POINTER(int)") in container  # plus warning message should appear
    assert ("FunctionUnknownStruct_test", "c_void_p", "POINTER(struct_S_test)") in container  # plus warning message


# TODO: add more cases
def test_handle_structures(parse_typedefs, add_types_manually):
    parser = parse_typedefs
    container = []
    print()
    for translation_unit in parser.parse_next_file():
        visitor_handle_structures(translation_unit.cursor, parser, container)
    print(container)
    assert ("Typedef_IncompleteStruct_test",) in container
    assert ('struct_S_test', ('array', 'c_int32 * 123'), ('c', 'c_char'), ('self', 'POINTER(c_void_p)')) in container
    assert ('S_callback_test', ('function', 'callback_test')) in container


# def test_update_writer(create_parser, create_writer):   # why doesn't work in this way?
def test_update_writer(create_parser, create_writer, add_types_manually):
    parser = create_parser
    writer = create_writer
    traverse_ast(parser, writer, [CursorKind.TYPEDEF_DECL])
    traverse_ast(parser, writer, [kind for kind in Kinds.cursorKinds.keys() if kind != CursorKind.TYPEDEF_DECL])
    print()
    container = []
    for kind, instances in writer.containers.items():
        for instance in instances:
            container.append((kind, instance.name))
    assert (CursorKind.TYPEDEF_DECL, 'u8_test') in container
    assert (CursorKind.MACRO_DEFINITION, 'HEADER_DEFINE_test') in container
    assert (CursorKind.ENUM_DECL, 'EnumAlias_test') in container
    assert (CursorKind.STRUCT_DECL, 'S_callback_test') in container
    assert (CursorKind.FUNCTION_DECL, 'FunctionEmpty_test') in container


# +------------------------------------------------------+
# +     DEBUG                                            +
# +------------------------------------------------------+


def visitor_debug(parent, parser):
    for cursor in parent.get_children():
        if is_appropriate(cursor, parser.currentUnit.spelling, [CursorKind.STRUCT_DECL]):
            type_instance = Type().get_instance(cursor, parser.currentUnit)
            type_instance.handle()
        visitor_debug(cursor, parser)


def test_debug(create_parser):
    parser = create_parser
    print()
    for translation_unit in parser.parse_next_file():
        visitor_debug(translation_unit.cursor, parser)
