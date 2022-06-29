#include "parse_unit.h"


/*--------------------------------------------------------------*
 *               STATIC FUNCTIONS PROTOTYPES                    *
 *--------------------------------------------------------------*/

// callback functions
static void cursor_handler_struct(CXCursor cursor, CursorData cursorData);
static void cursor_handler_enum(CXCursor cursor, CursorData cursorData);
static void cursor_handler_field(CXCursor cursor, CursorData cursorData);
static void cursor_handler_enum_constant(CXCursor cursor, CursorData cursorData);
static void cursor_handler_function(CXCursor cursor, CursorData cursorData);
static void cursor_handler_parameter(CXCursor cursor, CursorData cursorData);                       //  not used due to excluding decl_parameter kind from handling
static void cursor_handler_typedef(CXCursor cursor, CursorData cursorData);
static void cursor_handler_macro(CXCursor cursor, CursorData cursorData);

// get cursor common information
static CursorCategory get_cursor_category(CXCursor cursor);                                         // used separetely from CursorData structure
static CursorKind get_cursor_kind(CXCursor cursor);
static CXString get_cursor_type(CXCursor cursor, bool canonical);
static CXString get_cursor_name(CXCursor cursor);
static CursorLocation get_cursor_location(CXCursor cursor);
static CursorTokens get_cursor_tokens(CXCursor cursor, CXTranslationUnit unit);

// disposing resources
static void dispose_cursor_data(CursorData cursorData);
static void dispose_structures();
static void dispose_enums();
static void dispose_fields(ListNode** fields);
static void dispose_enum_constants(ListNode** enumConstants);
static void dispose_functions();
static void dispose_typedefs();
static void dispose_macros();

// utilities
static bool is_from_given_file(CXCursor cursor);                                                    // true if is from given file, false otherwise
static int find_cursor_kind(CXCursor cursor, CursorKind* cursorKindsArray, size_t arraySize);       // index of given array if success, -1 otherwise
static char* get_string(CXString clangString);
static int get_string_token(const char* source, char** destination, char separator);
static char** get_parameters_types(CXCursor cursor);
static void print_cursor_data(CursorData cursorData);


/*--------------------------------------------------------------*
 *                        CONTAINERS                            *
 *--------------------------------------------------------------*/

ListNode* structures  = NULL;      // dispose after list was used
ListNode* enums       = NULL;      // dispose after list was used
ListNode* functions   = NULL;      // dispose after list was used
ListNode* typedefs    = NULL;      // dispose after list was used
ListNode* macros      = NULL;      // dispose after list was used


/*--------------------------------------------------------------*
 *                          STATIC                              *
 *--------------------------------------------------------------*/

static CursorKind cursorParentKinds[] =
{
    { CXCursor_StructDecl        , "decl_struct"         ,  cursor_handler_struct        },
    { CXCursor_EnumDecl          , "decl_enum"           ,  cursor_handler_enum          },
    { CXCursor_MacroDefinition   , "decl_macro"          ,  cursor_handler_macro         },
};

static CursorKind cursorChildKinds[] =
{
    { CXCursor_FieldDecl         , "decl_field"          ,  cursor_handler_field         }, 
    { CXCursor_EnumConstantDecl  , "decl_enum_constant"  ,  cursor_handler_enum_constant }, 
    { CXCursor_FunctionDecl      , "decl_function"       ,  cursor_handler_function      },
//  { CXCursor_ParmDecl          , "decl_parameter"      ,  cursor_handler_parameter     },  // replaced with clang_Cursor_getArgument() in function handler
    { CXCursor_TypedefDecl       , "decl_typedef"        ,  cursor_handler_typedef       },  // migth me excluded because of clang_getCanonicalType()
};


/*--------------------------------------------------------------*
 *                          DEBUG                               *
 *--------------------------------------------------------------*/

void print_cursor_data(CursorData cursorData)
{
    // kind, type, name 
    char* type = get_string(cursorData.type);
    char* name = get_string(cursorData.name);
    char* file = get_string(cursorData.location.file);
    printf("  %-24s %-24s %-22s %s:%u:%-10u     ",
        cursorData.kind.string, 
        type, name,
        file, cursorData.location.line, cursorData.location.column
    );
    free(type);
    free(name);
    free(file);

    /* uncomment to see cursor tokens in debug output
        // tokens
        for (unsigned token = 0; token < cursorData.tokens.tokensNumber; ++token)
        {
            CXString tokenSpelling = clang_getTokenSpelling(cursorData.unit, cursorData.tokens.tokensArray[token]);
            printf(":%s ", clang_getCString(tokenSpelling));
            clang_disposeString(tokenSpelling);
        }
    */

    printf("\n");
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
        .type = get_cursor_type(cursor, true),
        .name = get_cursor_name(cursor),
        .location = get_cursor_location(cursor),
        .tokens = get_cursor_tokens(cursor, unit),
    };

    return cursorData;
}

