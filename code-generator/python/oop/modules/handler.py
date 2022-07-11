from clang.cindex import Cursor, CursorKind
from kind import Kind, Type
from context import Context


class Handler(Kind):
    handlers = None

    @classmethod
    def handle_cursor(cls, cursor: Cursor):
        if cls.handlers is None:
            cls.handlers = dict()
            for kind, name in cls.cursorKinds.items():
                cls.handlers[kind] = getattr(Handler, "parse_" + name)
        return cls.parse_kind(cursor)

    @classmethod
    def parse_kind(cls, cursor):
        type_data = Type(cursor)
        return cls.handlers[cursor.kind](cursor, type_data)

    @classmethod
    def parse_structure(cls, cursor, parsed_type):
        return parsed_type

    @classmethod
    def parse_enum(cls, cursor, parsed_type):
        return parsed_type

    @classmethod
    def parse_macro(cls, cursor, parsed_type):
        return parsed_type

    @classmethod
    def parse_function(cls, cursor, parsed_type):
        return parsed_type

    @classmethod
    def parse_typedef(cls, cursor, parsed_type):
        return parsed_type
