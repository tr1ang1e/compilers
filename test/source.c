// clang -Xclang -ast-dump <path_to_c> -I<path_to_headers> -fsyntax-only


// can find standard headers
#include <stddef.h>
#include <stdint.h>


// can find relative paths
#include "header.h"


// correct parsing for Linux target machine
#ifdef __linux__
#define LINMAC "linux"
#endif


// correct parsing for not-Windows target machine
#ifdef _WIN32
#define WINMAC "windows"
#else
#define NOTWINMAC "notwin"
#endif


// only constnant representing macros
#define MACRO_INT 42
#define MACRO_FUNC_LIKE(arg) (++arg)


// single typedefs
typedef void(*function_p)(int**, char);
typedef char** char_pp;


// enum, enum constants
enum EnumNotTypedef
{
	ZERO,
	ONE,
	BY_MACRO_INT = MACRO_INT,
};


// enum, enum constants, combine with typedef
typedef enum EnumTypedefUnderlying
{
	NEGATIVE = -1,
	FOUR = 4,
	FIVE,
} EnumTypedefAlias;


// struct
struct StructNotTypedef
{
	void* structField;
};

// struct combined with typedef
typedef struct StructTypedefUnderlying
{
	void* structField;
} StructTypedefAlias;


// struct fields
struct StructFields
{
	// void
	void void_nop;
	void* void_p;
	void** void_pp;

	// platform-dependent
	uint8_t u8;
	int16_t s16;
	size_t sizet;

	// arrays
	int arraySizeFromHeaderMacro[HEADER_MACRO_INT];
	int** arrayPointerPointer[MACRO_INT];

	// char
	char char_nop;
	char* char_p;
	char** char_pp;

	// qualifiers
	const int without_c;
	volatile int without_v;
	const volatile int without_cv;

	// enums
	enum EnumNotTypedef enum_notypedef;
	enum EnumTypedefUnderlying enum_underlying;
	EnumTypedefAlias enum_alias;

	// structs
	struct StructNotTypedef struct_notypedef;
	struct StructTypedefUnderlying struct_underlying;
	StructTypedefAlias struct_alias;
	struct StructFields* struct_itself_p;
	struct StructFields** struct_itself_pp;

	// types from header
	struct headerStructS struct_header_underlying;		// alias if header generated, c_void_p if header only parsed
	headerStruct struct_header_alias;					// alias if header generated, c_void_p if header only parsed
	// struct unknownType struct_noexist;				// should cause error anyway because no such a type
};


// correct parsing function without definition
void function_declaraion(size_t);


// correct 'restrict' parsing and skipping function body
void function_definition(int* restrict without_restrict, function callback)
{
	int localVariable = 1;

	return;
}