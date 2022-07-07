# llvm source = https://github.com/llvm/llvm-project/tree/main/clang/bindings/python
# understanding AST = https://jonasdevlieghere.com/understanding-the-clang-ast/

# json info
# https://docs.python.org/3/library/json.html
# https://www.geeksforgeeks.org/read-write-and-parse-json-using-python/
# https://stackoverflow.com/questions/3768895/how-to-make-a-class-json-serializable

# TODO: implement OOP logic
# TODO: split into modules
# TODO: exceptions
# TODO: autodetect source files order if both must be parsed and one is included by another
# TODO: logging (module 'logging')


import argparse
import json
import clang.cindex as cl
from clang.cindex import TranslationUnit
from clang.cindex import CursorKind
from clang.cindex import TokenGroup


# ---------------------------------------------------------------------- #
#                                GLOBAL                                  #
# ---------------------------------------------------------------------- #


# handle current unit to find out if current cursor is from correct file
currentUnitHandler = 0
currentUnitSpelling = ""

# keep all handled kinds in convenient for generating code format
structures = {}  # "name"   :  {"name" : "type"}
enums = {}  # "name"   :  {"name" :  int  }
macros = {}  # "name"   :  "value"
functions = {}  # ("name", "type")  :  {"name" : "type"}
typedefs = {}  # "alias"  :  "underlying"

typedefsAccum = {}  # keep typedefs are declared in parsed and (!) generated file, but is used in another
typedefsReplaced = {}  # keep underlying types for the case when they are used despite typedef aliases
typedefsAfter = {}  # keep typedefs which are pointers to complete usertype

# cursor kinds will be handled
cursorKinds = {

    # need to handle their children (see handlers)
    CursorKind.STRUCT_DECL:           "STRUCT_DECL",
    CursorKind.ENUM_DECL:             "ENUM_DECL",

    # handle without handling children
    CursorKind.MACRO_DEFINITION:     "MACRO_DEFINITION",
    CursorKind.FUNCTION_DECL:        "FUNCTION_DECL",
    CursorKind.TYPEDEF_DECL:         "TYPEDEF_DECL",

    # debug
    # CursorKind.ENUM_CONSTANT_DECL	: "ENUM_CONSTANT_DECL",
    # CursorKind.FIELD_DECL			: "FIELD_DECL",
}

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

    "HostCmdEnum":              "c_int",
    "union NotificationId":     "c_uint32",
    "MUTEX_TYPE":               "c_int32",
    "CONDITION_TYPE":           "c_int32",
    "THREAD_TYPE":              "c_void_p",

    # otherwise would be implicitly replaced with warning

    "AppEventMsg":              "c_void_p",
    "FwLogOutputStream":        "c_void_p",

    # hiding types backward compatibility

    "SpiAdapter":               "c_void_p",
    "I2cAdapter":               "c_void_p",
}

hideTypes = []


# ---------------------------------------------------------------------- #
#                                 DEBUG                                  #
# ---------------------------------------------------------------------- #


def print_cursor_kind(cursor, end='\n'):
    kind = cursorKinds[cursor.kind]
    print("  {:<18}".format(kind), end=end)


def print_cursor_name(cursor, end='\n'):
    name = cursor.displayname
    print("  {:<28}".format(name), end=end)


def print_cursor_location(cursor, end='\n'):
    name = "None"
    if cursor.location.file:
        name = cursor.location.file.name
    line = cursor.location.line
    column = cursor.location.column
    print(f"   {name}:{line}:{column}", end=end)


def print_cursor_info(cursor):
    if cursor.kind in cursorKinds.keys():
        print_cursor_kind(cursor, "")
        print_cursor_name(cursor, "")
        print_cursor_location(cursor)


