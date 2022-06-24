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
static void cursor_handler_parameter(CXCursor cursor, CXClientData clangData);
static void cursor_handler_typedef(CXCursor cursor, CXClientData clangData);
static void cursor_handler_macro(CXCursor cursor, CXClientData clangData);

// get cursor common information
static CursorKind get_cursor_kind(CXCursor cursor);
static const char* get_cursor_type(CXCursor cursor);
static const char* get_cursor_name(CXCursor cursor);
static CursorLocation get_cursor_location(CXCursor cursor);
static CursorTokens get_cursor_tokens(CXCursor cursor, CXTranslationUnit unit);

// utilities
static bool is_from_given_file(CXCursor cursor);                                                    // true if is from given file, false otherwise
static int find_cursor_kind(CXCursor cursor, CursorKind* cursorKindsArray, size_t arraySize);       // index of given array if success, -1 otherwise
static CursorCategory get_cursor_category(CXCursor cursor);
static const char* get_token_string(CXToken token, CXTranslationUnit unit);
static int get_string_token(const char* source, char** destination, char separator);
static const char** get_parameters_types(CXCursor cursor);
static void print_cursor_data(CursorData cursorData);


/*--------------------------------------------------------------*
 *                        CONTAINERS                            *
 *--------------------------------------------------------------*/

ListNode* structures     = NULL;
ListNode* enums          = NULL;
ListNode* functions      = NULL;
ListNode* typedefs       = NULL;
ListNode* macros         = NULL;


/*--------------------------------------------------------------*
 *                          STATIC                              *
 *--------------------------------------------------------------*/

static CursorKind cursorParentKinds[] =
{
    { CXCursor_StructDecl        , "decl_struct"         ,  cursor_handler_struct        },
    { CXCursor_EnumDecl          , "decl_enum"           ,  cursor_handler_enum          },
    { CXCursor_TypedefDecl       , "decl_typedef"        ,  cursor_handler_typedef       },
    { CXCursor_MacroDefinition   , "decl_macro"          ,  cursor_handler_macro         },
};

static CursorKind cursorChildKinds[] =
{
    { CXCursor_FieldDecl         , "decl_field"          ,  cursor_handler_field         },
    { CXCursor_EnumConstantDecl  , "decl_enum_constant"  ,  cursor_handler_enum_constant },
    { CXCursor_FunctionDecl      , "decl_function"       ,  cursor_handler_function      },
 // { CXCursor_ParmDecl          , "decl_parameter"      ,  cursor_handler_parameter     },  // replaced with clang_Cursor_getArgument() in function handler
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
    // recursively find parents then handle them and their children  

    enum CXChildVisitResult visitResult = CXChildVisit_Recurse;    // default for parent kind and for kinds we dont't need 
    CursorData cursorData = { 0 };

    do
    {
        bool result = is_from_given_file(currentCursor);
        if (!result)
        {
            break;
        }

        CursorCategory category = get_cursor_category(currentCursor);
        if (category.category == CURSOR_UNKNOWN_E)
        {
            break;
        }

        // common data
        CXTranslationUnit unit = ((ClientData*)clangData)->unit;    // deserialize argument given by caller
        cursorData = generate_cursor_data(currentCursor, unit);

        // handle cursor with callback
        CXClientData data = (CXClientData)&cursorData;
        cursorData.kind.handler(currentCursor, data);

        switch (category.category)
        {
            case CURSOR_PARENT_E:
                break;

            case CURSOR_CHILD_E:
                visitResult = CXChildVisit_Continue;   // guarantees visiting only children without thier children
                break;

            default: break;
        }
        
        // debug
        // print_cursor_data(cursorData);

        // clean up
        // clang_disposeTokens(cursorData.unit, cursorData.tokens.tokensArray, cursorData.tokens.tokensNumber);

    } while (0);

    return visitResult;
}

void dispose_containers()
{

}

