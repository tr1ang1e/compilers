from clang.cindex import Cursor, CursorKind


class Kind:

    # kinds would be parsed during AST traversal
    # when handle some of them, additional parsing is required
    cursorKinds = {
        CursorKind.STRUCT_DECL:          "structure",
        CursorKind.ENUM_DECL:            "enum",
        CursorKind.MACRO_DEFINITION:     "macro",
        CursorKind.FUNCTION_DECL:        "function",
        CursorKind.TYPEDEF_DECL:         "typedef",
    }


class Type:
    cursor: Cursor = None
    name: str = None
    srcType: str = None
    canonType: str = None

    def __init__(self, cursor: Cursor):
        self.cursor = cursor
        self.name = cursor.displayname
        self.srcType = cursor.type.spelling
        self.canonType = cursor.type.get_canonical().spelling