def print_containers():
    # structures
    global structures
    print("\n +-------------------- STRUCTURES --------------------+ ")
    for name, fields in structures.items():
        print("\n    {:<0}".format(name))
        for fname, ftype in fields.items():
            print("       {:<24} {:<24}".format(ftype, fname))
    print()

    # enums
    global enums
    print("\n +---------------------- ENUMS ------------------------+ ")
    for name, constants in enums.items():
        print("\n    {:<0}".format(name))
        for cname, cvalue in constants.items():
            print("       {:<8} {}".format(cname, cvalue))
    print()

    # typedefs
    global typedefs
    print("\n +--------------------- TYPEDEFS ----------------------+ ")
    print()
    for alias, underlying in typedefs.items():
        print("    {:<14} {:<24}".format(alias, underlying))
    print()

    # macros
    global macros
    print("\n +---------------------- MACROS -----------------------+ ")
    print()
    for name, value in macros.items():
        print("    {:<14} {:<24}".format(name, value))
    print()

    # functions
    global functions
    print("\n +--------------------- FUNCTIONS ---------------------+ ")
    print()
    for [fname, ftype], arguments in functions.items():
        print("    _name_: {:<0}".format(fname))
        print("    _return_: {:<0}".format(ftype))
        print("    _arguments_: ")
        for aname, atype in arguments.items():
            print("       {:<16}   {:<16} ".format(atype, aname))
        print()

    # additional info
    print()


# ---------------------------------------------------------------------- #
#                               UTILITIES                                #
# ---------------------------------------------------------------------- #


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--settings', dest="settpath", type=str, default='./settings.json',
                        help="path to settings file")
    args = parser.parse_args()
    return args


def get_settings(sett_path):
    settings_file = open(sett_path, mode="r")
    settings_dict = json.load(settings_file)

    # root directory, files to parse
    settings = [settings_dict["project"], settings_dict["files"]]

    # arguments
    compile_args = []
    compile_args.extend(settings_dict["preprocessor"])

    include_paths = settings_dict["-Ipaths"]
    for path in range(len(include_paths)):
        include_paths[path] = add_prefix(include_paths[path], "-I" + settings_dict["project"])
    compile_args.extend(include_paths)

    settings.append(compile_args)

    # file to write to
    settings.append(settings_dict["output"])

    settings_file.close()
    return settings


def is_from_given_file(cursor):
    if cursor.location.file:
        if cursor.location.file.name == currentUnitSpelling:
            return True
    return False


def is_appropriate_kind(cursor):
    kind = cursor.kind
    return kind in cursorKinds.keys()


def add_prefix(string, prefix):
    result = prefix + string
    return result


def is_pointer(string):
    depth = string.count('*')
    string = string.replace('*', '').strip(' ')
    return depth, string


def is_array(string):
    array_begin = string.find("[")
    array = True if (array_begin != -1) else False
    value = 0
    if array:
        array_end = string.find("]")
        value = string[array_begin + 1: array_end: 1]
        string = string[:array_begin:].strip(' ')
    return value, string


def get_ctype(source_type):
    temp = source_type
    ctype = ""
    known_type = False

    # qualifiers are not allowed in python wrapper
    source_type = source_type.replace("const ", "")
    source_type = source_type.replace("const", "")
    source_type = source_type.replace("volatile ", "")
    source_type = source_type.replace("restrict", "")

    # get and remove pointer and array info from type
    ptr_depth, source_type = is_pointer(source_type)
    arr_size, source_type = is_array(source_type)

    # built-in or hidden types
    if source_type in typesMapping.keys():
        ctype = typesMapping[source_type]
        known_type = True

    # enum without typedef
    elif source_type.find('enum ') != -1:
        ctype = "c_int"
        known_type = True

    # full enum type even if typedef was declared
    elif source_type in typedefsReplaced.keys():
        ctype = typedefsReplaced[source_type]
        known_type = True

    # structure typedef
    elif source_type in structures.keys():
        ctype = source_type
        known_type = True

    # struct without typedef
    elif source_type.replace("struct ", "struct_") in structures.keys():
        ctype = source_type.replace("struct ", "struct_")
        known_type = True

    # full sruct type even if typedef was declared
    elif source_type.replace("struct ", "struct_") in typedefsReplaced.keys():
        ctype = typedefsReplaced[source_type.replace("struct ", "struct_")]
        known_type = True

    # typedef was declared in file parsed and (!) generated before
    elif source_type in typedefsAccum.keys():
        ctype = source_type
        known_type = True

    # turn pointer and array info back
    if known_type:
        while ptr_depth:
            if ctype == "c_char":
                ctype = "c_char_p"
            elif (ctype == "c_void_p") and (ptr_depth == 1):
                pass  # both 'void' and 'void *' are mapped to c_void_p
            else:
                ctype = "POINTER(" + ctype + ")"
            ptr_depth -= 1
        if arr_size:
            ctype = ctype + " * " + arr_size
    # probably, type was declared in parsed but not generated file
    # if it is expected case, add this type to typesMapping list to avoid warning
    else:
        print(
            "  Warning! Type '{}' is defined in file which was #include'd, parsed but were not generated. "
            "Replaced with 'c_void_p'".format(temp))
        ctype = "c_void_p"

    return ctype


