/* GPL-3.0-or-later. Owned cache and local A9 publication, following the tested
 * ZZDosBox DCCMVAU/ICIMVAU sequence. No Linux services or shared L2 operations.
 * Single Core1 producer/executor; no code execution during free or publication.
 * Page tables are this application's NC tables and all data pages start XN. */
#include "jit_cache.h"
#include "machine.h"
#include "protocol.h"
#include <stdlib.h>
static unsigned char arena[ZJ_CAPACITY+4095];
static uint32_t first,used,commits;
static uint32_t *pte(uint32_t address){
 uint32_t base=(uint32_t)uae_shared;
 uint32_t table=(base+0x400000u+16383u)&~16383u;
 uint32_t descriptor=((uint32_t*)table)[address>>20];
 uint32_t leaf=descriptor&~1023u;
 if((descriptor&3)!=1 || leaf<table+16384u || leaf+1024u>base+0x420000u)abort();
 return (uint32_t*)leaf+((address>>12)&255);
}
static void executable(int enable){
 const uint32_t end=(first+used+4095u)&~4095u;
 /* Validate every page first: no partial mapping changes on a bad descriptor. */
 for(uint32_t a=first;a<end;a+=4096){
  uint32_t expected=a|(enable?0x117u:0x116u);
  if(*pte(a)!=expected)abort();
 }
 for(uint32_t a=first;a<end;a+=4096){
  uint32_t *p=pte(a);*p=enable?(*p&~1u):(*p|1u);
 }
 uint32_t zero=0;
 __asm__ volatile("dsb sy\n mcr p15,0,%0,c8,c7,0\n dsb sy\n isb"::"r"(zero):"memory");
}
extern "C" __attribute__((noinline)) void *zzuae_jit_alloc_executable(unsigned size){
 if(used || !size || size>ZJ_CAPACITY)return NULL;
 first=((uint32_t)arena+4095u)&~4095u;
 uint32_t base=(uint32_t)uae_shared;
 if(!zj_span(base+0x640000u,0x1970000u,first,(size+4095u)&~4095u))abort();
 used=size;executable(1);return (void*)first;
}
extern "C" __attribute__((noinline)) void zzuae_jit_publish_code(void *start,void *stop){
 uint32_t at=(uint32_t)start,end=(uint32_t)stop,zero=0;
 if(end<at || !used || !zj_span(first,used,at,end-at))abort();
 /* L1 line size and inner-WB/outer-NC policy are checked by the entry shim. */
 for(uint32_t a=at&~31u;a<end;a+=32)
  __asm__ volatile("mcr p15,0,%0,c7,c11,1"::"r"(a):"memory");
 __asm__ volatile("dsb sy":::"memory");
 for(uint32_t a=at&~31u;a<end;a+=32)
  __asm__ volatile("mcr p15,0,%0,c7,c5,1"::"r"(a):"memory");
 __asm__ volatile("mcr p15,0,%0,c7,c5,6\n dsb sy\n isb"::"r"(zero):"memory");
 ++commits;
}
extern "C" __attribute__((noinline)) void zzuae_jit_free_executable(void *p,unsigned size){
 if(!used || (uint32_t)p!=first || size!=used)abort();
 executable(0);used=0;
}
extern "C" unsigned zzuae_jit_cache_selftest(void){
 unsigned checks=0;
 if(zzuae_jit_alloc_executable(0) || zzuae_jit_alloc_executable(ZJ_CAPACITY+1))return 1;
 for(unsigned round=0;round<2;round++){
  uint32_t *code=(uint32_t*)zzuae_jit_alloc_executable(8192);
  if(!code || zzuae_jit_alloc_executable(4))return 2;
  const unsigned offsets[]={0,7,1023}; /* ordinary, L1 line and page crossing */
  for(unsigned i=0;i<3;i++)for(unsigned n=41;n<49;n++){
   uint32_t *entry=code+offsets[i];
   entry[0]=0xe3a00000u|(n+round*8);entry[1]=0xe12fff1eu;
   zzuae_jit_publish_code(entry,entry+2);
   if(((unsigned(*)())entry)()!=n+round*8)return 3;
   ++checks;
  }
  uint32_t a=first;
  zzuae_jit_free_executable(code,8192);
  if(*pte(a)!=(a|0x117u) || *pte(a+4096)!=((a+4096)|0x117u))return 4;
 }
 ad_put(uae_shared,ZJ_REPORT,0x4a495443u);ad_put(uae_shared,ZJ_REPORT+4,checks);
 ad_put(uae_shared,ZJ_REPORT+8,commits);ad_put(uae_shared,ZJ_REPORT+12,!used);
 __asm__ volatile("dsb sy":::"memory");return 0;
}
