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

    @staticmethod
    def get_ctype(input_type):
        base_type, pointers_count, array_sizes = CommonTypeData.get_base_type(input_type)
        base_type = Typedef.get_type(base_type)
        base_canonical_underlying = Typedef.get_canonical_underlying(base_type)

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
        elif base_type.find('enum ') != -1 and Enum.is_known(base_type):
            ctype = 'int'

        # structure type without typedef at all (the same replace would be done for structure declaration)
        elif base_type.find('struct ') != -1 and Struct.is_known(base_type):
            ctype = base_type.replace('struct ', 'struct_')

        # alias for known user's type (order is important: don't place before 2 previous 'elif')
        elif Struct.is_known(base_canonical_underlying) or Enum.is_known(base_canonical_underlying):
            ctype = base_type

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
    def get_type(cls, input_type):

        """
        returns:
          - base type if input_type is alias to base type or a base type itself
          - alias for users type (one alias even if several were used to typedef one underlying type)
          - input_type itself if it is user's type and if it hasn't any aliases
        """

        # built-in type is given
        if input_type in typesMapping.keys():
            return input_type

        else:
            underlying_type = cls.get_canonical_underlying(input_type)

            # alias for built-in type was given
            if underlying_type in typesMapping.keys():
                return underlying_type

            # alias for user type or user type which alias is available for was given
            if underlying_type in cls._underlyings.keys():
                return cls._underlyings[underlying_type][0]

            # possible only if input_type is user's and if it was never used in typedef statements
            return input_type

    @classmethod
    def get_canonical_underlying(cls, alias):
        if alias in cls._aliases.keys():
            return cls.get_canonical_underlying(cls._aliases[alias])
        else:
            return alias


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
    _enums = list()

    def __init__(self, cursor, unit):
        super().__init__(cursor, unit)
        self.constants = dict()

    def handle(self):
        self.name = self.cursor.type.spelling
        self.__class__._enums.append(self.name)
        alias = Typedef.get_type(self.name)
        if alias is not None:
            self.name = alias

        for const in self.cursor.get_children():
            self.constants[const.displayname] = const.enum_value

    def generate(self):
        pass

    @classmethod
    def is_known(cls, input_type):
        return input_type in cls._enums


# TODO: incomplete type handling
class Struct(CommonTypeData):
    _structs = list()

    def __init__(self, cursor, unit):
        super().__init__(cursor, unit)
        self.name = None
        self.fields = dict()

    def handle(self):
        self.name = self.get_ctype(self.cursor.type.spelling)
        self.__class__._structs.append(self.name)
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

    @classmethod
    def is_known(cls, input_type):
        return input_type in cls._structs


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
