#include <assert.h>
#include <stdio.h>
#include "policy.h"
int main(void){
 struct zo_status s;
 const char *stock="CLOCK_SESSION error=0 target_div=0 temp=55.1 C ctrl=00028008 cfg=000fa220 cpu=1f000200 nonce=0 fault=0 core1_idle=1\nCLOCK_KEEP held=0\n";
 assert(zo_parse(stock,&s)&&s.mhz10==6667&&zo_can_apply(&s));
 assert(zo_parse("CLOCK_SESSION error=0 target_div=48 temp=55.3 C ctrl=00030008 cfg=000fa240 cpu=1f000200 nonce=800171117 fault=0 core1_idle=1\nCLOCK_KEEP held=1\n",&s)&&s.mhz10==8000&&zo_can_apply(&s));
 s.idle=0;assert(!zo_can_apply(&s));s.idle=1;
 s.temp10=601;assert(!zo_can_apply(&s));s.temp10=550;
 s.fault=1;assert(!zo_can_apply(&s));s.fault=0;
 s.nonce=123;assert(!zo_can_apply(&s));
 assert(!zo_parse("Clock diagnostic firmware unavailable",&s));
 assert(!zo_parse("CLOCK_SESSION error=0 target_div=48 temp=55.3 C ctrl=00030008 cfg=000fa220 cpu=1f000200 nonce=0 fault=0 core1_idle=1\nCLOCK_KEEP held=1\n",&s));
 puts("PASS stock/800 status, unsupported firmware, busy, temperature, fault and foreign ownership");
}
