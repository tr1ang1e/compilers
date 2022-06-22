#include "parse_unit.h"

/*--------------------------------------------------------------*
 *               STATIC FUNCTIONS PROTOTYPES                    *
 *--------------------------------------------------------------*/

// callback functions
static void cursor_handler_struct(CXCursor cursor, CXClientData clangData);
static void cursor_handler_enum(CXCursor cursor, CXClientData clangData);
static void cursor_handler_field(CXCursor cursor, CXClientData clangData);
static void cursor_handler_enum_constant(CXCursor cursor, CXClientData clangData);
static void cursor_handler_function(CXCursor cursor, CXClientData clangData);
static void cursor_handler_typedef(CXCursor cursor, CXClientData clangData);
static void cursor_handler_macro(CXCursor cursor, CXClientData clangData);

// filter cursors
static bool is_from_given_file(CXCursor cursor);         // true if is from given file, false otherwise
static int find_cursor_kind(CXCursor cursor);            // cursorKinds[] index if success, -1 otherwise

// get cursor common information
static CursorKind get_cursor_kind(CXCursor cursor);
static const char* get_cursor_type(CXCursor cursor);
static const char* get_cursor_name(CXCursor cursor);
static CursorLocation get_cursor_location(CXCursor cursor);
static CursorTokens get_cursor_tokens(CXCursor cursor, CXTranslationUnit unit);

// utilities
static const char* get_token_string(CXToken token, CXTranslationUnit unit);
static void print_cursor_data(CursorData cursorData);


/*--------------------------------------------------------------*
 *                          STATIC                              *
 *--------------------------------------------------------------*/

static CursorKind cursorKinds[] =
{
    { CXCursor_StructDecl        , "decl_struct"         ,  cursor_handler_struct        },
    { CXCursor_EnumDecl          , "decl_enum"           ,  cursor_handler_enum          },
    { CXCursor_FieldDecl         , "decl_field"          ,  cursor_handler_field         },
    { CXCursor_EnumConstantDecl  , "decl_enum_constant"  ,  cursor_handler_enum_constant },
    { CXCursor_FunctionDecl      , "decl_function"       ,  cursor_handler_function      },
    { CXCursor_TypedefDecl       , "decl_typedef"        ,  cursor_handler_typedef       },
    { CXCursor_MacroDefinition   , "decl_macro"          ,  cursor_handler_macro         },
};


/*--------------------------------------------------------------*
 *                          DEBUG                               *
 *--------------------------------------------------------------*/

bool print_cursor_kind(CXCursor cursor)
{
    enum CXCursorKind cursorKindEnum = clang_getCursorKind(cursor);
    
    if (cursorKindEnum == CXCursor_MacroDefinition)
    {
        if (!clang_Cursor_isMacroFunctionLike(cursor))
        {
            CXString cursorKind = clang_getCursorKindSpelling(cursorKindEnum);
            const char* cursorKindString = clang_getCString(cursorKind);
            clang_disposeString(cursorKind);
            printf(" : %s", cursorKindString);

            return true;
        }
    }

    return false;
}

bool print_cursor_location(CXCursor cursor)
{
    CursorLocation location = get_cursor_location(cursor);
    printf(" : %s:%u:%u", location.file, location.line, location.column);
    
    return true;
}

bool print_cursor_name(CXCursor cursor)
{
    printf(" : %s", get_cursor_name(cursor));

    return true;
}

#define _TR_(x) printf(" :: %d \n", x)

/*--------------------------------------------------------------*
 *                          PUBLIC                              *
 *--------------------------------------------------------------*/

CursorData generate_cursor_data(CXCursor cursor, CXTranslationUnit unit)
{
    CursorData cursorData =
    {
        .unit = unit,
        .kind = get_cursor_kind(cursor),
        .type = get_cursor_type(cursor),
        .name = get_cursor_name(cursor),
        .location = get_cursor_location(cursor),
        .tokens = get_cursor_tokens(cursor, unit),
    };

    return cursorData;
}

enum CXChildVisitResult visitor_callback(CXCursor currentCursor, CXCursor parent, CXClientData clangData)
{
    CursorData cursorData = { 0 };