enum CXChildVisitResult visitor_callback(CXCursor currentCursor, CXCursor parent, CXClientData clangData)
{
    // recursively find parents then handle them and their children  

    enum CXChildVisitResult visitResult = CXChildVisit_Recurse;     // default for parent kind and for kinds we dont't need 
    CursorData cursorData = { 0 };                                  // handle all necessary data in convinient form

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

        // common data = generate from cursor
        CXTranslationUnit unit = ((ClientData*)clangData)->unit;    // deserialize argument given by caller
        cursorData = generate_cursor_data(currentCursor, unit);

        // handle cursor = use common data and cursor itself
        cursorData.kind.handler(currentCursor, cursorData);

        switch (category.category)
        {
            case CURSOR_PARENT_E:
                break;

            case CURSOR_CHILD_E:
                visitResult = CXChildVisit_Continue;   // guarantees visiting only children without their children
                break;

            default: break;
        }
        
        // debug
        print_cursor_data(cursorData);

        // common data = dispose resources
        dispose_cursor_data(cursorData);

    } while (0);

    return visitResult;
}

void dispose_containers()
{
    dispose_structures();
    dispose_enums();
    dispose_functions();
    dispose_typedefs();
    dispose_macros();
}

void print_lists()
{    
    printf("\n");

    // ------------------------------ structures ------------------------------ //

    if (structures)
    {
        printf("  :: STRUCTS :: \n");
    
        // first structure
        StructType* currentStruct = GET_NODE(structures, StructType, next);
        printf(" %s \n", currentStruct->name);

        FieldType* currentField = GET_NODE(currentStruct->fields, FieldType, next);
        printf("    %-20s  %-20s \n", currentField-> type, currentField->name);
        while (currentField->next.next)
        {
            currentField = GET_NODE(currentField->next.next, FieldType, next);
            printf("    %-20s  %-20s \n", currentField->type, currentField->name);
        }


        // other structures
        while (currentStruct->next.next)
        {
            currentStruct = GET_NODE(currentStruct->next.next, StructType, next);
            printf(" %s \n", currentStruct->name);

            FieldType* currentField = GET_NODE(currentStruct->fields, FieldType, next);
            printf("    %-20s  %-20s \n", currentField->type, currentField->name);
            while (currentField->next.next)
            {
                currentField = GET_NODE(currentField->next.next, FieldType, next);
                printf("    %-20s  %-20s \n", currentField->type, currentField->name);
            }
        }
        printf("\n");
    }


    // -------------------------------- enums -------------------------------- //
    
    if (enums)
    {
        printf(" :: ENUMS :: \n");
    
        // first enum
        EnumType* currentEnum = GET_NODE(enums, EnumType, next);
        printf(" %s \n", currentEnum->name);
        EnumConstantType* currentEnumConstant = GET_NODE(currentEnum->constants, EnumConstantType, next);
        printf("    %s = %d \n", currentEnumConstant->name, currentEnumConstant->value);
        while (currentEnumConstant->next.next)
        {
            currentEnumConstant = GET_NODE(currentEnumConstant->next.next, EnumConstantType, next);
            printf("    %s = %d \n", currentEnumConstant->name, currentEnumConstant->value);
        }

        // other enums
        while (currentEnum->next.next)
        {
            currentEnum = GET_NODE(currentEnum->next.next, EnumType, next);
            printf(" %s \n", currentEnum->name);

            currentEnumConstant = GET_NODE(currentEnum->constants, EnumConstantType, next);
            printf("    %s = %d \n", currentEnumConstant->name, currentEnumConstant->value);
            while (currentEnumConstant->next.next)
            {
                currentEnumConstant = GET_NODE(currentEnumConstant->next.next, EnumConstantType, next);
                printf("    %s = %d \n", currentEnumConstant->name, currentEnumConstant->value);
            }

        }
        printf("\n");
    }



    // ------------------------------ functions ------------------------------ //
    
    if (functions)
    {
        printf(" :: FUNCTIONS :: \n");

        // first function
        FunctionType* currentFunction = GET_NODE(functions, FunctionType, next);
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

        // other functions
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
    }



    // ------------------------------- typedefs ------------------------------ //
    
    if (typedefs)
    {
        printf(" :: TYPEDEFS :: \n");

        // first typedef
        TypedefType* currentTypedef = GET_NODE(typedefs, TypedefType, next);
        printf(" %-10s", currentTypedef->alias);
        printf(" %s \n", currentTypedef->underlyingType);
    
        // other tyedefs
        while (currentTypedef->next.next)
        {
            currentTypedef = GET_NODE(currentTypedef->next.next, TypedefType, next);
            printf(" %-10s", currentTypedef->alias);
            printf(" %s \n", currentTypedef->underlyingType);
        }
        printf("\n");
    }



    // -------------------------------- macros ------------------------------- //
    if (macros)
    {
        printf(" :: MACROS :: \n");

        // first macro
        MacroType* currentMacro = GET_NODE(macros, MacroType, next);
        printf(" %-10s", currentMacro->name);
        printf(" %s \n", currentMacro->value);
    
        // other macros
        while (currentMacro->next.next)
        {
            currentMacro = GET_NODE(currentMacro->next.next, MacroType, next);
            printf(" %-10s", currentMacro->name);
            printf(" %s \n", currentMacro->value);
        }
        printf("\n");
    }
}


