/* Diagnostic-only fault capture. Private VBAR restored before fatal unwind. */
#include "machine.h"
#include "protocol.h"
#include <stdlib.h>
extern "C" void zz_jit_vectors();
static unsigned original_vbar,installed;
extern "C" int zz_jit_fault_install(){
 unsigned sctlr,cpsr;
 __asm__ volatile("mrs %0,cpsr\n mrc p15,0,%1,c1,c0,0":"=r"(cpsr),"=r"(sctlr));
 if((cpsr&0xdf)!=0xd3 || (sctlr&0x2000) || installed)return 0;
 __asm__ volatile("mrc p15,0,%0,c12,c0,0":"=r"(original_vbar));
 unsigned vectors=(unsigned)&zz_jit_vectors;
 if(vectors&31)return 0;
 __asm__ volatile("dsb sy\n mcr p15,0,%0,c12,c0,0\n isb"::"r"(vectors):"memory");
 installed=1;return 1;
}
extern "C" void zz_jit_fault_restore(){
 if(!installed)return;
 __asm__ volatile("dsb sy\n mcr p15,0,%0,c12,c0,0\n isb"::"r"(original_vbar):"memory");
 installed=0;
}
extern "C" __attribute__((noreturn)) void zz_jit_fault(unsigned reason,unsigned link,unsigned saved_cpsr){
 unsigned dfsr,ifsr,dfar,ifar;
 __asm__ volatile("mrc p15,0,%0,c5,c0,0\n mrc p15,0,%1,c5,c0,1\n mrc p15,0,%2,c6,c0,0\n mrc p15,0,%3,c6,c0,2":"=r"(dfsr),"=r"(ifsr),"=r"(dfar),"=r"(ifar));
 unsigned fields[]={0x4a464c54u,reason,link,saved_cpsr,dfsr,ifsr,dfar,ifar};
 for(unsigned i=0;i<8;i++)ad_put(uae_shared,0x482a40+i*4,fields[i]);
 __asm__ volatile("dsb sy":::"memory");zz_jit_fault_restore();exit(100+reason);
}
