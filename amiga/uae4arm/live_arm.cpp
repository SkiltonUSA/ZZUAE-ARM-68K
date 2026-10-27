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
#include "aspect.h"
#include "convert_row.h"
#include "profile.h"
#include "../common/rtg_mapping.h"
#ifdef ZZUAE_NEON_EXPERIMENT
extern "C" unsigned zu_neon_available(void);
extern "C" void zu_convert_neon(uint32_t*,const uint16_t*,unsigned,unsigned);
extern "C" void zu_neon_snapshot(uint32_t*);
#endif
static uint32_t published,audio_skip_streak;
static unsigned present_phase;
extern "C" void zzuae_live_event(unsigned,int);
static void barrier() { __asm__ volatile("dsb sy" ::: "memory"); }
static void tlb() {
    uint32_t z=0;
    __asm__ volatile("dsb sy\n mcr p15,0,%0,c8,c7,0\n dsb sy\n isb"::"r"(z):"memory");
}
/* Map only the currently locked, OS-allocated bitmap. The same two-ended
 * ownership challenge and temporary NC/XN mapping are used by ZZDosBox. */
extern "C" unsigned zzuae_direct_convert(void) {
    ZU_PROFILE(4);
    volatile uint8_t *p=uae_shared+UAE_LIVE;
    uint32_t addr=ad_get(p,UL_ADDRESS),pitch=ad_get(p,UL_PITCH);
    uint32_t format=ad_get(p,UL_FORMAT),nonce=ad_get(p,UL_NONCE);
    uint32_t width=ad_get(p,UL_WIDTH),height=ad_get(p,UL_HEIGHT);
    if(!ul_view_valid(width,height))return 6;
    unsigned short xmap[640],ymap[512];
    ul_scale_map(xmap,width,640);ul_scale_map(ymap,height,256);
    uint32_t converted[640];
#ifdef ZZUAE_NEON_EXPERIMENT
    const bool neon=width==640 && zu_neon_available();
    uint32_t before[65] __attribute__((aligned(16))),after[65] __attribute__((aligned(16)));
#endif
    unsigned previous=256;
    uint32_t span=rtg_span_size(addr,pitch,format,width,height),error=0;
    uint32_t base=(uint32_t)uae_shared;
    uint32_t ttbr=(base+0x400000u+16383u)&~16383u;
    uint32_t table=(base+0x41c000u+1023u)&~1023u;
    uint32_t *l1=(uint32_t*)ttbr;
    if((format!=3 && format!=4) || !span || table+4096>base+0x420000u ||
       !rtg_map_size(l1,(uint32_t*)table,table,addr,pitch,format,width,height))return 6;
    tlb();volatile uint8_t *dst=(volatile uint8_t*)addr;
    unsigned neon_rows=0,scalar_rows=0;
#ifdef ZZUAE_NEON_EXPERIMENT
    if(neon)zu_neon_snapshot(before);
#endif
    if(ad_get(dst,0)!=nonce || ad_get(dst,span-4)!=(nonce^0x31415926u))error=7;
    else for(unsigned y=0;y<height;y++) {
        if(uae_stop && uae_stop()){error=2;break;}
        /* Vertical expansion repeats source rows. Convert each once in private
         * cached RAM, then write it to the granted bitmap. Never read back the
         * uncached display mapping and never retain data across frame grants. */
        if(previous!=ymap[y]){
            const uint16_t *src=(const uint16_t*)(gfxvidinfo.drawbuffer.bufmem+ymap[y]*1280);
#ifdef ZZUAE_NEON_EXPERIMENT
            if(neon){zu_convert_neon(converted,src,format,8);neon_rows++;}
            else
#endif
            {ul_prepare_row(converted,src,xmap,width,format);scalar_rows++;}
            previous=ymap[y];
        }
        volatile uint32_t *row=(volatile uint32_t*)(dst+y*pitch);
        for(unsigned x=0;x<width;x++)row[x]=converted[x];
    }
    ad_put(p,UL_NEON_ROWS,ad_get(p,UL_NEON_ROWS)+neon_rows);
    ad_put(p,UL_SCALAR_ROWS,ad_get(p,UL_SCALAR_ROWS)+scalar_rows);
#ifdef ZZUAE_NEON_EXPERIMENT
    if(neon){
        zu_neon_snapshot(after);
        unsigned mismatch=0;
        for(unsigned i=0;i<65;i++)if(before[i]!=after[i])mismatch++;
        ad_put(p,UL_SIMD_CHECKS,ad_get(p,UL_SIMD_CHECKS)+1);
        ad_put(p,UL_SIMD_ERRORS,ad_get(p,UL_SIMD_ERRORS)+mismatch);
        if(mismatch)error=9;
    }
#endif
    /* A requested snapshot is copied only while the producer owns the frame.
     * The host saves it before ACK, so no emulation/final-capture write races it. */
    if(!error && ad_get(p,UL_CAPTURE))
        memcpy((void*)(uae_shared+UAE_FRAME),gfxvidinfo.drawbuffer.bufmem,640*256*2);
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
#include "render_cadence.inc"
#ifdef ZZUAE_EARLY_DRAW
unsigned zu_drawn_frames,zu_skipped_frames;
extern "C" bool zzuae_live_draw_frame(void){
    bool draw=true;
    if(uae_shared && (ad_get(uae_shared,UAE_OPTIONS+4)&(UAE_OPT_LIVE|UAE_OPT_AUDIO))==(UAE_OPT_LIVE|UAE_OPT_AUDIO)){
        draw=zu_render_due(ad_get(uae_shared,UAE_OPTIONS+40),present_phase);
        // Bounded diagnostics must retain their exact final guest framebuffer.
        if(uae_frame_limit && timeframes+1>=uae_frame_limit)draw=true;
        if(!draw)input();
    }
    if(draw)++zu_drawn_frames;else ++zu_skipped_frames;
    return draw;
}
#endif
extern "C" void zzuae_live_present(void) {
    ZU_PROFILE(5);
    if(!uae_shared || !(ad_get(uae_shared,UAE_OPTIONS+4)&UAE_OPT_LIVE))return;
    /* Sound always follows PAL guest time. Lower presentation rates skip
     * drawing/host delivery only; Paula and chipset execute every frame. */
    if(ad_get(uae_shared,UAE_OPTIONS+4)&UAE_OPT_AUDIO){
        unsigned rate=ad_get(uae_shared,UAE_OPTIONS+40);
#ifndef ZZUAE_EARLY_DRAW
        if(!zu_render_due(rate,present_phase)){input();return;}
#endif
        if(ad_get(uae_shared,UA_PACING)){
            unsigned queued=ad_get(uae_shared,UA_WRITE)-ad_get(uae_shared,UA_READ);
            unsigned reserve=ad_get(uae_shared,UA_RESERVE)+queued*UA_FRAMES;
            if(ua_defer_display(published,reserve,audio_skip_streak)){
                ++audio_skip_streak;
                ad_put(uae_shared,UA_DEFERRED,ad_get(uae_shared,UA_DEFERRED)+1);
                input();return;
            }
            audio_skip_streak=0;
        }
    }
    volatile uint8_t *p=uae_shared+UAE_LIVE;
    unsigned direct=ad_get(uae_shared,UAE_OPTIONS+4)&UAE_OPT_DIRECT;
    if(!direct){
        uint16_t *out=(uint16_t*)(uae_shared+UAE_FRAME);
        const uint16_t *src=(const uint16_t*)gfxvidinfo.drawbuffer.bufmem;
        memcpy(out,src,640*256*2);
    }
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
