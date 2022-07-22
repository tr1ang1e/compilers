#include "header.h"


// test_traversal_ast :: check correct traversal
#define SOURCE_DEFINE_test "source_define_test"


// test_typedef_parsing_iteration :: check first iteration
// test_handle_structs
typedef struct IncompleteStruct_test Typedef_IncompleteStruct_test;
typedef bool another_bool_test


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


// test_handle_functions
void FunctionEmpty_test();
int FunctionDefault_test(int*, char**);
EnumAlias_test FunctionAliases_test(struct IncompleteStruct_test**);
UnknownEnum FunctionUnknown_test(enum EnumWithoutTypedef_test*);


// test_handle_structs
struct S_test
{
    int array[123];
    char c;
    struct S_test** self;
};