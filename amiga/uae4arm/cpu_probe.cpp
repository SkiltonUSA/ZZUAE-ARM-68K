/* Original synthetic 68000 test. Opcode implementations are upstream UAE4ARM.
 * This is a CPU integration diagnostic, not an Amiga boot or FPS benchmark. */
#include "sysconfig.h"
#include "sysdeps.h"
#include "options.h"
#include "memory.h"
#include "newcpu.h"
#include "events.h"
#include "bench.h"
struct regstruct regs;
addrbank *mem_banks[MEMORY_BANKS];
const int imm8_table[]={8,1,2,3,4,5,6,7};
static unsigned faults;
static uae_u8 ram[65536];
static uae_u32 rb(uaecptr a) { if(a>=sizeof(ram)){faults++;return 0;}return ram[a]; }
static uae_u32 rw(uaecptr a) { return rb(a)*256+rb(a+1); }
static uae_u32 rl(uaecptr a) { return rw(a)*65536+rw(a+2); }
static void wb(uaecptr a,uae_u32 v) { if(a>=sizeof(ram)){faults++;return;}ram[a]=v; }
static void ww(uaecptr a,uae_u32 v) { wb(a,v>>8);wb(a+1,v); }
static void wl(uaecptr a,uae_u32 v) { ww(a,v>>16);ww(a+2,v); }
void exception3i(uae_u32,uaecptr) { faults++; }
void exception3_write(uae_u32,uaecptr) { faults++; }
static addrbank bank;
extern uae_u32 op_7000_11_ff(uae_u32),op_5080_11_ff(uae_u32),op_51c8_11_ff(uae_u32),op_23c0_11_ff(uae_u32),op_4e71_11_ff(uae_u32);
extern "C" int mesen_test(int verify,MesenResult *r,int (*stop)(),uint32_t (*clock)()) {
    memset(r,0,sizeof(*r));faults=0;
    memset(&bank,0,sizeof(bank));
    bank.lget=bank.lgeti=rl;bank.wget=bank.wgeti=rw;bank.bget=rb;
    bank.lput=wl;bank.wput=ww;bank.bput=wb;
    for(unsigned i=0;i<MEMORY_BANKS;i++)mem_banks[i]=&bank;
    const uint16_t program[]={0x7000,0x720a,0x5280,0x51c9,0xfffc,0x23c0,0x0000,0x0400,0x4e71,0x4e71,0x4e71};
    for(unsigned i=0;i<sizeof(program)/2;i++)ww(0x100+2*i,program[i]);
    uint32_t start=clock();
    for(unsigned run=0;run<1000;run++) {
        if(stop())return 2;
        memset(&regs,0,sizeof(regs));wl(0x400,0);regs.s=1;
        m68k_setpci(0x100);regs.ir=rw(0x100);regs.irc=rw(0x102);
        unsigned n=0,cycles=0;
        while(regs.pc!=0x112 && n<64 && !faults) {
            uae_u32 op=regs.ir,c=0;
            switch(op) {
            case 0x7000:case 0x720a:c=op_7000_11_ff(op);break;
            case 0x5280:c=op_5080_11_ff(op);break;
            case 0x51c9:c=op_51c8_11_ff(op);break;
            case 0x23c0:c=op_23c0_11_ff(op);break;
            case 0x4e71:c=op_4e71_11_ff(op);break;
            default:r->unsupported++;return 1;
            }
            cycles+=c/(CYCLE_UNIT/2);n++;
        }
        if(n!=26 || cycles!=234 || regs.pc!=0x112 || regs.regs[0]!=11 || regs.regs[1]!=65535 || rl(0x400)!=11 || faults || GET_ZFLG() || GET_NFLG() || GET_CFLG() || GET_VFLG()) {
            r->mismatch++;r->actual_pc=regs.pc;r->expected_pc=0x112;
            r->actual_regs=regs.regs[0];r->expected_regs=11;r->errors=faults;
            r->cycles=cycles;r->checked=n;return 1;
        }
        r->checked+=n;r->cycles+=cycles;r->hash+=rl(0x400);
    }
    r->ticks=clock()-start;
    (void)verify;return 0;
}
