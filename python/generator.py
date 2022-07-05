
# module = https://pypi.org/project/libclang/
# llvm source = https://github.com/llvm/llvm-project/tree/main/clang/bindings/python
# understanding AST = https://jonasdevlieghere.com/understanding-the-clang-ast/

# json info
# https://docs.python.org/3/library/json.html
# https://www.geeksforgeeks.org/read-write-and-parse-json-using-python/
# https://stackoverflow.com/questions/3768895/how-to-make-a-class-json-serializable


# +------ IMPLEM ------+
# TBD: implement OOP logic
# TBD: split into modules
# TBD: add custom exception  // https://habr.com/ru/company/piter/blog/537642/


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


# keep all handled kinds in convinient for generating code format
structures = {}				# "name"   :  {"name" : "type"}
enums = {}					# "name"   :  {"name" :  int  }
macros = {}					# "name"   :  "value"
functions = {}				# ("name", "type")  :  {"name" : "type"}
typedefs = {}				# "alias"  :  "underlying"

typedefsAliases = []	    # keep till the end for the case when typedef is declared in parsed and (!) generated file, but is used in another
typedefsReplaced = {}       # keep underlying types for the case when they are used despite of typedef aliases

# cursor kinds will be handled
cursorKinds = {

	# need to handle their children (see handlers)
	CursorKind.STRUCT_DECL			: "STRUCT_DECL",
	CursorKind.ENUM_DECL			: "ENUM_DECL",

	# handle without handling children
	CursorKind.MACRO_DEFINITION		: "MACRO_DEFINITION",
	CursorKind.FUNCTION_DECL		: "FUNCTION_DECL",
	CursorKind.TYPEDEF_DECL			: "TYPEDEF_DECL",
	
	# debug
	# CursorKind.ENUM_CONSTANT_DECL	: "ENUM_CONSTANT_DECL",
	# CursorKind.FIELD_DECL			: "FIELD_DECL",
}

typesMapping = {
	"void"                :   "c_void_p",
	"bool"                :   "c_bool",
	"char"                :   "c_char",
	"size_t"              :   "c_size_t",
	
	"unsigned char"       :   "c_uint8",
	"uint8_t"             :   "c_uint8",
	"unsigned short"      :   "c_uint16",
	"uint16_t"            :   "c_uint16",
	"unsigned int"        :   "c_uint32",
	"uint32_t"            :   "c_uint32",
    "unsigned long long"  :   "c_uint64",
	"uint64_t"            :   "c_uint64",
	
	"signed char"         :   "c_int8",
	"int8_t"              :   "c_int8",
	"short"               :   "c_int16",
	"signed short"        :   "c_int16",
	"int16_t"             :   "c_int16",
	"int"                 :   "c_int32",
	"signed int"          :   "c_int32",
	"int32_t"             :   "c_int32",
	"long long"           :   "c_int64",
	"signed long_long"    :   "c_int64",
	"int64_t"             :   "c_int64",
	
	# hide types implementation
	# 
	# 
}


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
	if(cursor.location.file):
		name = cursor.location.file.name
	line = cursor.location.line
	column = cursor.location.column
	print(f"   {name}:{line}:{column}", end=end)


def print_cursor_info(cursor):
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
	parser.add_argument('-s', '--settings', dest="settpath", type=str, default = './settings.json', help="path to settings file")
	args = parser.parse_args()
	return args


def get_settings(settpath):
	settingsFile = open(settpath, mode="r")
	settingsDict = json.load(settingsFile)
	settings = []	

	# files to parse
	settings.append(settingsDict["files"])			
	
	# arguments 
	compileArgs = []
	compileArgs.extend(settingsDict["preprocessor"])	

	includePaths = settingsDict["-Ipaths"]
	for path in range(len(includePaths)):
		includePaths[path] = add_prefix(includePaths[path], "-I")
	compileArgs.extend(includePaths)
	
	settings.append(compileArgs)

	# file to write to
	settings.append(settingsDict["output"])

	settingsFile.close()
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
	arrayBegin = string.find("[")
	array = True if (arrayBegin != -1) else False
	value = 0
	if array:
		arrayEnd = string.find("]")
		value = string[arrayBegin + 1 : arrayEnd : 1]
		string = string[:arrayBegin:].strip(' ')
	return value, string
		

