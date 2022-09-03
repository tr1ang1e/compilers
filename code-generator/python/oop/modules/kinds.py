from clang.cindex import Cursor, CursorKind, TokenGroup


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

    # add types mapping rules:
    #   1 = user's types
    #   2 = otherwise would be implicitly replaced with warning
    #   3 = hiding typed backward compatibility (be aware of handlers for not incomplete types: currently they must be replaced by 'c_void_p')
}


ThisPointer = 'this'  # to use when structure has pointer to itself as it's field


class Kinds:

    # to add new kind management:
    #    1. if appropriate class already exists, update corresponding tuple: ( ..., CursorKind.<NEW_KIND>, ): ...
    #    2. if new class is required:
    #        - create: (CursorKind.<NEW_KIND>, ) : "NewKindClass"
    #        - create: class NewKindClass(CommonTypeData)
    cursorKinds = {
        (CursorKind.TYPEDEF_DECL, ):                                "Typedef",
        (CursorKind.MACRO_DEFINITION, ):                            "Macro",
        (CursorKind.ENUM_DECL, ):                                   "Enum",
        (CursorKind.UNION_DECL, CursorKind.STRUCT_DECL, ):          "StructUnion",
        (CursorKind.FUNCTION_DECL, ):                               "Function",
    }

    def __init__(self):
        self.types = dict()
        for kind, type_name in self.cursorKinds.items():
            for k in kind:
                self.types[k] = globals()[type_name]

    def get_instance(self, cursor, parser, writer):
        if cursor.kind in self.types.keys():
            return self.types[cursor.kind](cursor, parser, writer)
        return None


class CommonTypeData:
    def __init__(self, cursor, parser, writer):
        # keep full context for particular type
        self.cursor = cursor        # first time type was met
        self.parser = parser        # particular unit, necessary to handle location and tokens
        self.writer = writer        # output file which this type should be generated in
        self.name = None

    @property
    def location(self):
        return self.cursor.location.file.name

    def handle(self):
        raise NotImplementedError

    def generate(self, wrapper):
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

            # types to hide are mapped to 'c_void_p'
            elif ctype == 'c_void_p':
                pointers_count -= 1

            # 'char*' should be mapped to 'c_char_p'
            elif base_type == 'char' and pointers_count > 0:
                ctype = 'c_char_p'
                pointers_count -= 1

        # enum type without typedef at all (cannot be replaced with 'c_int' alias)
        elif base_type.find('enum ') != -1 and Enum.is_known(base_type):
            ctype = 'c_int'

        # structure type without typedef at all (the same replace would be done for structure declaration)
        elif (base_type.find('struct ') != -1 or base_type.find('union ') != -1) and StructUnion.is_known(base_type):
            ctype = base_type.replace('struct ', 'struct_').replace('union ', 'union_')

        # alias for known user's type (order is important: don't place before 2 previous 'elif')
        elif StructUnion.is_known(base_canonical_underlying) or Enum.is_known(base_canonical_underlying):
            ctype = base_type

        # alias for callback
        elif Typedef.is_known(base_type) and base_canonical_underlying.find('(') != -1:
            ctype = base_type

        # alias for type pointers
        elif Typedef.is_known(base_type) and base_canonical_underlying.find('*') != -1:
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
        result_type = input_type.replace('const ', '').replace(' const', '').replace('*const', '*')
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


