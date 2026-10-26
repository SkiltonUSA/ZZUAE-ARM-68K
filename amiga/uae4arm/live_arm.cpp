#include "sysconfig.h"
#include "sysdeps.h"
#include "options.h"
#include "custom.h"
#include "xwin.h"
#include "machine.h"
#include "live.h"
#include "audio_wire.h"
#include "protocol.h"
#include "live_pixels.h"
#include "../common/rtg_mapping.h"
static uint32_t published,present_phase;
extern "C" void zzuae_live_event(unsigned,int);
static void barrier() { __asm__ volatile("dsb sy" ::: "memory"); }
static void tlb() {
    uint32_t z=0;
    __asm__ volatile("dsb sy\n mcr p15,0,%0,c8,c7,0\n dsb sy\n isb"::"r"(z):"memory");
}
/* Map only the currently locked, OS-allocated bitmap. The same two-ended
 * ownership challenge and temporary NC/XN mapping are used by ZZDosBox. */
extern "C" unsigned zzuae_direct_convert(void) {
    volatile uint8_t *p=uae_shared+UAE_LIVE;
    uint32_t addr=ad_get(p,UL_ADDRESS),pitch=ad_get(p,UL_PITCH);
    uint32_t format=ad_get(p,UL_FORMAT),nonce=ad_get(p,UL_NONCE);
    uint32_t span=rtg_span_size(addr,pitch,format,640,256),error=0;
    uint32_t base=(uint32_t)uae_shared;
    uint32_t ttbr=(base+0x400000u+16383u)&~16383u;
    uint32_t table=(base+0x41c000u+1023u)&~1023u;
    uint32_t *l1=(uint32_t*)ttbr;
    if((format!=3 && format!=4) || !span || table+4096>base+0x420000u ||
       !rtg_map_size(l1,(uint32_t*)table,table,addr,pitch,format,640,256))return 6;
    tlb();volatile uint8_t *dst=(volatile uint8_t*)addr;
    if(ad_get(dst,0)!=nonce || ad_get(dst,span-4)!=(nonce^0x31415926u))error=7;
    else for(unsigned y=0;y<256;y++) {
        if(uae_stop && uae_stop()){error=2;break;}
        const uint16_t *src=(const uint16_t*)(gfxvidinfo.drawbuffer.bufmem+y*1280);
        volatile uint32_t *row=(volatile uint32_t*)(dst+y*pitch);
        for(unsigned x=0;x<640;x++)row[x]=ul_pixel(src[x],format);
    }
    barrier();rtg_unmap(l1,addr,span);tlb();return error;
}
static void input() {
    volatile uint8_t *p=uae_shared+UAE_LIVE;
    uint32_t tail=ad_get(p,UL_TAIL),head=ad_get(p,UL_HEAD);
    barrier();
    while(tail!=head) {
        uint32_t event=ad_get(p,UL_EVENTS+(tail%UL_CAPACITY)*4);
        zzuae_live_event(event>>16,(int16_t)event);
        ++tail;
    }
    barrier();ad_put(p,UL_TAIL,tail);barrier();
}
extern "C" void zzuae_live_present(void) {
    if(!uae_shared || !(ad_get(uae_shared,UAE_OPTIONS+4)&UAE_OPT_LIVE))return;
    /* Sound always follows PAL guest time. Lower presentation rates skip
     * host delivery only; Paula and chipset execution continue every frame. */
    if(ad_get(uae_shared,UAE_OPTIONS+4)&UAE_OPT_AUDIO){
        unsigned rate=ad_get(uae_shared,UAE_OPTIONS+40);
        if(rate && rate<50){present_phase+=rate;if(present_phase<50){input();return;}present_phase-=50;}
    }
    volatile uint8_t *p=uae_shared+UAE_LIVE;
    unsigned direct=ad_get(uae_shared,UAE_OPTIONS+4)&UAE_OPT_DIRECT;
    if(!direct)memcpy((void*)(uae_shared+UAE_FRAME),gfxvidinfo.drawbuffer.bufmem,640*256*2);
    barrier();ad_put(p,UL_FRAME,++published);barrier();
    if(direct) {
        while(ad_get(p,UL_GRANT)!=published) {
            if(uae_stop && uae_stop())return;
            input();
        }
        barrier();unsigned error=zzuae_direct_convert();
        ad_put(p,UL_ERROR,error);barrier();ad_put(p,UL_DONE,published);barrier();
    }
    while(ad_get(p,UL_ACK)!=published) {
        if(uae_stop && uae_stop())return;
        input();
    }
    barrier();input();
}
