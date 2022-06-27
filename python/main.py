# module = https://pypi.org/project/libclang/
# llvm source = https://github.com/llvm/llvm-project/tree/main/clang/bindings/python


# TBD: try: for ... = status of sourceFile local variable
# TBD: 


import sys
import clang.cindex as cl
from clang.cindex import TranslationUnit


# debug
#


# ---------------------------------------------------------------------- #
#                                SETTINGS                                #
# ---------------------------------------------------------------------- #

currentUnit = 0
sourceFiles = [
	"../examples/unit.c", 
    "../examples/empty.c"
]

arguments = [
	"-I../examples/include",		# path to search headers
	"-D__linux__",					# define __linux__
	"-U_WIN32"						# undex _WIN32
]

opt = TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD | TranslationUnit.PARSE_SKIP_FUNCTION_BODIES


def is_from_given_file(cursor):
	cursorFile = cursor.location.file.name
	return cursorFile == currentUnit



def print_cursor_location():
	pass


def visitor_function(cursor):
	for child in cursor.get_children():
		if is_from_given_file(child):
			print(child.displayname)





def main():

	# create shared context for files will be parsed
	index = cl.Index.create()

	# parse files
	try:
		for sourceFile in sourceFiles:
			translationUnit = index.parse(sourceFile, args=arguments)#, options=opt)
			global currentUnit
			currentUnit = translationUnit.spelling
			print("Translation unit:", currentUnit)
			visitor_function(translationUnit.cursor)    # start with root cursor
	except cl.TranslationUnitLoadError:
		print("Failed to parse translation unit:", sourceFile)
		exit()



if __name__ == "__main__":
	main()