/*--------------------------------------------------------------*
 *                          STATIC                              *
 *--------------------------------------------------------------*/

 // callback functions

void cursor_handler_struct(CXCursor cursor, CursorData cursorData)
{
    StructType* newInstance = NULL;                         // new instance
    ListNode* last = get_last_node(structures);             // node of the last instance
    
    // debug
    // print_cursor_data(cursorData);

    bool init = !last;                                                                                      // create instance and place first
    bool link = last && strcmp((GET_NODE(last, StructType, next))->name, get_string(cursorData.name));      // create instance and place last
    
    if (init || link) 
    {
        // create new instance
        newInstance = (StructType*)malloc(sizeof(StructType));
        if (!newInstance)
        {
            return;
        }
        newInstance->next.next = NULL;
        newInstance->name = get_string(cursorData.name);
        newInstance->fields = NULL;    // necessary for handle fields
    }
    else 
    {
        // list is not empty but new instance is the same as the last. Do nothing
        // occurs when typedef and type declaration are combined. Might be fixed by 
        // returninig "_Continue" when handle typedef in visitor callback function
    }

    // insert
    if (init)
    {
        structures = &newInstance->next;
    }
    else if (link)
    {
        last->next = &newInstance->next;
    }   
}

void cursor_handler_enum(CXCursor cursor, CursorData cursorData)
{
    EnumType* newInstance = NULL;                           // new instance
    ListNode* last = get_last_node(enums);                  // node of the last instance

    bool init = !last;                                                                                    // create instance and place first
    bool link = last && strcmp((GET_NODE(last, EnumType, next))->name, get_string(cursorData.name));      // create instance and place last

    if (init || link)
    {
        // create new instance
        newInstance = (EnumType*)malloc(sizeof(EnumType));
        if (!newInstance)
        {
            return;
        }
        newInstance->next.next = NULL;
        newInstance->name = get_string(cursorData.name);
        newInstance->constants = NULL;    // necessary for handle constants
    }  
    else
    {
        // list is not empty but new instance is the same as the last. Do nothing
        // occurs when typedef and type declaration are combined. Might be fixed by 
        // returninig "_Continue" when handle typedef in visitor callback function
    }

    // insert
    if (init)
    {
        enums = &newInstance->next;
    }
    else if (link)
    {
        last->next = &newInstance->next;
    }
}

void cursor_handler_field(CXCursor cursor, CursorData cursorData)
{
    // enums container stored in corresponding enum node of enums list
    ListNode* structDeclaration = get_last_node(structures);
    StructType* structInstance = GET_NODE(structDeclaration, StructType, next);

    FieldType* newInstance = NULL;                                // new instance
    ListNode* last = get_last_node(structInstance->fields);       // node of the last instance

    // debug
    // print_cursor_data(cursorData);

    // create new instance
    newInstance = (FieldType*)malloc(sizeof(FieldType));
    if (!newInstance)
    {
        return;
    }
    newInstance->next.next = NULL;
    newInstance->name = get_string(cursorData.name);

    CXString type = get_cursor_type(cursor, true);
    newInstance->type = get_string(type);
    clang_disposeString(type);

    // insert
    if (!last)
    {
        structInstance->fields = &newInstance->next;
    }
    else
    {
        last->next = &newInstance->next;
    }
}

