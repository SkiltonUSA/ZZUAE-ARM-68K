#pragma once
/* The upstream integer bus exception, adapted without C++ runtime unwinding.
 * TRY sites are limited to newcpu.cpp; callers must not hold C++ RAII objects. */
#include <setjmp.h>
extern jmp_buf *zzuae_exception;
void zzuae_throw(int value);
#define TRY(var) { jmp_buf zz_env; jmp_buf *zz_previous=zzuae_exception; zzuae_exception=&zz_env; int var=setjmp(zz_env); if(var==0)
#define CATCH(var) else if ((zzuae_exception=zz_previous, true))
#define ENDTRY zzuae_exception=zz_previous; }
#define THROW(n) zzuae_throw(n)
typedef int m68k_exception;
