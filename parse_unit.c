#include "parse_unit.h"

/*--------------------------------------------------------------*
 *                          STATIC                              *
 *--------------------------------------------------------------*/

static CursorData cursorData = { 0 };

static CursorKind cursorKinds[] =
{
    {CXCursor_StructDecl        , "_struct"},
    {CXCursor_EnumDecl          , "_enum"},
    {CXCursor_FieldDecl         , "_field"},
    {CXCursor_EnumConstantDecl  , "_enum_constant"},
    {CXCursor_FunctionDecl      , "_function"},
    {CXCursor_TypedefDecl       , "_typedef"}
};

static int find_cursor_kind(CXCursor cursor);
static CursorKind get_cursor_kind(CXCursor cursor);
static const char* get_cursor_type(CXCursor cursor);
static const char* get_cursor_name(CXCursor cursor);
static CursorLocation get_cursor_location(CXCursor cursor);
static void print_cursor_data();
static bool is_appropriate_kind(CXCursor cursor);
static bool is_from_main_file(CXCursor cursor);


/*--------------------------------------------------------------*
 *                          PUBLIC                              *
 *--------------------------------------------------------------*/

void generate_cursor_data(CXCursor cursor)
{
    // kind
    cursorData.kind = get_cursor_kind(cursor);
    
    // type
    cursorData.type = get_cursor_type(cursor);

    // name
    cursorData.name = get_cursor_name(cursor);

    // location
    cursorData.location = get_cursor_location(cursor);

}

enum CXChildVisitResult visitor_callback(CXCursor currentChild, CXCursor parent, CXClientData clientData)
{
    do
    {
        // cursor entities of the main unit
        if (!is_from_main_file(currentChild)) { break; }

        // cursor entities of an appropriate kind  
        if (!is_appropriate_kind(currentChild)) { break; }

        generate_cursor_data(currentChild);
        print_cursor_data();

    } while (0);

    
    return CXChildVisit_Recurse;
}


/*--------------------------------------------------------------*
 *                          STATIC                              *
 *--------------------------------------------------------------*/

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

void print_cursor_data()
{
    // kind, name, location 
    const char* format = "  %-18s %-24s %-30s %s:%u:%u \n";

    printf(format,
        cursorData.kind.string,
        cursorData.type, cursorData.name,
        cursorData.location.file, cursorData.location.line, cursorData.location.column
    );
}

bool is_appropriate_kind(CXCursor cursor)
{
    bool result = false;

    if (find_cursor_kind(cursor) != -1)
    {
        result = true;
    }

    return result;
}

bool is_from_main_file(CXCursor cursor)
{
    CXSourceLocation cursorLocation = clang_getCursorLocation(cursor);
    return clang_Location_isFromMainFile(cursorLocation);
}