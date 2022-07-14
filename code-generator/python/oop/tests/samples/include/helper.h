// represents some parts of standard C library to
// make test independent of C environment
#ifndef HELPER
#define HELPER


// test_traversal_ast :: check correct traversal
#define SKIP_DEFINE_test "skip_define_test"

// test_typedef_parsing_iteration :: check first iteration
typedef unsigned char uint8_t;
typedef _Bool bool;


#endif  // HELPER