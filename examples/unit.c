// clang -Xclang -ast-dump <path_to_c> -I<path_to_headers> -fsyntax-only

#include <stddef.h>
#include <stdint.h>
#include "header.h"

enum NameE
{
	ZERO,
	ONE,
	TWO,
};

typedef struct NameS
{
	const char* key;
	int value;
	struct NameS* next;

	size_t xy;
	uint16_t ij;
} Name;

void function(struct Unknown arg) 
{
	return;
}

int main(int argc, char** argv)
{
	Name instance = { "key", 1, NULL };
	int result = foo(instance.value);

	return 0;
}