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
#include "rtc_time.h"
extern uint64_t zu_rtc_now_us(void);
static uint32_t rtc_seconds;
static uint64_t rtc_started;
void zu_rtc_seed(uint32_t seconds,uint64_t monotonic_us){rtc_seconds=seconds;rtc_started=monotonic_us;}
time_t time(time_t *t){
 uint32_t seconds=rtc_seconds?rtc_seconds+(uint32_t)((zu_rtc_now_us()-rtc_started)/1000000u):0;
 if(t)*t=(time_t)seconds;return (time_t)seconds;
}
struct tm *localtime(const time_t *t){static struct tm fields;zu_rtc_calendar((uint32_t)*t,&fields);return &fields;}
