from clang.cindex import Cursor, CursorKind, TranslationUnit


# self.name = cursor.displayname
# self.srcType = cursor.type.spelling
# self.canonType = cursor.type.get_canonical().spelling
# self.aliasType = None


class Kinds:

    cursorKinds = {
        CursorKind.TYPEDEF_DECL:         "Typedef",
        CursorKind.MACRO_DEFINITION:     "Macro",
        CursorKind.ENUM_DECL:            "Enum",
        CursorKind.STRUCT_DECL:          "Struct",
        CursorKind.FUNCTION_DECL:        "Function",
    }


class CommonTypeData:
    def __init__(self, cursor, unit):
        self.cursor = cursor
        self.file = unit.spelling

    def handle(self):
        raise NotImplementedError

    def generate(self):
        raise NotImplementedError

    def manage_pointers(self):
        pass

    def manage_array(self):
        pass


class Typedef(CommonTypeData):
    _aliases = dict()
    _underlyings = dict()

    def __init__(self, cursor, unit):
        super().__init__(cursor, unit)
        self.alias = None
        self.underlying = None

    def handle(self):
        self.alias = self.cursor.type.spelling
        self.underlying = self.cursor.underlying_typedef_type.spelling
        self.__class__._update_typedefs(self.alias, self.underlying)

    def generate(self):
        pass

    @classmethod
    def _update_typedefs(cls, alias, underlying):
        cls._aliases[alias] = underlying
        if underlying in cls._underlyings.keys():
            cls._underlyings[underlying].append(alias)
        else:
            cls._underlyings[underlying] = [alias]


class Macro(CommonTypeData):

    def handle(self):
        pass

    def generate(self):
        pass


class Enum(CommonTypeData):

    def handle(self):
        pass

    def generate(self):
        pass


class Struct(CommonTypeData):

    def handle(self):
        pass

    def generate(self):
        pass


class Function(CommonTypeData):

    def handle(self):
        pass

    def generate(self):
        pass


class Type(Kinds):

    def __init__(self):
        self.types = dict()
        for kind, type_name in self.cursorKinds.items():
            self.types[kind] = globals()[type_name]

    def get_instance(self, cursor, unit):
        return self.types[cursor.kind](cursor, unit)