def hanlde_typedefs():
    global typedefs
    global structures
    global enums
    for alias, underlying in typedefs.items():

        if underlying in enums.keys():
            constants = enums[underlying]
            enums.pop(underlying)
            enums[alias] = constants
            typedefs[alias] = 'c_int # ' + underlying
            typedefsReplaced[underlying] = alias  # if full type naming will appear

        elif underlying.replace("struct ", "struct_") in structures.keys():
            key = underlying.replace("struct ", "struct_")
            fields = structures[key]
            structures.pop(key)
            structures[alias] = fields
            typedefsReplaced[key] = alias  # if full type naming will appear

        elif underlying.find('(') != -1:
            open_brace = underlying.find('(')
            close_brace = underlying.find(')')
            fun_type = get_ctype(underlying[:open_brace:].strip(' '))
            args_list = underlying[close_brace + 2: -1: 1].split(", ")
            args = (', ' + ', '.join([get_ctype(arg) for arg in args_list])) \
                if args_list[0] != "" else ""  # no args in function pointer
            c_func = "CFUNCTYPE(" + fun_type + args + ")"
            typedefs[alias] = c_func

        else:
            underlying = get_ctype(underlying)
            typedefs[alias] = underlying


# ---------------------------------------------------------------------- #
#                                PARSERS                                 #
# ---------------------------------------------------------------------- #


def parse_field(cursor):
    name = cursor.displayname
    source_type = cursor.type.spelling
    return {name: source_type}


def parse_structure(cursor):
    global structures
    name = "struct_" + cursor.displayname
    fields = {}
    for field in cursor.get_children():
        if is_appropriate_kind(field):
            print("  Error. parse_structure(), unexpected field kind, name = {}. "
                  "Generation stopped".format(field.displayname))
            print("  Probably type definition is in header that couldn't be found. "
                  "Check '-Ipaths' list in .json setting file")
            raise Exception()
        # debug
        # print_cursor_info(field)
        fields.update(parse_field(field))
    structures[name] = fields


def parse_const(cursor):
    name = cursor.displayname
    value = cursor.enum_value
    return {name: value}


def parse_enum(cursor):
    global enums
    name = "enum " + cursor.displayname
    children = {}
    for const in cursor.get_children():
        if not (const.kind == CursorKind.ENUM_CONSTANT_DECL):
            print("parse_enum(), unexpected const kind")    # TODO: exception
        children.update(parse_const(const))
    enums[name] = children


def parse_typedef(cursor):
    global typedefs
    alias = cursor.type.spelling
    underlying = cursor.underlying_typedef_type.spelling
    typedefs.update({alias: underlying})


def parse_macros(cursor):
    global macros
    tokens = []
    for token in TokenGroup.get_tokens(currentUnitHandler, cursor.extent):
        tokens.append(token.spelling)
    if len(tokens) == 2:
        name = tokens[0]
        value = tokens[1]
        macros.update({name: value})
    if len(tokens) == 4 and tokens[1] == '(' and tokens[3] == ')' and tokens[2] != "...":
        name = tokens[0]
        value = tokens[2]
        macros.update({name: value})


def parse_argument(cursor):
    name = cursor.displayname
    source_type = cursor.type.spelling
    return {name: source_type}


def parse_functions(cursor):
    global functions
    name = cursor.displayname.partition("(")[0]
    if name[:5:] != "ENUM_" and name[:4:] != "SDK_" and name[-1:-9:-1][::-1] != "ToString":
        source_type = cursor.type.get_result().spelling
        arguments = {}
        for arg in cursor.get_arguments():
            arguments.update(parse_argument(arg))
        functions[(name, source_type)] = arguments


# ---------------------------------------------------------------------- #
#                               GENERATORS                               #
# ---------------------------------------------------------------------- #