def get_ctype(sourceType):
	temp = sourceType
	ctype = ""
	knownType = False

	# debug
	# print("  :: sourceType = {}".format(temp))
	# print(typedefsAliases)
	# print(typedefsReplaced.keys())

	# qualifiers are not allowed in python wrapper
	sourceType = sourceType.replace("const ", "")
	sourceType = sourceType.replace("volatile ", "")
	sourceType = sourceType.replace("restrict", "")

	# get and remove pointer and array info from type
	ptrDepth, sourceType = is_pointer(sourceType)
	arrSize, sourceType = is_array(sourceType)

	if sourceType.find('enum ') != -1:  # enum without typedef
		ctype = "c_int"
		knownType = True

	if sourceType in typedefsReplaced.keys():  # full enum type even if typedef was declared
		ctype = typedefsReplaced[sourceType]
		knownType = True

	if sourceType in structures.keys():  # structure typedef
		ctype = sourceType
		knownType = True

	if sourceType.replace("struct ", "struct_") in structures.keys():  # struct without typedef
		ctype = sourceType.replace("struct ", "struct_")
		knownType = True

	if sourceType.replace("struct ", "struct_") in typedefsReplaced.keys():  # full sruct type even if typedef was declared
		ctype = typedefsReplaced[sourceType.replace("struct ", "struct_")]
		knownType = True

	if sourceType in typesMapping.keys():  # built-in or hidden types
		ctype = typesMapping[sourceType]
		knownType = True

	if sourceType in typedefsAliases:  # typedef was declared in file parsed and (!) generated before 
		ctype = sourceType
		knownType = True

	if knownType:  # turn pointer and array info back
		while ptrDepth:
			if ctype == "c_char": ctype = "c_char_p"
			elif (sourceType == "void") and (ptrDepth == 1): pass # both 'void' and 'void *' are mapped to c_void_p
			else: ctype = "POINTER(" + ctype+ ")"
			ptrDepth -= 1
		if arrSize: ctype = ctype + " * " + arrSize

	else:  # type was declared in file parsed but (!) not generated before
		print("  Warning! Type '{}' is defined in file which was #include'd, parsed but were not generated. Replaced with 'c_void_p'".format(temp))
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
			openBrace = underlying.find('(')
			closeBrace = underlying.find(')')
			funType = get_ctype(underlying[:openBrace:].strip(' '))
			args = ', '.join([get_ctype(arg) for arg in underlying[closeBrace + 2 : -1 : 1].split(", ")])
			cFunc = "CFUNCTYPE(" + funType + ", " + args + ")"
			typedefs[alias] = cFunc

		else:
			underlying = get_ctype(underlying)
			typedefs[alias] = underlying


# ---------------------------------------------------------------------- #
#                                PARSERS                                 #
# ---------------------------------------------------------------------- #


def parse_field(cursor):
	name = cursor.displayname
	# canonType = cursor.type.get_canonical().spelling
	# return {name : canonType}
	sourceType = cursor.type.spelling
	return {name : sourceType}


def parse_structure(cursor):
	global structures
	name = "struct_" + cursor.displayname
	fields = {}
	for field in cursor.get_children():
		if is_appropriate_kind(field):
			print("  Error. parse_structure(), unexpected field kind, name = {}. Generation stopped".format(field.displayname))
			print("  Probably type definition is in header that couldn't be found. Check '-Ipaths' list in .json setting file")
			raise Exception()
		# debug
		# print_cursor_info(field)
		fields.update(parse_field(field))
	structures[name] = fields


def parse_const(cursor):
	name = cursor.displayname
	value = cursor.enum_value
	return {name : value}


def parse_enum(cursor):
	global enums
	name = "enum " + cursor.displayname
	children = {}
	for const in cursor.get_children():
		if not (const.kind == CursorKind.ENUM_CONSTANT_DECL):
			# raise ChildError("Unexpected enum constant kind")
			print("parse_enum(), unexpected const kind")
		# debug
		# print_cursor_info(const)
		children.update(parse_const(const))
	enums[name] = children


def parse_typedef(cursor):
	global typedefs
	alias = cursor.type.spelling
	underlying = cursor.underlying_typedef_type.spelling
	typedefs.update({alias : underlying})


def parse_macros(cursor):
	global macros
	tokens = []
	for token in TokenGroup.get_tokens(currentUnitHandler, cursor.extent):
		tokens.append(token.spelling)
	if len(tokens) == 2:
		name = tokens[0]
		value = tokens[1]
		macros.update({name : value})
	

def parse_argument(cursor):
	name = cursor.displayname
	#canonType = cursor.type.get_canonical().spelling
	# return {name : canonType}
	sourceType = cursor.type.spelling
	return {name : sourceType}


def parse_functions(cursor):
	global functions
	name = cursor.displayname.partition("(")[0]
	# canonType = cursor.type.get_canonical().get_result().spelling
	sourceType = cursor.type.get_result().spelling
	arguments = {}
	for arg in cursor.get_arguments():
		arguments.update(parse_argument(arg))
	# functions[(name, canonType)] = arguments
	functions[(name, sourceType)] = arguments


# ---------------------------------------------------------------------- #
#                               GENERATORS                               #
# ---------------------------------------------------------------------- #


def generate_header(wrapper):
	wrapper.write("#!/usr/bin/python3\n")
	wrapper.write("import platform\n")
	wrapper.write("from ctypes import *\n")


