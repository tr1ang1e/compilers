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
#include <stdlib.h>

#include "list.h"


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
 *                        CONTAINERS                            *
 *--------------------------------------------------------------*/

typedef struct FiledTypeS
{
	char* name;		
	char* type;		
	
	ListNode next;
} FieldType;

typedef struct StructTypeS
{
	char* name;						
	ListNode* fields;

	ListNode next;
} StructType;

typedef struct EnumConstantTypeS
{
	char* name;		
	int value;
	
	ListNode next;
}EnumConstantType;

typedef struct EnumTypeS
{
	char* name;						
	ListNode* constants;

	ListNode next;
} EnumType;

typedef struct FunctionTypeS
{
	char* name;								
	char* returnType;						
	char** argsTypes;

	ListNode next;
} FunctionType;

typedef struct TypedefTypeS
{
	char* alias;						
	char* underlyingType;				

	ListNode next;
} TypedefType;

typedef struct MacroTypeS
{
	char* name;	
	char* value;				

	ListNode next;
} MacroType;


/*--------------------------------------------------------------*
 *                          STRUCTS                             *
 *--------------------------------------------------------------*/


struct CursorDataS;		// main cursor data - see definition below

typedef struct ClientDataS
{
	CXTranslationUnit unit;
} ClientData;

typedef struct CursorCategoryS
{
	CursorCategoryEnum category;
	int index;			// index in corresponding array
} CursorCategory;


typedef void (*cursorCallback)(CXCursor, struct CursorDataS);

typedef struct CursorKindS
{
	enum CXCursorKind code;		// simple enum constant, no need to dispose
	const char* string;			// clang-c doesn't provide API to get cursor kind string representation
	cursorCallback handler;		// pointer to specific callback function
} CursorKind;

typedef struct CursorLocationS
{
	CXString file;					
	unsigned line;
	unsigned column;
} CursorLocation;

typedef struct CursorTokensS
{
	CXToken* tokensArray;		
	unsigned tokensNumber;
} CursorTokens;

typedef struct CursorDataS
{
	CXTranslationUnit unit;		// parsed unit											! read-only, disposed in function which created unit
	CursorKind kind;			// exact kind											! nothing to dispose
	CXString type;				// represent type like is in location or canonical		! dispose after CursorData was used
	CXString name;				// represent cursor name								! dispose after CursorData was used
	CursorLocation location;	// location of entity cursor point to					! dispose after CursorData was used
	CursorTokens tokens;		// all of tokens										! dispose after CursorData was used
} CursorData;


/*--------------------------------------------------------------*
 *                         FUNCTIONS                            *
 *--------------------------------------------------------------*/

CursorData generate_cursor_data(CXCursor cursor, CXTranslationUnit unit);
enum CXChildVisitResult visitor_callback(CXCursor currentCursor, CXCursor parent, CXClientData clangData);
void dispose_containers();
void print_lists();


#endif // PARSE_UNIT 