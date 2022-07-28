#include "header.h"


// test_traversal_ast :: check correct traversal
#define SOURCE_DEFINE_test "source_define_test"


// test_typedef_parsing_iteration :: check first iteration
// test_handle_structs
typedef struct IncompleteStruct_test Typedef_IncompleteStruct_test;
typedef struct IncompleteStruct_test * IncompleteHandler_test
typedef bool another_bool_test;


// test_typedef_parsing_iteration
// test_handle_enums
typedef enum EnumUnderlying_test
{
    ZERO = 0,
    ONE,
} EnumAlias_test;


// test_handle_enums
enum EnumWithoutTypedef_test
{
    NEGATIVE = -1,
    MACRO = MACRO_INT1_test,
}


// test_typedef_parsing_iteration
typedef int(callback_test*)(int, int);


// test_handle_structs
typedef struct S_callback_test
{
    callback_test function;
} S_callback_test;


// test_handle_structs
typedef struct S_test* S_handler
struct S_test
{
    int array[123];
    char c;
    struct S_test** self;
    S_handler* self_handler;
};


// test_handle_functions
void FunctionEmpty_test();
int FunctionDefault_test(int*, char**);
EnumAlias_test FunctionAliases_test(struct IncompleteStruct_test**);
UnknownEnum FunctionUnknownEnum_test(enum EnumWithoutTypedef_test*);
struct UnknownStruct FunctionUnknownStruct_test(struct S_test*);


// handling pointers to structure inside this structure
// different cases

typedef struct T* T_handler;

struct T
{
    T_handler t;
}

typedef struct P P_alias;

struct P
{
    P_alias* p;
}

typedef struct Q* Q_handler

typedef struct Q
{
    Q_handler* q;
} Q_alias;