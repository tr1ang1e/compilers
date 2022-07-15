from clang.cindex import Cursor, CursorKind, TranslationUnit
from debug import print_cursor_info

# self.name = cursor.displayname
# self.srcType = cursor.type.spelling
# self.canonType = cursor.type.get_canonical().spelling
# self.aliasType = None

typesMapping = {

    # built-in types

    "void":                     "c_void_p",
    "_Bool":                    "c_bool",
    "char":                     "c_char",
    "size_t":                   "c_size_t",

    "unsigned char":            "c_uint8",
    "uint8_t":                  "c_uint8",
    "unsigned short":           "c_uint16",
    "uint16_t":                 "c_uint16",
    "unsigned int":             "c_uint32",
    "uint32_t":                 "c_uint32",
    "unsigned long long":       "c_uint64",
    "uint64_t":                 "c_uint64",

    "signed char":              "c_int8",
    "int8_t":                   "c_int8",
    "short":                    "c_int16",
    "signed short":             "c_int16",
    "int16_t":                  "c_int16",
    "int":                      "c_int32",
    "signed int":               "c_int32",
    "int32_t":                  "c_int32",
    "long long":                "c_int64",
    "signed long_long":         "c_int64",
    "int64_t":                  "c_int64",

    # user's types
    # otherwise would be implicitly replaced with warning
    # hiding types backward compatibility
}






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

    @staticmethod
    def get_ctype(input_type):
        base_type, pointers_count, array_sizes = CommonTypeData.get_base_type(input_type)
        ctype = Typedef.get_alias(base_type)
        if ctype is None:
            ctype = typesMapping[base_type]
        # apply pointers
        for i in range(pointers_count):
            ctype = "POINTER(" + ctype + ")"
        # apply arrays
        for size in array_sizes:
            ctype = ctype + " * {}".format(size)
        return ctype

    @staticmethod
    def get_base_type(input_type):
        base_type = CommonTypeData.manage_qualifiers(input_type)
        base_type, pointers_count = CommonTypeData.manage_pointers(base_type)
        base_type, array_sizes, pointer = CommonTypeData.manage_arrays(base_type)
        pointers_count += pointer
        return base_type, pointers_count, array_sizes

    @staticmethod
    def manage_qualifiers(input_type):
        result_type = input_type.replace('const ', '').replace(' const', '')
        result_type = result_type.replace('restrict', '')
        result_type = result_type.replace('volatile', '')
        return result_type.strip(' ')

    @staticmethod
    def manage_pointers(input_type):
        pointers_count = input_type.count('*')
        result_type = input_type.replace('*', '').strip(' ')
        return result_type, pointers_count

    @staticmethod
    def manage_arrays(input_type):
        array_sizes = list()
        pointer = 0
        result_type = input_type
        nesting = input_type.count('[')
        for i in range(nesting):
            open_brace = result_type.find('[')
            close_brace = result_type.find(']')
            if open_brace + 1 == close_brace:
                pointer = 1
            else:
                array_sizes.append(int(result_type[open_brace+1:close_brace:]))
            result_type = result_type[:open_brace] + result_type[close_brace+1:]
        return result_type, array_sizes, pointer


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

    @classmethod
    def get_alias(cls, input_type):
        if input_type in cls._underlyings.keys():
            return cls._underlyings[input_type][0]  # zero alias would be used if several are available
        else:
            return None


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
        # debug
        print("STRUCT")
        for field in self.cursor.get_children():
            print_cursor_info(field)

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
