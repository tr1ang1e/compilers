#include <stddef.h>
#include "foo.h"

typedef struct NameS
{
	const char* key;
	int value;
	struct NameS* next;
} Name;

int main(int argc, char** argv)
{
	Name instance = { "key", 1, NULL };
	int result = foo(instance.value);

	return 0;
}


// clang -Xclang -ast-dump <path_to_c> -I<path_to_headers> -fsyntax-only