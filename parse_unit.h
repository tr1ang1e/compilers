#ifndef PARSE_UNIT
#define PARSE_UNIT

/* Description of clang-c API entities
 *
 *  :: clang_<name> is clang functions
 *  :: CX<name> is clang types
 *
 * structs or pointers to structs
 *   CXCursor = represents any of AST nodes
 *   CXString = type to handle clang string
 *   CXTranslationUnit = represents parsed translation unit
 *
 * enums
 *   CXTranslationUnit_Flags = enum of options passed to clang_parseTranslationUnit()
 *   CXChildVisitResult = enum of how the traversal should proceed after visiting child of given cursor
 *   CXCursorKind = enum of cursor kind
 *
 * */
#include <clang-c/Index.h> 

#include <stdio.h>
#include <stdbool.h>
#include <string.h>


/*--------------------------------------------------------------*
 *                          DEFINES                             *
 *--------------------------------------------------------------*/


/*--------------------------------------------------------------*
 *                           ENUMS                              *
 *--------------------------------------------------------------*/


/*--------------------------------------------------------------*
 *                          STRUCTS                             *
 *--------------------------------------------------------------*/

typedef struct CursorLocationS
{
	const char* file;
	unsigned line;
	unsigned column;
} CursorLocation;

typedef struct CursorKindS
{
	enum CXCursorKind code;
	const char* string;
} CursorKind;

typedef struct CursorDataS
{
	CursorKind kind;
	const char* type;
	const char* name;
	CursorLocation location;
} CursorData;


/*--------------------------------------------------------------*
 *                         FUNCTIONS                            *
 *--------------------------------------------------------------*/

void generate_cursor_data(CXCursor cursor);
enum CXChildVisitResult visitor_callback(CXCursor currentChild, CXCursor parent, CXClientData clientData);


#endif // PARSE_UNIT 