class Typedef(CommonTypeData):
    _aliases = dict()
    _underlyings = dict()

    def __init__(self, cursor, parser, writer):
        super().__init__(cursor, parser, writer)
        self.name = None
        self.underlying = None

    def handle(self):
        self.name = self.cursor.type.spelling
        self.underlying = self.cursor.underlying_typedef_type.spelling
        self._update_typedefs(self.name, self.underlying)

    def generate(self, wrapper):
        alias = None
        underlying = None

        # struct: generate only handlers to avoid conflict with real declaration
        if (self.underlying.find("struct ") != -1 or self.underlying.find("union ") != -1) and self.underlying.find('*') != -1:
            alias = self.name
            base_type = self.get_ctype(self.get_base_type(self.underlying)[0])
            if StructUnion.is_incomplete(base_type):
                underlying = 'c_void_p'
            else:
                # TODO: generate in this file, but after structs
                underlying = self.get_ctype(self.underlying)

        # enum: replace with 'c_int' only one of several aliases
        elif self.underlying.find("enum ") != -1:
            canonical = self.get_type(self.name)
            if self.name == canonical:
                alias = self.name
                underlying = "c_int"

        # functions: handle function pointer typedef   # TODO
        elif self.underlying.find('(') != -1:
            types = self.underlying.replace('(*)', '').replace(' (', ', ').replace(')', '').split(', ')
            types = [self.get_ctype(curr) for curr in types if curr != '']
            alias = self.name
            underlying = "CFUNCTYPE(" + ", ".join(types) + ")"

        # built-in types: skip, all aliases are replaced to built-in types in Typedef.get_ctype()
        else:
            pass

        if alias is not None and underlying is not None:
            wrapper.write("{} = {} \n".format(alias, underlying))

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

    @classmethod
    def is_known(cls, alias):
        return alias in cls._aliases.keys()


class Macro(CommonTypeData):

    def __init__(self, cursor, parser, writer):
        super().__init__(cursor, parser, writer)
        self.value = None

    def handle(self):

        tokens = []
        for token in TokenGroup.get_tokens(self.parser.currentUnit, self.cursor.extent):
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

    def generate(self, wrapper):
        if self.value is not None:
            value = "c_int(" + self.value + ")" if self.value.isdigit() else self.value
            wrapper.write("{} = {} \n".format(self.name, value))


class Enum(CommonTypeData):
    _enums = list()

    def __init__(self, cursor, parser, writer):
        super().__init__(cursor, parser, writer)
        self.constants = dict()

    def handle(self):
        # keep all handled enums original names
        # necessary for correct get_ctype() working
        self.name = self.cursor.type.spelling
        self.__class__._enums.append(self.name)

        alias = Typedef.get_type(self.name)
        if alias is not None:
            self.name = alias

        for const in self.cursor.get_children():
            self.constants[const.displayname] = const.enum_value

    def generate(self, wrapper):
        wrapper.write("\n# {}\n".format(self.name))
        for name, value in self.constants.items():
            wrapper.write("{} = c_int({})\n".format(name, value))

    @classmethod
    def is_known(cls, input_type):
        return input_type in cls._enums