def generate_typedefs(wrapper):
	hanlde_typedefs() # use parsed data to effect other types
	global typedefs
	if len(typedefs):
		wrapper.write("\n# _typedefs_ = \n")
	for alias, underlying in typedefs.items():
		if underlying.find("CFUNCTYPE") != -1 or underlying.find("c_") != -1:
			wrapper.write("{} = {} \n".format(alias, underlying))
		else:
			wrapper.write("{} = \"{}\" \n".format(alias, underlying))

	typedefsAliases.extend(list(typedefs.keys()))
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
		wrapper.write("\nclass {}(Structure):\n".format(structName))
		wrapper.write("    _fields_ = [")

		fnames = list(fields.keys())
		ftypes = list(fields.values())
		fnumber = len(fnames) # convinient last field handling

		for i in range(fnumber):
			fieldType = get_ctype(ftypes[i])
			
			if fieldType.find(structName) != -1:
				fieldType = fieldType.replace("POINTER({})".format(structName), "c_void_p")
				wrapper.write("\n\t\t(\"{}\", {}), # pointer to this struct type".format(fnames[i], fieldType))		
			else:
				wrapper.write("\n\t\t(\"{}\", {}),".format(fnames[i], fieldType))
		
		wrapper.write("\n\t]\n")
	
	structures = {}


def generate_functions_class(wrapper):
	wrapper.write("\n")
	wrapper.write("# +----------------------------------------+\n")
	wrapper.write("# +    {:<35} +\n".format("Functions class"))
	wrapper.write("# +----------------------------------------+\n")
	wrapper.write("\nclass VlnsAPhySdk(object): \n\
	_instance = None \n\
	_initialized = False \n\
	\n\
	def __new__(cls, *args, **kwargs): \n\
		if VlnsAPhySdk._instance is None: \n\
			VlnsAPhySdk._instance = object.__new__(cls) \n\
		return VlnsAPhySdk._instance \n\
	\n\
	def __init__(self, libpath=None): \n\
		if VlnsAPhySdk._initialized: \n\
			pass \n\
		else: \n\
			if libpath is None: \n\
				is_linux = lambda: True if platform.system() == \"Linux\" else False \n\
				libpath = \"./libvalens_aphy.{0}\".format(\"so\" if is_linux() else \"dll\") \n\
			lib = cdll.LoadLibrary(libpath) \n")


def generate_functions(wrapper):
	global functions
	generate_functions_class(wrapper)
	for key, value in functions.items():
		wrapper.write("\n\t\t\tself.{} = lib.{}\n".format(key[0], key[0]))
		wrapper.write("\t\t\tself.{}.restype = {}\n".format(key[0], get_ctype(key[1])))
		wrapper.write("\t\t\tself.{}.argtypes = [".format(key[0]))
		args = list(value.values())

		for i in range(len(args) - 1):
			wrapper.write("{}, ".format(get_ctype(args[i])))
		if len(args):
			wrapper.write("{}".format(get_ctype(args[len(args)-1])))
		wrapper.write("]\n")
	
	functions = {}


# ---------------------------------------------------------------------- #
#                                  MAIN                                  #
# ---------------------------------------------------------------------- #


def visitor_function(parent):
	for cursor in parent.get_children():
		if is_from_given_file(cursor) and is_appropriate_kind(cursor):
			# debug
			# print_cursor_info(cursor)

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


def parse_file(index, currentFile, parseArgs, parseOpts):
	translationUnit = index.parse(currentFile, args=parseArgs, options=parseOpts)
	print(f"Processing unit: {translationUnit.spelling}")
			
	global currentUnitHandler
	global currentUnitSpelling
	currentUnitHandler = translationUnit
	currentUnitSpelling = translationUnit.spelling
			
	visitor_function(translationUnit.cursor)    # start with the root cursor


def generate_code(wrapper, currentFile):

	# info about file
	wrapper.write("\n")
	wrapper.write("# +----------------------------------------+\n")
	wrapper.write("# +    {:<35} +\n".format(currentFile))
	wrapper.write("# +----------------------------------------+\n")

	generate_typedefs(wrapper)
	generate_macros(wrapper)
	generate_enums(wrapper)
	generate_structs(wrapper)


def main():
	
	args = get_args() 

	# shared context for all files will be parsed
	parseFiles, parseArgs, outputFile = get_settings(args.settpath)
	parseOpts = TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD | TranslationUnit.PARSE_SKIP_FUNCTION_BODIES
	index = cl.Index.create()	
	
	# output wrapper file
	wrapper = open(outputFile, mode="w")
	generate_header(wrapper)

	# try:	

	for currentFile in parseFiles:
		parse_file(index, currentFile, parseArgs, parseOpts)
		generate_code(wrapper, currentFile)	
	# debug
	# print_containers()

	# except Exception as exception:
		# print(exception)

	# put all functions together
	generate_functions(wrapper)
	wrapper.close()


if __name__ == "__main__":
	main()
