// clang -Xclang -ast-dump <path_to_c> -I<path_to_headers> -fsyntax-only

#include <stddef.h>
#include <stdint.h>
#include "header.h"


//#ifndef APHY_TYPES_H
//#define APHY_TYPES_H
//
//#include <stdint.h>
//#include <stddef.h>
//#include <stdbool.h>
//#include <limits.h>
//#include <inttypes.h>
//
//#if defined(_MSC_VER)
//#include <BaseTsd.h>
//typedef SSIZE_T ssize_t;
//#endif
//
//#ifdef _WIN32
//#define EXPORT __declspec(dllexport)
//#else
//#define EXPORT
//#endif
//
//#endif
//
enum Enum1
{
	ZERO,
	ONE,
	TWO = 4,
};

typedef enum Enum2
{
	THREE = 3,
	FOUR,
	FIVE,
} TEnum2;


#define MACROINT 42
#define MACROSTR "stringmacro"
#define MACROFUNC(x) (x+1)


struct Struct1
{
	const char* key;
	struct NameS* next;
	int arr[MACRO];
	UnknownType field;
	size_t xy;
	uint16_t ij;
};

typedef void(*function)(UnknownType*);

typedef struct Struct2
{
	int anotherint;
	function funct;
} TStruct2;


void* function1(UnknownType* arg) 
{
	return;
}

int function2(int argc, char** argv)
{
	Name instance = { "key", 1, NULL };
	int result = foo(instance.value);

	return 0;
}