from clang.cindex import CursorKind
from kind import Kind, Type
from context import Context


class Handler(Kind):
    handlers = {}

    def __init__(self):
        for kind, name in self.cursorKinds.items():
            self.handlers[kind] = getattr(Handler, "parse_" + name)

    def parse_structure(self):
        pass

    def parse_enum(self):
        pass

    def parse_macro(self):
        pass

    def parse_function(self):
        pass

    def parse_typedef(self):
        pass