void cursor_handler_enum_constant(CXCursor cursor, CursorData cursorData)
{
    // enums container stored in corresponding enum node of enums list
    ListNode* enumDeclaration = get_last_node(enums);
    EnumType* enumInstance = GET_NODE(enumDeclaration, EnumType, next);
    
    EnumConstantType* newInstance = NULL;                         // new instance
    ListNode* last = get_last_node(enumInstance->constants);      // node of the last instance
    
    // debug
    // print_cursor_data(cursorData);
    
    // create new instance
    newInstance = (EnumConstantType*)malloc(sizeof(EnumConstantType));
    if (!newInstance)
    {
        return;
    }
    newInstance->next.next = NULL;
    newInstance->name = get_string(cursorData.name);
    newInstance->value = (int)clang_getEnumConstantDeclValue(cursor);

    // insert
    if (!last)
    {
        enumInstance->constants = &newInstance->next;
    }
    else
    {
        last->next = &newInstance->next;
    }
}

void cursor_handler_function(CXCursor cursor, CursorData cursorData)
{
    FunctionType* newInstance = NULL;                       // new instance
    ListNode* last = get_last_node(functions);              // node of the last instance

    // debug
    // print_cursor_data(cursorData);

    // create new instance
    newInstance = (FunctionType*)malloc(sizeof(FunctionType));
    if (!newInstance)
    {
        return;
    }
    newInstance->next.next = NULL;

    // function type 
    CXType cursorType = clang_getCursorType(cursor);
    CXType canonicalType = clang_getCanonicalType(cursorType);
    CXType resultType = clang_getResultType(canonicalType);
    CXString typeSpelling = clang_getTypeSpelling(resultType);
    newInstance->returnType = get_string(typeSpelling);
    clang_disposeString(typeSpelling);
    
    // function name
    int index = 0; 
    const char* fullName = get_string(cursorData.name);
    index = get_string_token(&fullName[0], &newInstance->name, '(');

    // handle function arguments
    newInstance->argsTypes = get_parameters_types(cursor);

    // insert
    if (!last)
    {
        functions = &newInstance->next;
    }
    else
    {
        last->next = &newInstance->next;
    }
}

void cursor_handler_parameter(CXCursor cursor, CursorData cursorData) 
{

}

void cursor_handler_typedef(CXCursor cursor, CursorData cursorData)
{
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
    newInstance->alias = get_string(cursorData.name);

    // underlying type
    CXType underlyingType = clang_getTypedefDeclUnderlyingType(cursor);
    CXString underlyingTypeString = clang_getTypeSpelling(underlyingType);
    newInstance->underlyingType = get_string(underlyingTypeString);
    clang_disposeString(underlyingTypeString);

    // insert
    if (!last)
    {
        typedefs = &newInstance->next;
    }
    else
    {
        last->next = &newInstance->next;
    }
}

void cursor_handler_macro(CXCursor cursor, CursorData cursorData)
{
    // filter out function-like macros
    if (clang_Cursor_isMacroFunctionLike(cursor))  
    {
        return;
    }

    // only macros representing constants
    if (cursorData.tokens.tokensNumber != 2)  
    {
        return;
    }
    
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
    newInstance->name = get_string(cursorData.name);

    // macro value = token on the 1 index position
    CXString tokenSpelling = clang_getTokenSpelling(cursorData.unit, cursorData.tokens.tokensArray[1]);
    newInstance->value =get_string(tokenSpelling);
    clang_disposeString(tokenSpelling);

    // insert
    if (!last)
    {
        macros = &newInstance->next;
    }
    else
    {
        last->next = &newInstance->next;
    }
}

// get cursor common information

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

CXString get_cursor_type(CXCursor cursor, bool canonical)
{
    CXType cursorType = clang_getCursorType(cursor);
    
    if (canonical)
    {
        cursorType = clang_getCanonicalType(cursorType);
    }

    CXString cursorTypeString = clang_getTypeSpelling(cursorType);

    return cursorTypeString;
}

CXString get_cursor_name(CXCursor cursor)
{
    CXString cursorName = clang_getCursorDisplayName(cursor);
    return cursorName;
}