void print_lists()
{    
    printf("\n");
    
    // structures
    
    StructType* currentStruct = GET_NODE(structures, StructType, next);
    printf("  :: STRUCTS :: \n");
    
    printf(" %s \n", currentStruct->name);
    while (currentStruct->next.next)
    {
        currentStruct = GET_NODE(currentStruct->next.next, StructType, next);
        printf(" %s \n", currentStruct->name);
    }
    printf("\n");

    // enums

    EnumType* currentEnum = GET_NODE(enums, EnumType, next);
    printf(" :: ENUMS :: \n");

    printf(" %s \n", currentEnum->name);
    while (currentEnum->next.next)
    {
        currentEnum = GET_NODE(currentEnum->next.next, EnumType, next);
        printf(" %s \n", currentEnum->name);
    }
    printf("\n");

    // functions

    FunctionType* currentFunction = GET_NODE(functions, FunctionType, next);
    printf(" :: FUNCTIONS :: \n");

    printf(" %-10s", currentFunction->returnType);
    printf(" %-15s", currentFunction->name);
    int i = 0;
    const char* argType = currentFunction->argsTypes[i];
    while (argType)
    {
        printf(" %s  ", argType);
        ++i;
        argType = currentFunction->argsTypes[i];
    }
    printf("\n");

    while (currentFunction->next.next)
    {
        currentFunction = GET_NODE(currentFunction->next.next, FunctionType, next);
        printf(" %-10s", currentFunction->returnType);
        printf(" %-15s", currentFunction->name);

        int i = 0;
        const char* argType = currentFunction->argsTypes[i];
        while (argType)
        {
            printf(" %s  ", argType);
            ++i;
            argType = currentFunction->argsTypes[i];
        }
    }
    printf("\n\n");

    // typedefs

    TypedefType* currentTypedef = GET_NODE(typedefs, TypedefType, next);
    printf(" :: TYPEDEFS :: \n");

    printf(" %-10s", currentTypedef->alias);
    printf(" %s \n", currentTypedef->underlyingType);
    while (currentTypedef->next.next)
    {
        currentTypedef = GET_NODE(currentTypedef->next.next, TypedefType, next);
        printf(" %-10s", currentTypedef->alias);
        printf(" %s \n", currentTypedef->underlyingType);
    }
    printf("\n");

    // macros

    MacroType* currentMacro = GET_NODE(macros, MacroType, next);
    printf(" :: TYPEDEFS :: \n");

    printf(" %-10s", currentMacro->name);
    printf(" %s \n", currentMacro->value);
    while (currentMacro->next.next)
    {
        currentMacro = GET_NODE(currentMacro->next.next, MacroType, next);
        printf(" %-10s", currentMacro->name);
        printf(" %s \n", currentMacro->value);
    }
    printf("\n");
}

/*--------------------------------------------------------------*
 *                          STATIC                              *
 *--------------------------------------------------------------*/

/* 
 * fileds, enumConstants  >>  check last parent, if pointer to them not null, skip, otherwise add
 * parameters  >>  get last parent, add
 * 
 * */

void cursor_handler_struct(CXCursor cursor, CXClientData clangData)
{
    CursorData cursorData = *(CursorData*)clangData;        // data for new instance
    StructType* newInstance = NULL;                         // new instance
    ListNode* last = get_last_node(structures);             // node of the last instance
    
    // debug
    // print_cursor_data(cursorData);

    bool init = !last;                                                                          // create instance and place first
    bool link = last && strcmp((GET_NODE(last, StructType, next))->name, cursorData.name);      // create instance and place last
    
    if (init || link) 
    {
        // create new instance
        newInstance = (StructType*)malloc(sizeof(StructType));
        if (!newInstance)
        {
            return;
        }
        newInstance->next.next = NULL;
        
        newInstance->name = cursorData.name;
    }
    else 
    {
        // list is not empty but new instance is the same as the last. Do nothing
    }

    if (init)
    {
        structures = &newInstance->next;
    }
    else if (link)
    {
        last->next = &newInstance->next;
    }   
}