    if (is_from_given_file(currentCursor))    // cursor entities of only the given unit
    {    
        int index = find_cursor_kind(currentCursor);

        if (index != -1)
        {            
            // common data
            cursorData = generate_cursor_data(currentCursor, ((ClientData*)clangData)->unit);
            
            // cursor kind handler
            CursorKind cursorKind = cursorKinds[index];
            cursorKind.handler(currentCursor, clangData);

            // debug
            print_cursor_data(cursorData);
        }
    }

    // clean up
    // ...

    return CXChildVisit_Recurse;
}


/*--------------------------------------------------------------*
 *                          STATIC                              *
 *--------------------------------------------------------------*/

void cursor_handler_struct(CXCursor cursor, CXClientData clangData)
{
    
}

void cursor_handler_enum(CXCursor cursor, CXClientData clangData)
{

}

void cursor_handler_field(CXCursor cursor, CXClientData clangData)
{

}

void cursor_handler_enum_constant(CXCursor cursor, CXClientData clangData)
{

}

void cursor_handler_function(CXCursor cursor, CXClientData clangData)
{

}

void cursor_handler_typedef(CXCursor cursor, CXClientData clangData)
{

}

void cursor_handler_macro(CXCursor cursor, CXClientData clangData)
{

}

bool is_from_given_file(CXCursor cursor)
{
    CXSourceLocation cursorLocation = clang_getCursorLocation(cursor);
    return clang_Location_isFromMainFile(cursorLocation);
}

int find_cursor_kind(CXCursor cursor)
{
    int index = -1;

    enum CXCursorKind cursorKindEnum = clang_getCursorKind(cursor);
    size_t cursorKindsSize = sizeof(cursorKinds) / sizeof(CursorKind);

    for (size_t i = 0; i < cursorKindsSize; ++i)
    {
        if (cursorKindEnum == cursorKinds[i].code)
        {
            index = i;
            break;
        }
    }

    return index;
}

CursorKind get_cursor_kind(CXCursor cursor)
{
    CursorKind kind = { 0 };

    int result = find_cursor_kind(cursor);
    if (result != -1)
    {
        kind = cursorKinds[result];
    }

    return kind;
}

const char* get_cursor_type(CXCursor cursor)
{
    const char* type = NULL;

    CXType cursorType = clang_getCursorType(cursor);
    CXString cursorTypeString = clang_getTypeSpelling(cursorType);
    type = clang_getCString(cursorTypeString);
    clang_disposeString(cursorTypeString);

    return type;
}

const char* get_cursor_name(CXCursor cursor)
{
    const char* name = NULL;

    CXString cursorName = clang_getCursorDisplayName(cursor);
    name = clang_getCString(cursorName);
    clang_disposeString(cursorName);

    return name;
}

CursorLocation get_cursor_location(CXCursor cursor)
{
    CXSourceLocation sourceLocation = clang_getCursorLocation(cursor);

    CursorLocation cursorLocation = { 0 };
    CXFile file;

    clang_getFileLocation(sourceLocation, &file, &cursorLocation.line, &cursorLocation.column, NULL);

    CXString cursorFile = clang_getFileName(file);
    cursorLocation.file = clang_getCString(cursorFile);
    clang_disposeString(cursorFile);

    return cursorLocation;
}

CursorTokens get_cursor_tokens(CXCursor cursor, CXTranslationUnit unit)
{
    CursorTokens tokens = { 0 };
    
    // get cursor range and tokenize it
    CXSourceRange range = clang_getCursorExtent(cursor);
    clang_tokenize(unit, range, &tokens.tokensArray, &tokens.tokensNumber);

    return tokens;
}

const char* get_token_string(CXToken token, CXTranslationUnit unit)
{
    const char* tokenString = NULL;
    
    CXString tokenSpelling = clang_getTokenSpelling(unit, token);
    tokenString = clang_getCString(tokenSpelling);
    clang_disposeString(tokenSpelling);

    return tokenString;
}

void print_cursor_data(CursorData cursorData)
{
    // kind, name, location 
    printf("  %-20s %-24s %-30s %s:%u:%-10u     ",
        cursorData.kind.string,
        cursorData.type, cursorData.name,
        cursorData.location.file, cursorData.location.line, cursorData.location.column
    );

    // tokens
    for (unsigned token = 0; token < cursorData.tokens.tokensNumber; ++token)
    {
        printf("%s . ", get_token_string(cursorData.tokens.tokensArray[token], cursorData.unit));
    }
    printf("\n");
}