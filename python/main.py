# module = https://pypi.org/project/libclang/
# llvm source = https://github.com/llvm/llvm-project/tree/main/clang/bindings/python


# TBD: try: for ... = status of sourceFile local variable
# TBD: if variable inside 'if' might it ebe used after
# TBD: how to do function static

# TBD: is function like macro
# TBD: get function parameters

# 


import clang.cindex as cl
from clang.cindex import TranslationUnit
from clang.cindex import CursorKind


# ---------------------------------------------------------------------- #
#                                GLOBAL                                  #
# ---------------------------------------------------------------------- #


# handle current unit to find out if current cursor is from correct file
currentUnit = 0


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
	"-U_WIN32"		   # undex _WIN32
	
	# paths to search headers, format is -I<path>
	"-I../examples/include",			
	"-I../examples/include/include2",	
]


# need to handle their children
cursorParentKinds = {
	CursorKind.STRUCT_DECL			: "STRUCT_DECL",
	CursorKind.ENUM_DECL			: "ENUM_DECL",
}	


# stop traversal depth increasing
cursorChildKinds = {
	CursorKind.FIELD_DECL			: "FIELD_DECL",
	CursorKind.ENUM_CONSTANT_DECL	: "ENUM_CONSTANT_DECL",
	CursorKind.MACRO_DEFINITION		: "MACRO_DEFINITION",
	CursorKind.FUNCTION_DECL		: "FUNCTION_DECL",
	CursorKind.TYPEDEF_DECL			: "TYPEDEF_DECL",
}


# ---------------------------------------------------------------------- #
#                               FUNCTIONS                                #
# ---------------------------------------------------------------------- #


def is_from_given_file(cursor):
	if cursor.location.file:
		if cursor.location.file.name == currentUnit:
			return True
	return False


def is_parent_kind(cursor):
	kind = cursor.kind
	return kind in cursorParentKinds


def is_child_kind(cursor):
	kind = cursor.kind
	return kind in cursorChildKinds


def is_appropriate_kind(cursor):
	return is_parent_kind(cursor) or is_child_kind(cursor)


# ---------------------------------------------------------------------- #
#                                 DEBUG                                  #
# ---------------------------------------------------------------------- #


def print_cursor_kind(cursor, end='\n'):
	if is_parent_kind(cursor):
		kind = cursorParentKinds[cursor.kind]
	if is_child_kind(cursor):
		kind = cursorChildKinds[cursor.kind]
	print("  {:<18}".format(kind), end=end)


def print_cursor_name(cursor, end='\n'):
	name = cursor.displayname
	print("  {:<28}".format(name), end=end)


def print_cursor_location(cursor, end='\n'):
	name = cursor.location.file.name
	line = cursor.location.line
	column = cursor.location.column
	print(f"   {name}:{line}:{column}", end=end)


def print_cursor_info(cursor):
	print_cursor_kind(cursor, "")
	print_cursor_name(cursor, "")
	print_cursor_location(cursor)


# ---------------------------------------------------------------------- #
#                                VISITOR                                 #
# ---------------------------------------------------------------------- #


def visitor_function(parent):
	for cursor in parent.get_children():
		if is_from_given_file(cursor) and is_appropriate_kind(cursor):
			print_cursor_info(cursor)
			if is_parent_kind(cursor):
				visitor_function(cursor)













# ---------------------------------------------------------------------- #
#                                  MAIN                                  #
# ---------------------------------------------------------------------- #


def main():

	# debug
	#

	# create shared context for files will be parsed
	index = cl.Index.create()

	# necessary options to pass into the parser funciton = index.parse(...)
	opts = TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD | TranslationUnit.PARSE_SKIP_FUNCTION_BODIES

	# parse files
	try:
		for sourceFile in sourceFiles:
			translationUnit = index.parse(sourceFile, args=arguments, options=opts)
			
			global currentUnit
			currentUnit = translationUnit.spelling
			print(f"\n :: Translation unit: {currentUnit} \n")
			
			visitor_function(translationUnit.cursor)    # start with the root cursor
	
	except cl.TranslationUnitLoadError:
		print("Failed to parse translation unit:", sourceFile)
		exit()


if __name__ == "__main__":
	main()
