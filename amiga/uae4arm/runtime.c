/* Small PIC runtime for the diagnostic worker; no host I/O or TLS. */
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <time.h>
#include <stdlib.h>
#include <setjmp.h>
jmp_buf uae_fatal;
int uae_fatal_active;
int errno;
int printf(const char *s,...){(void)s;return 0;}
int fprintf(FILE *f,const char *s,...){(void)f;(void)s;return 0;}
int puts(const char*s){(void)s;return 0;}
int fflush(FILE *f){(void)f;return 0;}
void exit(int status){if(uae_fatal_active){uae_fatal_active=0;longjmp(uae_fatal,status?status:1);}for(;;)__asm__ volatile("wfe");}
void abort(void){
#if ZU_JIT_TRACE_INSTRUCTIONS == 1 || ZU_JIT_EVENT_BLOCKS
 /* Isolated timing diagnostics report the relocated ARM caller for symbolisation. */
 exit((int)(uintptr_t)__builtin_return_address(0));
#else
 exit(99);
#endif
}
void __assert_func(const char *file,int line,const char *fn,const char *expr){(void)file;(void)line;(void)fn;(void)expr;abort();}
int isspace(int c){return c==' '||(c>=9&&c<=13);}
int toupper(int c){return c>='a'&&c<='z'?c-32:c;}
time_t time(time_t *t){if(t)*t=0;return 0;}
struct tm *localtime(const time_t *t){static struct tm epoch={0,0,0,1,0,70,4,0,0};if(*t!=0)return NULL;return &epoch;}
