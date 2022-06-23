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

#define ARRAY_SIZE(array)  (sizeof(array) / sizeof(array[0]))
#define _TR_(x) printf(" :: %d \n", x) // debug


/*--------------------------------------------------------------*
 *                           ENUMS                              *
 *--------------------------------------------------------------*/

typedef enum CursorCategoryE
{
	CURSOR_UNKNOWN_E = -1,
	CURSOR_PARENT_E,
	CURSOR_CHILD_E,
} CursorCategoryEnum;


/*--------------------------------------------------------------*
 *                          STRUCTS                             *
 *--------------------------------------------------------------*/

typedef struct ClientDataS
{
	CXTranslationUnit unit;
} ClientData;

typedef struct CursorCategoryS
{
	CursorCategoryEnum category;
	int index;					// index in corresponding array
} CursorCategory;

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
	CXTranslationUnit unit;		// parsed unit
	CursorKind kind;			// exact kind
	const char* type;			// type spelling as it is in the source code
	const char* name;			// name of entity cursor points to
	CursorLocation location;	// location of entity cursor point to
	CursorTokens tokens;		// all of tokens
} CursorData;


/*--------------------------------------------------------------*
 *                         FUNCTIONS                            *
 *--------------------------------------------------------------*/

CursorData generate_cursor_data(CXCursor cursor, CXTranslationUnit unit);
enum CXChildVisitResult visitor_callback(CXCursor currentCursor, CXCursor parent, CXClientData clangData);
enum CXChildVisitResult visitor_parent_callback(CXCursor currentCursor, CXCursor parent, CXClientData clangData);
enum CXChildVisitResult visitor_child_callback(CXCursor currentCursor, CXCursor parent, CXClientData clangData);


#endif // PARSE_UNIT 