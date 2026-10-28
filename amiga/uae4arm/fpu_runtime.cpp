#include <stdlib.h>
#include <stdint.h>
void jit_abort(const char*,...){exit((int)(uintptr_t)__builtin_return_address(0));}