void cursor_handler_enum(CXCursor cursor, CXClientData clangData)
{
    CursorData cursorData = *(CursorData*)clangData;        // data for new instance
    EnumType* newInstance = NULL;                           // new instance
    ListNode* last = get_last_node(enums);                  // node of the last instance

    bool init = !last;                                                                        // create instance and place first
    bool link = last && strcmp((GET_NODE(last, EnumType, next))->name, cursorData.name);      // create instance and place last

    if (init || link)
    {
        // create new instance
        newInstance = (EnumType*)malloc(sizeof(EnumType));
        if (!newInstance)
        {
            return;
        }
        newInstance->next.next = NULL;
        
        newInstance->name = cursorData.name;
    }
    else
    {
        // list is not empty but new instance is the same as the last. Do nothing
    }

    if (init)
    {
        enums = &newInstance->next;
    }
    else if (link)
    {
        last->next = &newInstance->next;
    }
}

void cursor_handler_field(CXCursor cursor, CXClientData clangData)
{
    CursorData cursorData = *(CursorData*)clangData;


}

void cursor_handler_enum_constant(CXCursor cursor, CXClientData clangData)
{
    CursorData cursorData = *(CursorData*)clangData;

    // clang_getEnumConstantDeclValue()


}

void cursor_handler_function(CXCursor cursor, CXClientData clangData)
{
    CursorData cursorData = *(CursorData*)clangData;        // data for new instance
    FunctionType* newInstance = NULL;                       // new instance
    ListNode* last = get_last_node(functions);              // node of the last instance

    // debug
    print_cursor_data(cursorData);

    // create new instance
    newInstance = (FunctionType*)malloc(sizeof(FunctionType));
    if (!newInstance)
    {
        return;
    }
    newInstance->next.next = NULL;

    // function type and name information
    int index = 0;
    index = get_string_token(&cursorData.name[0], &newInstance->name, '(');
    index = get_string_token(&cursorData.type[0], &newInstance->returnType, '(');

    // handle function arguments
    newInstance->argsTypes = get_parameters_types(cursor);

    if (!last)
    {
        functions = &newInstance->next;
    }
    else
    {
        last->next = &newInstance->next;
    }
}

void cursor_handler_parameter(CXCursor cursor, CXClientData clangData)  //  not used due to excuding decl_parameter kind from handling
{
    CursorData cursorData = *(CursorData*)clangData;
}

void cursor_handler_typedef(CXCursor cursor, CXClientData clangData)
{
    CursorData cursorData = *(CursorData*)clangData;        // data for new instance
    TypedefType* newInstance = NULL;                        // new instance
    ListNode* last = get_last_node(typedefs);               // node of the last instance

    // debug
    // print_cursor_data(cursorData);

    // create new instance
    newInstance = (TypedefType*)malloc(sizeof(TypedefType));
    if (!newInstance)
    {
        return;
    }
    newInstance->next.next = NULL;
    newInstance->alias = cursorData.name;

    CXType underlyingType = clang_getTypedefDeclUnderlyingType(cursor);
    CXString underlyingTypeString = clang_getTypeSpelling(underlyingType);
    newInstance->underlyingType = clang_getCString(underlyingTypeString);
     
    if (!last)
    {
        typedefs = &newInstance->next;
    }
    else
    {
        last->next = &newInstance->next;
    }
}

void cursor_handler_macro(CXCursor cursor, CXClientData clangData)
{
    if (clang_Cursor_isMacroFunctionLike(cursor))
    {
        return;
    }
    
    CursorData cursorData = *(CursorData*)clangData;        // data for new instance
    MacroType* newInstance = NULL;                          // new instance
    ListNode* last = get_last_node(macros);                 // node of the last instance

    // debug
    // print_cursor_data(cursorData);

    // create new instance
    newInstance = (MacroType*)malloc(sizeof(MacroType));
    if (!newInstance)
    {
        return;
    }
    newInstance->next.next = NULL;
    newInstance->name = cursorData.name;

    CXString tokenSpelling = clang_getTokenSpelling(cursorData.unit, cursorData.tokens.tokensArray[1]);
    newInstance->value = clang_getCString(tokenSpelling);

    if (!last)
    {
        macros = &newInstance->next;
    }
    else
    {
        last->next = &newInstance->next;
    }
}

CursorKind get_cursor_kind(CXCursor cursor)
{
    CursorKind kind = { 0 };

    do
    {
        CursorCategory category = get_cursor_category(cursor);
        if (category.category == CURSOR_UNKNOWN_E)
        {
            break;
        }

        switch (category.category)
        {
            case CURSOR_PARENT_E:
                kind = cursorParentKinds[category.index];
                break;

            case CURSOR_CHILD_E:
                kind = cursorChildKinds[category.index];
                break;

            default: 
                break;
        }
       
    } while (0);

    return kind;
}

