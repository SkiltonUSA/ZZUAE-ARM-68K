#include "wire.h"
#include "bench.h"
#ifdef MB_MMU
#include "mmu.h"
#endif
static volatile uint8_t *shared;
static void barrier() { __asm__ volatile("dsb sy" ::: "memory"); }
extern "C" void mesen_progress(uint32_t phase) {
    ad_put(shared,MB_REPLY+64,phase);barrier();
}
static uint64_t ticks() {
    volatile uint32_t *t = (volatile uint32_t *)0xf8f00200u;
    uint32_t hi,lo;
    do { hi=t[1];lo=t[0]; } while(hi!=t[1]);
    return (uint64_t)hi<<32 | lo;
}
static uint32_t clock_low() { barrier(); return (uint32_t)ticks(); }
static int stopped() { return ad_get(shared,ZZ_STOP)!=0; }
extern "C" void zz_worker(volatile uint8_t *base) {
    uint32_t sctlr,midr,mpidr,seq=0;
    shared=base;
    __asm__ volatile("mrc p15,0,%0,c1,c0,0":"=r"(sctlr));
    __asm__ volatile("mrc p15,0,%0,c0,c0,0":"=r"(midr));
    __asm__ volatile("mrc p15,0,%0,c0,c0,5":"=r"(mpidr));
#ifdef MB_MMU
    uint32_t wanted=0x1001u;
#ifdef MB_DCACHE
    wanted|=4u;
#endif
    if((sctlr&0x1005u)!=wanted||(mpidr&255u)!=1u)return;
    for(unsigned i=0;i<256;i++)ad_put(base,MB_WITNESS+i*4,ad_get(base,ZZ_CONTROL)^(i*0x01010101u));
#elif defined(MB_ICACHE)
    if((sctlr&0x1005u)!=0x1000u||(mpidr&255u)!=1u)return;
#else
    if((sctlr&0x1005u)||(mpidr&255u)!=1u)return;
#endif
    if(!(*(volatile uint32_t *)0xf8f00208u&1u))return;
    ad_put(base,ZZ_DIAG+4,sctlr);ad_put(base,ZZ_DIAG+8,midr);ad_put(base,ZZ_DIAG+12,mpidr);
    ad_put(base,ZZ_DIAG,ZZ_READY);barrier();
    while(!stopped()) {
        volatile uint8_t *cmd=base+MB_HOST,*reply=base+MB_REPLY;
        uint32_t next=ad_get(cmd,MB_SEQ);
        if(next==seq)continue;
        barrier();uint32_t op=ad_get(cmd,MB_OP),error=0;
        uint32_t token=ad_get(cmd,8);
        MesenResult result{};
        if(next!=seq+1 || token!=(next^ad_get(base,ZZ_CONTROL)))error=3;
        else if(op==MB_VERIFY || op==MB_BENCH)
            error=mesen_test(op==MB_VERIFY,&result,stopped,clock_low);
#ifdef MB_MMU
        else if(op==MB_CANCEL) {
            /* Bounded stress workload; cancellation must be observed through
             * the uncached shared stop word while private D-cache is active. */
            for(unsigned repeat=0;repeat<10000;repeat++) {
                error=mesen_test(0,&result,stopped,clock_low);
                if(error)break;
            }
            if(!error)error=5; /* host cancellation did not arrive */
        }
#endif
        else if(op!=MB_CLOCK)error=4;
        uint64_t now=ticks();
        ad_put(reply,MB_ERROR,error);ad_put(reply,MB_LO,(uint32_t)now);ad_put(reply,MB_HI,(uint32_t)(now>>32));
        const uint32_t values[]={result.checked,result.mismatch,result.cycles,result.hash,
            result.errors,result.unsupported,result.ticks,result.actual_pc,result.expected_pc,
            result.actual_regs,result.expected_regs};
        for(unsigned i=0;i<sizeof(values)/sizeof(values[0]);i++)ad_put(reply,MB_RESULT+i*4,values[i]);
        ad_put(reply,68,token^ZZ_XOR);
        barrier();ad_put(reply,MB_ACK,next);barrier();seq=next;
    }
}
