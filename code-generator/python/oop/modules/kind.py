from clang.cindex import CursorKind


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
    pass
