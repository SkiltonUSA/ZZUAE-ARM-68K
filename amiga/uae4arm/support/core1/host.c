#include <exec/memory.h>
#include <devices/timer.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <proto/timer.h>
#include <stdio.h>
#include "wire.h"
#include "expected.h"
#ifdef MB_MMU
#include "mmu.h"
#endif
struct Device *TimerBase;
static volatile uint8_t *shared;
static const struct ad_io *syncio;
static uint32_t sequence;
static ULONG us(void) { struct timeval t;GetSysTime(&t);return t.tv_secs*1000000u+t.tv_micro; }
static ULONG value(unsigned field) { return ad_get(shared+MB_REPLY,MB_RESULT+field*4); }
static int request(ULONG op) {
    ULONG start=us(),cancel_sent=0;volatile uint8_t *cmd=shared+MB_HOST,*reply=shared+MB_REPLY;
    ULONG token=(sequence+1)^ad_get(shared,ZZ_CONTROL);
    ad_put(cmd,8,token);
    ad_put(cmd,MB_OP,op);syncio->push(cmd+4,60,NULL);syncio->barrier(NULL);
    ad_put(cmd,MB_SEQ,++sequence);syncio->push(cmd,4,NULL);
    do {
        syncio->pull(reply,96,NULL);
        if(ad_get(reply,MB_ACK)==sequence) {
            if(ad_get(reply,68)!=(token^ZZ_XOR)){puts("MAILBOX ECHO FAIL");return 0;}
            if(op==MB_CANCEL && cancel_sent && ad_get(reply,MB_ERROR)==2) {
                printf("CANCEL PASS active_work=1 elapsed_us=%u\n",(ULONG)(us()-start));return 1;
            }
            if(ad_get(reply,MB_ERROR))printf("FAIL op=%u error=%u checked=%u mismatch=%u pc=%04x expected_pc=%04x regs=%08x expected_regs=%08x\n",
                op,(ULONG)ad_get(reply,MB_ERROR),value(0),value(1),value(7),value(8),value(9),value(10));
            return ad_get(reply,MB_ERROR)==0;
        }
        if(SetSignal(0,SIGBREAKF_CTRL_C)&SIGBREAKF_CTRL_C)return 0;
        if(op==MB_CANCEL && !cancel_sent && (ULONG)(us()-start)>=100000u) {
            ad_put(shared,ZZ_STOP,1);syncio->push(shared+ZZ_STOP,4,NULL);cancel_sent=1;
        }
        Delay(1);
    } while((ULONG)(us()-start)<10000000u);
    syncio->pull(shared+MB_REPLY+64,64,NULL);
    printf("TIMEOUT op=%u phase=%08x\n",op,(ULONG)ad_get(shared,MB_REPLY+64));return 0;
}
static uint64_t armclock(void) { return (uint64_t)ad_get(shared+MB_REPLY,MB_HI)<<32 | ad_get(shared+MB_REPLY,MB_LO); }
int ff_window(volatile uint8_t *base,const struct ad_io *io,int connected) {
    struct MsgPort *port=NULL;struct timerequest *timer=NULL;
    int opened=0,rc=20;ULONG t0,t1,rate,i;uint64_t c0,c1;
    (void)connected;shared=base;syncio=io;
    port=CreateMsgPort();if(!port)goto done;
    timer=(struct timerequest *)CreateIORequest(port,sizeof(*timer));if(!timer)goto done;
    if(OpenDevice(TIMERNAME,UNIT_MICROHZ,(struct IORequest *)timer,0))goto done;
    opened=1;TimerBase=timer->tr_node.io_Device;
#ifdef MB_MMU
#ifdef MB_DCACHE
    puts("MESEN CPU-ONLY; private inner WB/WA; MMU/I/D ON; shared and outer NC");
#else
    puts("MESEN CPU-ONLY; private MMU/I ON; D OFF; shared and outer NC");
#endif
#elif defined(MB_ICACHE)
    puts("MESEN CPU-ONLY; no PPU/APU/display/game FPS; I-cache ON, MMU/D-cache OFF");
#else
    puts("MESEN CPU-ONLY; no PPU/APU/display/game FPS; MMU/I-cache/D-cache OFF");
#endif
    if(!request(MB_CLOCK))goto done;
    c0=armclock();t0=us();Delay(100);
    if(!request(MB_CLOCK))goto done;
    c1=armclock();t1=us();rate=(ULONG)((c1-c0)*1000000u/(t1-t0));
    printf("TIMER estimated_hz=%u calibration_us=%u\n",rate,t1-t0);
    if(rate<320000000u || rate>345000000u)goto done;
    if(!request(MB_VERIFY))goto done;
    printf("VERIFY checked=%u mismatch=%u cycles=%u hash=%08x errors=%u unsupported=%u\n",
        value(0),value(1),value(2),value(3),value(4),value(5));fflush(stdout);
    if(value(0)!=8991 || value(1) || value(2)!=MESEN_EXPECT_CYCLES || value(3)!=MESEN_EXPECT_HASH || value(4) || value(5))goto done;
    for(i=0;i<11;i++) {
        if(!request(MB_BENCH))goto done;
        if(value(0) || value(1) || value(2)!=MESEN_EXPECT_CYCLES || value(3)!=MESEN_EXPECT_HASH || value(4) || value(5) || !value(6))goto done;
        printf("SAMPLE n=%u warmup=%u instructions=8991 cycles=%u ticks=%u cpu_us=%u hash=%08x\n",
            i,i==0,value(2),value(6),(ULONG)((uint64_t)value(6)*1000000u/rate),value(3));fflush(stdout);
    }
#ifdef MB_MMU
    if(!request(MB_CANCEL))goto done;
#endif
    puts("MESEN_CPU PASS; CPU-only throughput, NOT emulated video FPS");fflush(stdout);rc=0;
done:
    if(opened)CloseDevice((struct IORequest *)timer);
    if(timer)DeleteIORequest((struct IORequest *)timer);
    if(port)DeleteMsgPort(port);
    return rc;
}
#ifdef MB_MMU
/* Invoked only after RET1 and synchronous idle reset, before FreeMem. */
int mb_after_stop(volatile uint8_t *base,const struct ad_io *io) {
    ULONG i,bad=0,phase,registers,mask;
    io->pull(base+MB_MMU_REPORT,160,NULL);
    phase=ad_get(base,MB_MMU_REPORT);registers=ad_get(base,MB_MMU_REPORT+4);
    mask=ad_get(base,MB_MMU_REPORT+136);
    io->pull(base+MB_WITNESS-32,1088,NULL);
    for(i=0;i<256;i++)if(ad_get(base,MB_WITNESS+i*4)!=(ad_get(base,ZZ_CONTROL)^i*0x01010101u))bad++;
    for(i=0;i<32;i+=4)if(ad_get(base,MB_WITNESS-32+i) || ad_get(base,MB_WITNESS+1024+i))bad++;
    printf("MMU_RESTORE phase=%u register_mismatches=%08x cpsr_control=%03x expected=%03x ttbr=%08x ccsidr=%08x witness_bad=%u mailbox_rounds=%u\n",
        phase,registers,mask,ad_get(base,MB_MMU_REPORT+16+6*4)&511u,
        ad_get(base,MB_MMU_REPORT+8),ad_get(base,MB_MMU_REPORT+12),bad,sequence);
    for(i=0;i<14;i++)printf("REGISTER n=%u original=%08x restored=%08x\n",i,
        ad_get(base,MB_MMU_REPORT+16+i*4),ad_get(base,MB_MMU_REPORT+80+i*4));
    return phase==3 && !registers && !bad && mask==(ad_get(base,MB_MMU_REPORT+16+6*4)&511u);
}
#endif
