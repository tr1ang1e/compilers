// clang -Xclang -ast-dump <path_to_c> -I<path_to_headers> -fsyntax-only

#include <stddef.h>
#include <stdint.h>
#include "header.h"


#ifndef APHY_TYPES_H
#define APHY_TYPES_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <limits.h>
#include <inttypes.h>

#if defined(_MSC_VER)
#include <BaseTsd.h>
typedef SSIZE_T ssize_t;
#endif

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif

#endif

enum NameE
{
	ZERO,
	ONE,
	TWO = 4,
};

#define MACRO 42
#define FMACRO(x) (x+1)

typedef struct NameS
{
	const char* key;
	struct NameS* next;
	int arr[MACRO];
	UnknownType filed;
	size_t xy;
	uint16_t ij;
} Name;


void function(UnknownType* arg) 
{
	return;
}

int main(int argc, char** argv)
{
	Name instance = { "key", 1, NULL };
	int result = foo(instance.value);

	return 0;
}