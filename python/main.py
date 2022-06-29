# module = https://pypi.org/project/libclang/
# llvm source = https://github.com/llvm/llvm-project/tree/main/clang/bindings/python


# +------ THEORY ------+
# TBD: try: for ... = status of sourceFile local variable
# TBD: if variable inside 'if' might it ebe used after
# TBD: how to do function static


# +------ IMPLEM ------+
# TBD: is function like macro
# TBD: get function parameters
# TBD: add callback logic for cursor kinds handlers
# TBD: .json settings file
# TBD: how to parse types: canonical or original (typedefs)


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
typedefs = {}				# "alias"  :  "underlying"
macros = {}					# "name"   :  int
functions = {}				# ("name", "type")  :  {"name" : "type"}


# ---------------------------------------------------------------------- #
#                                SETTINGS                                #
# ---------------------------------------------------------------------- #


# cursor info only about this files are necessary
sourceFiles = [
	"../examples/unit.c", 
    "../examples/empty.c"
]


# argumets to pass into the parser funciton = index.parse(...)
arguments = [
	
	# must be because linux is tests target machine
	"-D__linux__",     # define __linux__
	"-U_WIN32",		   # undex _WIN32
	
	# paths to search headers, format is -I<path>
	"-I../examples/include",			
	"-I../examples/include/include2",	
]


# cursor kinds will be handled
cursorKinds = {

	# need to handle their children (see handlers)
	CursorKind.STRUCT_DECL			: "STRUCT_DECL",
	CursorKind.ENUM_DECL			: "ENUM_DECL",

	# handle without handling children
	CursorKind.TYPEDEF_DECL			: "TYPEDEF_DECL",
	CursorKind.MACRO_DEFINITION		: "MACRO_DEFINITION",
	CursorKind.FUNCTION_DECL		: "FUNCTION_DECL",
	
	# debug
	# CursorKind.ENUM_CONSTANT_DECL	: "ENUM_CONSTANT_DECL",
	# CursorKind.FIELD_DECL			: "FIELD_DECL",
}


# ---------------------------------------------------------------------- #
#                               FUNCTIONS                                #
# ---------------------------------------------------------------------- #


def is_from_given_file(cursor):
	if cursor.location.file:
		if cursor.location.file.name == currentUnitSpelling:
			return True
	return False


def is_appropriate_kind(cursor):
	kind = cursor.kind
	return kind in cursorKinds.keys()


def generate_field(cursor):
	name = cursor.displayname
	#canonType = cursor.type.get_canonical().spelling
	# return {name : canonType}
	sourceType = cursor.type.spelling
	return {name : sourceType}


def generate_structure(cursor):
	global structures
	name = cursor.displayname
	fields = {}
	for field in cursor.get_children():
		if is_appropriate_kind(field):
			raise ChildError("Unexpected field kind")
		# debug
		# print_cursor_info(field)
		fields.update(generate_field(field))
	structures[name] = fields


def generate_const(cursor):
	name = cursor.displayname
	value = cursor.enum_value
	return {name : value}


def generate_enum(cursor):
	global enums
	name = cursor.displayname
	children = {}
	for const in cursor.get_children():
		if not (const.kind == CursorKind.ENUM_CONSTANT_DECL):
			raise ChildError("Unexpected enum constant kind")
		# debug
		# print_cursor_info(const)
		children.update(generate_const(const))
	enums[name] = children


def generate_typedef(cursor):
	global typedefs
	alias = cursor.type.spelling
	underlying = cursor.underlying_typedef_type.spelling
	typedefs.update({alias : underlying})


def generate_macros(cursor):
	global macros
	tokens = []
	for token in TokenGroup.get_tokens(currentUnitHandler, cursor.extent):
		tokens.append(token.spelling)
	if len(tokens) == 2:
		name = tokens[0]
		value = tokens[1]
		macros.update({name : value})
	

def generate_argument(cursor):
	name = cursor.displayname
	#canonType = cursor.type.get_canonical().spelling
	# return {name : canonType}
	sourceType = cursor.type.spelling
	return {name : sourceType}


def generate_functions(cursor):
	global functions
	name = cursor.displayname.partition("(")[0]
	canonType = cursor.type.get_canonical().get_result().spelling
	# sourceType = cursor.type.get_result().spelling
	arguments = {}
	for arg in cursor.get_arguments():
		arguments.update(generate_argument(arg))
	functions[(name, canonType)] = arguments


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
		print("    name: {:<0}".format(fname))
		print("    return type: {:<0}".format(ftype))
		print("    arguments: ")
		for aname, atype in arguments.items():
			print("       {} {} ".format(atype, aname))
		print()
	
	# additional info
	print()

	
# ---------------------------------------------------------------------- #
#                                VISITOR                                 #
# ---------------------------------------------------------------------- #


def visitor_function(parent):
	for cursor in parent.get_children():
		if is_from_given_file(cursor) and is_appropriate_kind(cursor):
			# debug
			# print_cursor_info(cursor)

			if cursor.kind == CursorKind.STRUCT_DECL:
				generate_structure(cursor)
			if cursor.kind == CursorKind.ENUM_DECL:
				generate_enum(cursor)
			if cursor.kind == CursorKind.TYPEDEF_DECL:
				generate_typedef(cursor)
			if cursor.kind == CursorKind.MACRO_DEFINITION:
				generate_macros(cursor)
			if cursor.kind == CursorKind.FUNCTION_DECL:
				generate_functions(cursor)

			# recursion
			visitor_function(cursor)


# ---------------------------------------------------------------------- #
#                                  MAIN                                  #
# ---------------------------------------------------------------------- #


def main():

	# looks better
	print()

	# create shared context for files will be parsed
	index = cl.Index.create()

	# necessary options to pass into the parser funciton = index.parse(...)
	opts = TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD | TranslationUnit.PARSE_SKIP_FUNCTION_BODIES

	# parse files
	try:
		for sourceFile in sourceFiles:
			translationUnit = index.parse(sourceFile, args=arguments, options=opts)
			
			global currentUnitHandler
			global currentUnitSpelling
			currentUnitHandler = translationUnit
			currentUnitSpelling = translationUnit.spelling
			
			# debug
			print(f":: Processing unit = {currentUnitSpelling}")
			
			visitor_function(translationUnit.cursor)    # start with the root cursor
	
	except cl.TranslationUnitLoadError:
		print("Failed to parse translation unit:", sourceFile)
		exit()

	# debug
	print(":: Printing parsing results...")
	print_containers()



if __name__ == "__main__":
	main()