class StructUnion(CommonTypeData):
    _structs_unions = list()
    _incomplete = list()

    def __init__(self, cursor, parser, writer):
        super().__init__(cursor, parser, writer)
        self.fields = dict()

    def handle(self):

        # variables to deal with nested anonymous structures and unions
        anon_fields_counter = 0     # auto naming counter
        anon_type_name = None       # nested declaration is met twice: have to keep name without counter increasing
        is_anon_scope = False       # cover the case with 'struct' as an anonymous scope

        # know if current structure is anonymous
        if hasattr(self.cursor, "anon_type_name"):
            self.name = self.cursor.anon_type_name
            self.__class__._structs_unions.append(self.name)
        else:
            # keep all handled structures original names. [!] necessary for correct get_ctype() processing
            self.__class__._structs_unions.append(self.cursor.type.spelling)
            # get common name
            self.name = Typedef.get_type(self.cursor.type.spelling)
            self.name = self.name.replace("struct ", "struct_")  # if type doesn't have aliases
            self.name = self.name.replace("union ", "union_")  # if type doesn't have aliases

        for field in self.cursor.get_children():

            # check for nested declarations
            temp_type_name = self.name + "_anon_{}".format(anon_fields_counter)
            field_declaration = self.is_nested_declaration(field, temp_type_name)

            # nested declaration
            if field_declaration is not None:
                anon_type_name = temp_type_name

                # consider anonymous declaration as an anonymous scope anyway
                if field.is_anonymous():
                    if not is_anon_scope:
                        self.fields["_scope"] = (anon_type_name, 0)
                        is_anon_scope = True

                anon_fields_counter += 1
                if self.parser.register_cursor(field):
                    field_declaration.handle()
                    if field_declaration.name is not None:  # some instances should be skipped
                        self.writer.update_containers(field_declaration)

            # members (of both nested and usual declared types)
            else:
                if field.is_anonymous():
                    if is_anon_scope:
                        # if we are here, it means anonymous declaration is a named member (not an anonymous scope)
                        self.fields.pop("_scope", None)
                    field_type = anon_type_name
                else:
                    field_type = self.get_ctype(field.type.spelling)

                field_name = field.displayname
                field_width = field.get_bitfield_width() if field.is_bitfield() else 0

                # handle callbacks. Not necessary. The reason: callback is typedef kind ...
                # ... if skip this check, all of identical callbacks would be replaced with the same typedef
                if self.is_callback(field):
                    field_type = field.type.spelling  # the exact input name without getting ctype

                # handle pointer to structure itself: if field type is pointer to structure name or to alias ...
                if field_type.find("POINTER(" + self.name + ")") != -1:
                    field_type = field_type.replace("POINTER(" + self.name + ")", ThisPointer)

                # ... or if field type is 'handler' = alias to pointer to structure or alias
                elif self.is_handler(field.type.spelling):
                    field_type = field_type.replace(self.get_base_type(field.type.spelling)[0], ThisPointer)
                    field_type = field_type.replace('c_void_p', ThisPointer)

                self.fields[field_name] = (field_type, field_width)

        if not len(self.fields):
            self.__class__._incomplete.append(self.name)
        elif self.name in self.__class__._incomplete:
            self.__class__._incomplete.remove(self.name)

    def generate(self, wrapper):
        incomplete = "# incomplete type, pointers to type replaced with 'c_void_p'" if not len(self.fields) else ""
        wrapper.write("\n\nclass {}({}):  {}\n".format(self.name, "Structure" if self.cursor.kind == CursorKind.STRUCT_DECL else "Union", incomplete))
        wrapper.write("    _fields_ = [")

        for field_name, field_type_info in self.fields.items():
            field_type = field_type_info[0]
            field_width = ", {}".format(field_type_info[1]) if field_type_info[1] else ""
            wrapper.write("\n        (\"{}\", {}{}),".format(field_name, field_type, field_width))

        wrapper.write("\n    ]\n")

    @classmethod
    def is_known(cls, input_type):
        return input_type in cls._structs_unions

    @classmethod
    def is_incomplete(cls, input_type):
        return input_type in cls._incomplete

    def is_nested_declaration(self, cursor, name):
        if cursor.type.get_declaration().is_anonymous():
            cursor.anon_type_name = name
        field_declaration = Kinds().get_instance(cursor, self.parser, self.writer)
        return field_declaration

    def is_callback(self, cursor):
        return cursor.type.get_canonical().spelling.find('(*)') != -1

    def is_handler(self, type_spelling):
        field_base_type = self.get_base_type(type_spelling)[0]
        field_canonical_type = Typedef.get_canonical_underlying(field_base_type).replace('*', '').strip()
        struct_union_canonical_type = Typedef.get_canonical_underlying(self.name).\
            replace("struct_", "struct ").replace("union_", "union ").strip()
        return field_canonical_type == struct_union_canonical_type


class Function(CommonTypeData):

    def __init__(self, cursor, parser, writer):
        super().__init__(cursor, parser, writer)
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

    def generate(self, wrapper):
        tab = "            "
        wrapper.write(tab + "self.{} = lib.{}\n".format(self.name, self.name))
        wrapper.write(tab + "self.{}.restype = {}\n".format(self.name, self.type))

        wrapper.write(tab + "self.{}.argtypes = [".format(self.name))
        for arg in range(len(self.args) - 1):
            wrapper.write("{}, ".format(self.args[arg]))

        # would be written for the last arg of if the only one exists
        if len(self.args):
            wrapper.write("{}".format(self.args[len(self.args) - 1]))
        wrapper.write("]\n\n")

