/* Status boundary for the existing experimental clock firmware. */
#pragma once
#include <stdio.h>
#include <string.h>
#define ZO_NONCE 800171117u
struct zo_status {unsigned mhz10,temp10,idle,held,nonce,fault;};
static int zo_parse(const char *text,struct zo_status *s){
 unsigned error,div,whole,frac,ctrl,cfg,cpu;
 const char *line=strstr(text,"CLOCK_SESSION "),*keep=strstr(text,"CLOCK_KEEP held=");
 memset(s,0,sizeof *s);
 if(!line||!keep||sscanf(line,"CLOCK_SESSION error=%u target_div=%u temp=%u.%u C ctrl=%x cfg=%x cpu=%x nonce=%u fault=%u core1_idle=%u",&error,&div,&whole,&frac,&ctrl,&cfg,&cpu,&s->nonce,&s->fault,&s->idle)!=10||sscanf(keep,"CLOCK_KEEP held=%u",&s->held)!=1)return 0;
 if(error||cpu!=0x1f000200||frac>9||whole>150)return 0;
 if(ctrl==0x28008&&cfg==0xfa220)s->mhz10=6667;
 else if(ctrl==0x30008&&cfg==0xfa240)s->mhz10=8000;
 else return 0;
 s->temp10=whole*10+frac;return 1;
}
static int zo_can_apply(const struct zo_status *s){
 return s->mhz10&&s->idle&&!s->fault&&s->temp10<=600&&(!s->nonce||s->nonce==ZO_NONCE);
}
