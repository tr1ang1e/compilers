#ifndef PARSE_UNIT
#define PARSE_UNIT

/* Description of the most significant clang-c API entities
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

typedef struct ClientDataS
{
	CXTranslationUnit unit;
} ClientData;

typedef void (*cursorCallback)(CXCursor, CXClientData);

typedef struct CursorKindS
{
	enum CXCursorKind code;
	const char* string;			// clang-c doesn't provide API to get cursor kind string representation
	cursorCallback handler;
} CursorKind;

typedef struct CursorLocationS
{
	const char* file;
	unsigned line;
	unsigned column;
} CursorLocation;

typedef struct CursorTokensS
{
	CXToken* tokensArray;		// must be disposed after usage: clang_disposeTokens(...)
	unsigned tokensNumber;
} CursorTokens;

// main cursor data
typedef struct CursorDataS
{
	CXTranslationUnit unit;
	CursorKind kind;
	const char* type;
	const char* name;
	CursorLocation location;
	CursorTokens tokens;
} CursorData;


/*--------------------------------------------------------------*
 *                         FUNCTIONS                            *
 *--------------------------------------------------------------*/

CursorData generate_cursor_data(CXCursor cursor, CXTranslationUnit unit);
enum CXChildVisitResult visitor_callback(CXCursor currentCursor, CXCursor parent, CXClientData clientData);


#endif // PARSE_UNIT 