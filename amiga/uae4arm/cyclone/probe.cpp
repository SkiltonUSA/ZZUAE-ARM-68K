/* Isolated Cyclone comparison: the same 26-instruction workload as cpu_probe.cpp.
 * CPU throughput only; this does not establish Amiga chipset compatibility. */
#include <stdint.h>
#include <string.h>
#include "Cyclone.h"
#include "bench.h"
static uint16_t ram[32768];
static unsigned faults;
#ifdef CYCLONE_BIG_ENDIAN
#define BYTE_XOR 0
#else
#define BYTE_XOR 1
#endif
static unsigned read8(unsigned a) { if(a>=sizeof(ram)){++faults;return 0;}return ((uint8_t*)ram)[a^BYTE_XOR]; }
static unsigned read16(unsigned a) { return read8(a)*256+read8(a+1); }
static unsigned read32(unsigned a) { return read16(a)*65536+read16(a+2); }
static void write8(unsigned a,unsigned char v) { if(a>=sizeof(ram)){++faults;return;}((uint8_t*)ram)[a^BYTE_XOR]=v; }
static void write16(unsigned a,unsigned short v) { write8(a,v>>8);write8(a+1,v); }
static void write32(unsigned a,unsigned v) { write16(a,v>>16);write16(a+2,v); }
static unsigned checkpc(unsigned pc) { if(pc-(uintptr_t)ram>=sizeof(ram)){++faults;return (uintptr_t)ram+0x100;}return pc; }
static int irq(int) { return CYCLONE_INT_ACK_AUTOVECTOR; }
static void reset() { ++faults; }
extern "C" int mesen_test(int verify,MesenResult *r,int (*stop)(),uint32_t (*clock)()) {
    memset(r,0,sizeof(*r));faults=0;CycloneInit();
    const uint16_t program[]={0x7000,0x720a,0x5280,0x51c9,0xfffc,0x23c0,0x0000,0x0400,0x4e71,0x4e71,0x4e71};
    for(unsigned i=0;i<sizeof(program)/2;++i)write16(0x100+i*2,program[i]);
    uint32_t start=clock();
    for(unsigned run=0;run<1000;run++) {
        if(stop())return 2;
        Cyclone c{};write32(0x400,0);
        c.pc=(uintptr_t)ram+0x100;c.membase=(uintptr_t)ram;c.srh=0x27;
        c.jumptab=(uintptr_t)CycloneJumpTab;c.checkpc=checkpc;
        c.read8=c.fetch8=read8;c.read16=c.fetch16=read16;c.read32=c.fetch32=read32;
        c.write8=write8;c.write16=write16;c.write32=write32;c.IrqCallback=irq;c.ResetCallback=reset;
        unsigned n=0,cycles=0;
#ifdef CYCLONE_BATCH
        c.cycles=233;CycloneRun(&c);cycles=233-c.cycles;n=26;
#else
        while(c.pc-c.membase!=0x112 && n<64 && !faults) {
            c.cycles=0;CycloneRun(&c);cycles-=c.cycles;++n;
        }
#endif
        unsigned pc=c.pc-c.membase;
        if(n!=26 || cycles!=234 || pc!=0x112 || c.d[0]!=11 || c.d[1]!=65535 || read32(0x400)!=11 || faults || (CycloneGetSr(&c)&15)) {
            r->mismatch++;r->actual_pc=pc;r->expected_pc=0x112;r->actual_regs=c.d[0];r->expected_regs=11;
            r->errors=faults;r->cycles=cycles;r->checked=n;return 1;
        }
        r->checked+=n;r->cycles+=cycles;r->hash+=read32(0x400);
    }
    r->ticks=clock()-start;(void)verify;return 0;
}