def generate_header(wrapper):
    wrapper.write("#!/usr/bin/python3\n")
    wrapper.write("import platform\n")
    wrapper.write("from ctypes import *\n")


def generate_typedefs_after(wrapper):
    global typedefsAfter
    if len(typedefsAfter):
        wrapper.write("\n# _typedefs_after_ = \n")
    for alias, underlying in typedefsAfter.items():
        wrapper.write("{} = {} \n".format(alias, underlying))
    typedefsAfter = {}


def generate_typedefs(wrapper):
    hanlde_typedefs()  # use parsed data to effect other types
    global typedefs
    global typedefsAccum
    global typedefsAfter
    if len(typedefs):
        wrapper.write("\n# _typedefs_ = \n")
    for alias, underlying in typedefs.items():
        if underlying[:16:] != "POINTER(POINTER(" and underlying[
                                                      :15:] == "POINTER(struct_":  # replace handlers with typedefs
            close_brace = underlying.find(')')
            handler_for = underlying[8:close_brace]
            if handler_for in typedefsReplaced.keys():
                handler_for = typedefsReplaced[handler_for]
            wrapper.write("{} = c_void_p  # handler for '{}'\n".format(alias, handler_for))
        elif underlying.find("CFUNCTYPE") != -1 or underlying.find("c_") != -1:
            wrapper.write("{} = {} \n".format(alias, underlying))
        elif underlying.find("POINTER") != -1:
            temp = underlying.replace("POINTER(", "").replace(")", "")
            typedefsAfter[alias] = underlying if temp not in typesMapping.keys() else typesMapping[temp]
        else:
            wrapper.write("{} = \"{}\" \n".format(alias, underlying))

    typedefsAccum = {**typedefsAccum, **typedefs}
    typedefs = {}


def generate_macros(wrapper):
    global macros
    if len(macros):
        wrapper.write("\n# _macros_ = \n")
    for name, value in macros.items():
        value = "c_int(" + value + ")" if value.isdigit() else value
        wrapper.write("{} = {} \n".format(name, value))

    macros = {}


def generate_enums(wrapper):
    global enums
    for name, consts in enums.items():
        wrapper.write("\n# {} \n".format(name))
        for cname, cvalue in consts.items():
            wrapper.write("{} = c_int({}) \n".format(cname, cvalue))

    enums = {}


def generate_structs(wrapper):
    global structures
    for structName, fields in structures.items():
        incomplete_type = "# incomplete type, pointers to type replaced with 'c_void_p'" if not len(fields) else ""
        wrapper.write("\nclass {}(Structure):  {}\n".format(structName, incomplete_type))
        wrapper.write("    _fields_ = [")

        fnames = list(fields.keys())
        ftypes = list(fields.values())

        for i in range(len(fnames)):
            field_type = get_ctype(ftypes[i])
            this_struct = False

            # pointer to intelf
            if field_type.find("POINTER(" + structName + ")") != -1:
                field_type.replace("POINTER(" + structName + ")", "c_void_p")
                this_struct = True

            # alias for pointer to itself, alias declared for struct without typedef or before struct typedef
            if field_type in typedefsAccum.keys():
                underlying = typedefsAccum[field_type]

                if underlying == "POINTER(" + structName + ")":
                    pass
                    field_type = "c_void_p"
                    this_struct = True

                else:
                    temp = underlying.replace("POINTER(", "").replace(")", "")
                    if temp in typedefsReplaced.keys():
                        if typedefsReplaced[temp] == structName:
                            # field_type = "c_void_p"
                            this_struct = True

            # alias for pointer itself, alias declared after struct typedef
            if field_type.find(structName) != -1:
                temp = field_type.replace(structName, "")
                open_brace = temp.find('(')
                if open_brace != -1 and temp[open_brace + 1] == ')':
                    field_type = field_type.replace("POINTER({})".format(structName), "c_void_p")
                    this_struct = True

            if this_struct:
                wrapper.write("\n\t\t(\"{}\", {}),  # pointer to this struct type".format(fnames[i], field_type))
            else:
                wrapper.write("\n\t\t(\"{}\", {}),".format(fnames[i], field_type))

        wrapper.write("\n\t]\n")

    structures = {}