CursorLocation get_cursor_location(CXCursor cursor)
{
    CXSourceLocation sourceLocation = clang_getCursorLocation(cursor);
    CursorLocation cursorLocation = { 0 };
    
    CXFile file;
    clang_getFileLocation(sourceLocation, &file, &cursorLocation.line, &cursorLocation.column, NULL);
    cursorLocation.file = clang_getFileName(file);

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

// disposing resources

void dispose_cursor_data(CursorData cursorData)
{
    clang_disposeString(cursorData.type);
    clang_disposeString(cursorData.name);
    clang_disposeString(cursorData.location.file);
    clang_disposeTokens(cursorData.unit, cursorData.tokens.tokensArray, cursorData.tokens.tokensNumber);
}

void dispose_structures()
{
    StructType* current, * temp;
    if (structures)
    {
        current = GET_NODE(structures, StructType, next);
        while (current)
        {
            temp = GET_NODE(current->next.next, StructType, next);

            free(current->name);
            current->name = NULL;

            dispose_fields(&current->fields);

            current = temp;
        }

        free(structures);
        structures = NULL;
    }
}

void dispose_enums()
{
    EnumType* current, * temp;
    if (enums)
    {
        current = GET_NODE(enums, EnumType, next);
        while (current)
        {
            temp = GET_NODE(current->next.next, EnumType, next);

            free(current->name);
            current->name = NULL;

            dispose_enum_constants(&current->constants);

            current = temp;
        }

        free(enums);
        enums = NULL;
    }
}

void dispose_fields(ListNode** fields)
{
    FieldType* current, * temp;
    if (*fields)
    {
        current = GET_NODE(*fields, FieldType, next);
        while (current)
        {
            temp = GET_NODE(current->next.next, FieldType, next);

            free(current->name);
            current->name = NULL;

            free(current->type);
            current->type = NULL;

            current = temp;
        }

        free(*fields);
        *fields = NULL;
    }
}

void dispose_enum_constants(ListNode** enumConstants)
{
    EnumConstantType* current, * temp;
    if (*enumConstants)
    {
        current = GET_NODE(*enumConstants, EnumConstantType, next);
        while (current)
        {
            temp = GET_NODE(current->next.next, EnumConstantType, next);

            free(current->name);
            current->name = NULL;

            current = temp;
        }

        free(*enumConstants);
        *enumConstants = NULL;
    }
}

void dispose_functions()
{
    FunctionType* current, * temp;
    if (functions)
    {
        current = GET_NODE(functions, FunctionType, next);
        while (current)
        {
            temp = GET_NODE(current->next.next, FunctionType, next);

            free(current->name);
            current->name = NULL;

            free(current->returnType);
            current->returnType = NULL;

            if(current->argsTypes)
            {
                int argNumber = 0;
                char* argument = current->argsTypes[argNumber];
                while (argument)
                {
                    free(argument);
                    ++argNumber;
                    argument = current->argsTypes[argNumber];
                }

                free(current->argsTypes);
                current->argsTypes = NULL;
            }

            current = temp;
        }

        free(enums);
        enums = NULL;
    }
}

void dispose_typedefs()
{
    TypedefType* current, * temp;
    if (typedefs)
    {
        current = GET_NODE(typedefs, TypedefType, next);
        while (current)
        {
            temp = GET_NODE(current->next.next, TypedefType, next);

            free(current->alias);
            current->alias = NULL;

            free(current->underlyingType);
            current->underlyingType = NULL;

            current = temp;
        }

        free(typedefs);
        typedefs = NULL;
    }
}

void dispose_macros()
{
    MacroType* current, * temp;
    if (macros)
    {
        current = GET_NODE(macros, MacroType, next);
        while (current)
        {
            temp = GET_NODE(current->next.next, MacroType, next);

            free(current->name);
            current->name = NULL;

            free(current->value);
            current->value = NULL;

            current = temp;
        }

        free(macros);
        macros = NULL;
    }
}

// utilities

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

char* get_string(CXString clangString)
{
    const char* temp = clang_getCString(clangString);
    size_t length = strlen(temp);  
    
    char* string = (char*)malloc(length + 1); // to add '\0'
    if (string)
    {
        strncpy(string, temp, length);
        string[length] = '\0';
    }

    return string;
}

int get_string_token(const char* source, char** destination, char separator)  // return -1 if end of string is achieved, otherwise index of separator
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

char** get_parameters_types(CXCursor cursor)
{
    int argsNumber = clang_Cursor_getNumArguments(cursor);
    char** types = (char**)calloc(sizeof(char**), argsNumber + 1);  // add NULL to indicate end of args

    if (!types)
    {
        return NULL;
    }

    int i;
    for (i = 0; i < argsNumber; ++i)
    {
        CXCursor argument = clang_Cursor_getArgument(cursor, i);
        CXString type = get_cursor_type(argument, true);
        types[i] = get_string(type);
        clang_disposeString(type);
    }
    types[i] = NULL;

    return types;
}
