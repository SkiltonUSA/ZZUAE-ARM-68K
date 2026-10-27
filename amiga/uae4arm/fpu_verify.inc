/* Diagnostic guest code is assembled from tests/amiga/uae4arm/fpu_guest.S. */
#include "fpu_fixture.h"
static int zu_fpu_verify(MesenResult *r,int (*stop)()){
    static const uint32_t expected[]={16,4,0x40030000,0x80000000,0,2,3,2,4,0x46505531};
    map_overlay(1);
    for(unsigned i=0;i<sizeof(zu_fpu_fixture);i++)put_byte(0x100+i,zu_fpu_fixture[i]);
    regs.s=1;regs.intmask=7;regs.regs[15]=0x70000;m68k_setpc(0x100);
    fpu_reset();
    for(unsigned i=0;i<4096 && get_long(0x10024)!=0x46505531;i++){
        if(stop())return 2;
        uae_u32 op=get_diword(0);cpufunctbl[op](op);
    }
    for(unsigned i=0;i<sizeof(expected)/sizeof(expected[0]);i++){
        uint32_t value=get_long(0x10000+i*4);
        if(value!=expected[i])r->mismatch|=1u<<i;
        r->hash=r->hash*31+value;r->checked++;
    }
    r->errors=r->mismatch?1:0;r->cycles=zz_fpu_instructions;
    r->actual_pc=m68k_getpc();return r->errors?1:0;
}