const char* get_cursor_type(CXCursor cursor)
{
    const char* type = NULL;

    CXType cursorType = clang_getCursorType(cursor);
    CXString cursorTypeString = clang_getTypeSpelling(cursorType);
    type = clang_getCString(cursorTypeString);
    // clang_disposeString(cursorTypeString);

    return type;
}

const char* get_cursor_name(CXCursor cursor)
{
    const char* name = NULL;

    CXString cursorName = clang_getCursorDisplayName(cursor);
    name = clang_getCString(cursorName);
    // clang_disposeString(cursorName);

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
    // clang_disposeString(cursorFile);

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

bool is_from_given_file(CXCursor cursor)
{
    CXSourceLocation cursorLocation = clang_getCursorLocation(cursor);
    return clang_Location_isFromMainFile(cursorLocation);
}

int find_cursor_kind(CXCursor cursor, CursorKind* cursorKindsArray, size_t arraySize)
{
    int index = -1;

    enum CXCursorKind cursorKindEnum = clang_getCursorKind(cursor);

    for (size_t i = 0; i < arraySize; ++i)
    {
        if (cursorKindEnum == cursorKindsArray[i].code)
        {
            index = i;
            break;
        }
    }

    return index;
}

CursorCategory get_cursor_category(CXCursor cursor)
{
    CursorCategory category =
    {
        .category = CURSOR_UNKNOWN_E,
        .index = -1
    };

    do
    {
        // handle cursor parent kinds
        category.index = find_cursor_kind(cursor, cursorParentKinds, ARRAY_SIZE(cursorParentKinds));
        if (category.index != -1)
        {
            category.category = CURSOR_PARENT_E;
            break;
        }

        // handle cursor child kinds
        category.index = find_cursor_kind(cursor, cursorChildKinds, ARRAY_SIZE(cursorChildKinds));
        if (category.index != -1)
        {
            category.category = CURSOR_CHILD_E;
            break;
        }

    } while (0);

    return category;
}

const char* get_token_string(CXToken token, CXTranslationUnit unit)
{
    const char* tokenString = NULL;
    
    CXString tokenSpelling = clang_getTokenSpelling(unit, token);
    tokenString = clang_getCString(tokenSpelling);
    // clang_disposeString(tokenSpelling);

    return tokenString;
}

int get_string_token(const char* source, char** destination, char separator)  // return -1 if end of string is achieved, separator index of separator
{   
    // get type length
    size_t index;
    for (index = 0; index < strlen(source); ++index)
    {
        if (source[index] == separator)
        {
            break;
        }
    }

    // create string
    char* temp = (char*)malloc(index + 1);    // length + '\0'
    if (temp)
    {
        strncpy(temp, source, index);
        temp[index] = '\0';
        *destination = temp;
    }

    // return
    if (index == strlen(source))
    {
        index = -1;
    }

    return index;
}

const char** get_parameters_types(CXCursor cursor)
{
    int argsNumber = clang_Cursor_getNumArguments(cursor);
    const char** types = (char**)calloc(sizeof(char**), argsNumber + 1);  // add NULL despite of explicit args number

    if (!types)
    {
        return NULL;
    }

    int i;
    for (i = 0; i < argsNumber; ++i)
    {
        CXCursor argument = clang_Cursor_getArgument(cursor, i);
        types[i] = get_cursor_type(argument);
    }
    types[i] = NULL;

    return types;
}

void print_cursor_data(CursorData cursorData)
{
    // kind, type, name 
    printf("  %-20s %-24s %-30s %s:%u:%-10u     ",
        cursorData.kind.string,
        cursorData.type, cursorData.name,
        cursorData.location.file, cursorData.location.line, cursorData.location.column
    );

    // tokens
    for (unsigned token = 0; token < cursorData.tokens.tokensNumber; ++token)
    {
        printf("%s ", get_token_string(cursorData.tokens.tokensArray[token], cursorData.unit));
    }
    printf("\n");
}
