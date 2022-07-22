from clang.cindex import CursorKind, TokenGroup
from debug import print_cursor_info


typesMapping = {

    # built-in types

    "void":                     "c_void_p",
    "bool":                     "c_bool",
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
        self.unit = unit
        self.name = None

    def handle(self):
        raise NotImplementedError

    def generate(self):
        raise NotImplementedError

    # TODO: change typedefs handling (what if typedef is for standard type?)
    @staticmethod
    def get_ctype(input_type):
        base_type, pointers_count, array_sizes = CommonTypeData.get_base_type(input_type)
        ctype = Typedef.get_alias(base_type)
        if ctype is None:

            # explicit types mapping
            if base_type in typesMapping.keys():
                ctype = typesMapping[base_type]

                # both 'void' and 'void*' types mapped to 'c_void_p'
                if base_type == 'void' and pointers_count > 0:
                    pointers_count -= 1

                # 'char*' should be mapped to 'c_char_p'
                if base_type == 'char' and pointers_count > 0:
                    ctype = 'c_char_p'
                    pointers_count -= 1

            # enum type without typedef at all (cannot be replaced with 'c_int' alias)
            elif base_type.find('enum ') != -1:
                ctype = 'int'

            # structure type without typedef at all (the same replace would be done for structure declaration)
            elif base_type.find('struct ') != -1:
                ctype = base_type.replace('struct ', 'struct_')

            # type is from parsed but not generated file
            else:
                ctype = 'c_void_p'
                print("Warning! Type '{}' was not recognized and was replaced with 'c_void_p'. "
                      "If it was expected or replace was incorrect, put explicit mapping rule to the kinds.py module"
                      .format(base_type))

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
        return base_type.strip(' '), pointers_count, array_sizes

    @staticmethod
    def manage_qualifiers(input_type):
        result_type = input_type.replace('const ', '').replace(' const', '')
        result_type = result_type.replace('restrict', '')
        result_type = result_type.replace('volatile', '')
        return result_type.strip()

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


# TODO: function pointer typedefs
class Typedef(CommonTypeData):
    _aliases = dict()
    _underlyings = dict()

    def __init__(self, cursor, unit):
        super().__init__(cursor, unit)
        self.alias = None
        self.underlying = None

    def handle(self):
        self.alias = self.cursor.type.spelling
        self.underlying = self.cursor.underlying_typedef_type.spelling  # TODO: get_ctype() (to print enum names, functions typedef pointers and handlers)
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
        if input_type in cls._aliases.keys():
            input_type = cls._aliases[input_type]   # get underlying type to use the same typedef in all cases
        if input_type in cls._underlyings.keys():   # not 'elif': important if input_type is alias already
            return cls._underlyings[input_type][0]  # zero alias would be used if several are available
        else:
            return None


class Macro(CommonTypeData):

    def __init__(self, cursor, unit):
        super().__init__(cursor, unit)
        self.value = None

    def handle(self):
        tokens = []
        for token in TokenGroup.get_tokens(self.unit, self.cursor.extent):
            tokens.append(token.spelling)
        # MACRO 1 or MACRO "string"
        if len(tokens) == 2:
            self.name = tokens[0]
            self.value = tokens[1]
        # MACRO (1)
        elif len(tokens) == 4 and tokens[1] == '(' and tokens[2] != '...' and tokens[3] == ')':
            self.name = tokens[0]
            self.value = tokens[2]
        else:
            return
        self.value = 'c_int(' + self.value + ')' if self.value.isdigit() else self.value

    def generate(self):
        pass


class Enum(CommonTypeData):

    def __init__(self, cursor, unit):
        super().__init__(cursor, unit)
        self.constants = dict()

    def handle(self):
        self.name = self.cursor.type.spelling
        alias = Typedef.get_alias(self.name)
        if alias is not None:
            self.name = alias

        for const in self.cursor.get_children():
            self.constants[const.displayname] = const.enum_value

    def generate(self):
        pass


class Struct(CommonTypeData):

    def __init__(self, cursor, unit):
        super().__init__(cursor, unit)
        self.name = None
        self.fields = dict()

    def handle(self):
        self.name = self.get_ctype(self.cursor.type.spelling)
        for field in self.cursor.get_children():
            field_name = field.displayname
            field_type = field.type.spelling

            # handle pointer to structure itself
            field_base_type = self.get_base_type(field_type)[0]
            if field_base_type.replace('struct ', 'struct_') == self.name:
                field_type = field_type.replace(field_base_type, 'void')
            field_type = self.get_ctype(field_type)

            self.fields[field_name] = field_type

    def generate(self):
        pass


class Function(CommonTypeData):

    def __init__(self, cursor, unit):
        super().__init__(cursor, unit)
        self.type = None
        self.args = list()

    def handle(self):
        self.name = self.cursor.displayname.partition('(')[0]
        if self.name.startswith('ENUM') or self.name.startswith('SDK_') or self.name.endswith('ToString'):
            self.name = None
        else:
            self.type = self.get_ctype(self.cursor.type.get_result().spelling)
            for arg in self.cursor.get_arguments():
                self.args.append(self.get_ctype(arg.type.spelling))

    def generate(self):
        pass


class Type(Kinds):

    def __init__(self):
        self.types = dict()
        for kind, type_name in self.cursorKinds.items():
            self.types[kind] = globals()[type_name]

    def get_instance(self, cursor, unit):
        return self.types[cursor.kind](cursor, unit)