def generate_functions_class_begin(wrapper):
    wrapper.write("\n")
    wrapper.write("# +----------------------------------------------------------------------+\n")
    wrapper.write("# +    {:<65} +\n".format("Functions class"))
    wrapper.write("# +----------------------------------------------------------------------+\n")
    wrapper.write("""
class instance(object):
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if instance._instance is None:
            instance._instance = object.__new__(cls)
        return instance._instance 
    
    def __init__(self, libpath=None): 
        if instance._initialized: 
            pass 
        else: 
            if libpath is None: 
                is_linux = lambda: True if platform.system() == "Linux" else False 
                libpath = "./library.{0}".format("so" if is_linux() else "dll") 
            lib = cdll.LoadLibrary(libpath)
""")


def generate_functions_class_end(wrapper):
    wrapper.write("""
            # init
            
            sdk_version = ...
            print('*****************************************************************')
            print('Py Wrapper: ...
            print('*****************************************************************')

            status = ... init() ...
            if not status:
                raise Exception("Failed to init '...' library") 

            instance._initialized = True

    @staticmethod 
    def get_version():
        return "..." 
""")


def generate_functions(wrapper):
    print(f"Processing all units functions")
    global functions
    generate_functions_class_begin(wrapper)
    for key, value in functions.items():

        wrapper.write("\n\t\t\tself.{} = lib.{}\n".format(key[0], key[0]))
        wrapper.write("\t\t\tself.{}.restype = {}\n".format(key[0], get_ctype(key[1])))
        wrapper.write("\t\t\tself.{}.argtypes = [".format(key[0]))
        args = list(value.values())

        for i in range(len(args) - 1):
            wrapper.write("{}, ".format(get_ctype(args[i])))
        if len(args):
            wrapper.write("{}".format(get_ctype(args[len(args) - 1])))
        wrapper.write("]\n")
    generate_functions_class_end(wrapper)
    functions = {}


# ---------------------------------------------------------------------- #
#                                  MAIN                                  #
# ---------------------------------------------------------------------- #


def visitor_function(parent):
    for cursor in parent.get_children():

        if is_from_given_file(cursor) and is_appropriate_kind(cursor):

            if cursor.kind == CursorKind.STRUCT_DECL:
                parse_structure(cursor)
            if cursor.kind == CursorKind.ENUM_DECL:
                parse_enum(cursor)
            if cursor.kind == CursorKind.TYPEDEF_DECL:
                parse_typedef(cursor)
            if cursor.kind == CursorKind.MACRO_DEFINITION:
                parse_macros(cursor)
            if cursor.kind == CursorKind.FUNCTION_DECL:
                parse_functions(cursor)

        # recursion
        visitor_function(cursor)


def parse_file(index, current_file, parse_args, parse_opts):
    translation_unit = index.parse(current_file, args=parse_args, options=parse_opts)
    print(f"Processing unit: {translation_unit.spelling}")

    global currentUnitHandler
    global currentUnitSpelling
    currentUnitHandler = translation_unit
    currentUnitSpelling = translation_unit.spelling

    visitor_function(translation_unit.cursor)  # start with the root cursor


def generate_code(wrapper, current_file):
    # info about file
    wrapper.write("\n")
    wrapper.write("# +----------------------------------------------------------------------+\n")
    wrapper.write("# +    {:<65} +\n".format(current_file))
    wrapper.write("# +----------------------------------------------------------------------+\n")

    generate_typedefs(wrapper)
    generate_macros(wrapper)
    generate_enums(wrapper)
    generate_structs(wrapper)
    generate_typedefs_after(wrapper)


def main():
    args = get_args()

    # shared context for all files will be parsed
    project_path, parse_files, parse_args, output_file = get_settings(args.settpath)
    parse_opts = TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD | TranslationUnit.PARSE_SKIP_FUNCTION_BODIES
    index = cl.Index.create()

    # output wrapper file
    wrapper = open(output_file, mode="w")
    generate_header(wrapper)

    for current_file in parse_files:      # TODO: exception
        parse_file(index, project_path + current_file, parse_args, parse_opts)
        generate_code(wrapper, current_file)

    # put all functions together
    generate_functions(wrapper)
    wrapper.close()


if __name__ == "__main__":
    main()
