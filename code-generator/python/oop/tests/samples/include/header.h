#ifndef HEADER
#define HEADER

#include "helper.h"

// test_traversal_ast :: check correct traversal
#define HEADER_DEFINE_test "header_define_test"

// test_typedef_parsing_iteration :: check first iteration
typedef uint8_t u8_test;
typedef bool bool_test;

// test_handle_macros
// test_handle_typedefs
#define MACRO_INT1_test 42
#define MACRO_INT2_test (123)
#define MACRO_STR_test "string"
#define MACRO_EMPTY_test
#define MACRO_FUNC_test(arg) (arg)



#endif // HEADER