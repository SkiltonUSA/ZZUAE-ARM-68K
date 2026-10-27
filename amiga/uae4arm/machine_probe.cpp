/* Bounded OCS/ECS player: upstream CPU/chipset with host display, input and audio. */
#include "sysconfig.h"
#include "sysdeps.h"
#include "options.h"
#include "memory.h"
#include "custom.h"
#include "newcpu.h"
#include "events.h"
#include "xwin.h"
#include "drawing.h"
#include "bench.h"
#include "inputdevice.h"
#include "disk.h"
#include "machine.h"
#include "jit_config.h"
#include "md-pandora/rpt.h"
#include "profiles.h"
#include "profile.h"
#include "live.h"
#include "audio_wire.h"
#ifdef ZZUAE_JIT_CACHE_TEST
#include "jit_cache.h"
#endif
#include "audio.h"
#ifdef ZZUAE_GUEST_JIT
extern "C" void zzuae_run_accelerated(unsigned,uint32_t*,uint32_t*);
extern "C" int zz_jit_fault_install();
extern "C" void zz_jit_fault_restore();
extern unsigned zz_jit_translated,zz_jit_fallback;
unsigned zzuae_engine;
#endif
#ifdef ZZUAE_GUEST_FPU
extern "C" unsigned zu_neon_available(void);
extern "C" void zu_neon_snapshot(uint32_t*);
extern "C" void zu_fpu_restore(uint32_t*);
extern "C" void zu_fpu_clear(void);
extern unsigned zz_fpu_instructions,zz_fpu_data_ops,zz_fpu_saves,zz_fpu_restores;
static uint32_t zu_saved_fp[65] __attribute__((aligned(16)));
#endif
extern "C" void zzuae_audio_init(void);
#include "protocol.h"
#include <setjmp.h>
extern "C" { extern jmp_buf uae_fatal;extern int uae_fatal_active; }
extern "C" void fb_heap_init(void*,size_t);
static uint16_t pixels[640*256];
static unsigned char heap[0x800000] __attribute__((aligned(64)));
extern cpuop_func *cpufunctbl[65536];
#ifdef ZZUAE_GUEST_FPU
#include "fpu_verify.inc"
#endif
static int run_machine(int verify,MesenResult *r,int (*stop)(),uint32_t (*clock)()) {
    int cancelled=0;
    uae_stop=stop;
#ifdef ZZUAE_JIT_CACHE_TEST
    unsigned cache_error=zzuae_jit_cache_selftest();
    if(cache_error){r->errors=cache_error;return 13;}
#endif
    unsigned options=(!verify && uae_shared)?ad_get(uae_shared,UAE_OPTIONS+4):0;
    if((options&~127u) || ((options&UAE_OPT_DIRECT) && !(options&UAE_OPT_LIVE)))return 10;
    uae_input_mode=options&3u;uae_volatile_write=(options&4u)!=0;
    fb_heap_init(heap,sizeof(heap));
    memset(&currprefs,0,sizeof(currprefs));
    currprefs.cpu_model=68000;currprefs.cpu_compatible=true;
#ifdef ZZUAE_GUEST_JIT
    unsigned engine=(!verify && uae_shared)?ad_get(uae_shared,UAE_OPTIONS+44):0;
    #ifdef ZZUAE_GUEST_FPU
    if(verify)engine=2;
    #endif
    if(engine>2)return 10;
    zzuae_engine=engine;
    if(engine){currprefs.cpu_model=68020;currprefs.cpu_compatible=false;currprefs.cachesize=ZU_JIT_CACHE_KIB;}
#endif
#ifdef ZZUAE_GUEST_FPU
    unsigned fpu=(!verify && uae_shared)?ad_get(uae_shared,UAE_OPTIONS+72):0;
    if(verify){fpu=1;ad_put(uae_shared,UAE_OPTIONS+72,1);}
    if(fpu>1 || (fpu && !zzuae_engine))return 10;
    currprefs.fpu_model=fpu?68882:0;currprefs.compfpu=false;
#endif
    currprefs.address_space_24=true;
    unsigned selected=(!verify && uae_shared)?ad_get(uae_shared,UAE_OPTIONS+20):0;
    if(selected>4)return 10;
    unsigned profile=selected?selected-1:ZP_LEGACY;
    currprefs.chipmem_size=zp_chip(profile,(options&32u)!=0);
    currprefs.bogomem_size=zp_slow(profile,(options&32u)!=0);
    currprefs.cs_compatible=profile==ZP_A1000?CP_A1000:profile==ZP_A500PLUS?CP_A500P:profile==ZP_A600?CP_A600:CP_A500;
    built_in_chipset_prefs(&currprefs);
    if(profile==ZP_A1000){currprefs.cs_df0idhw=0;currprefs.cs_rtc=0;}
    currprefs.chipset_mask=(profile==ZP_A500PLUS || profile==ZP_A600)?CSMASK_ECS_AGNUS|CSMASK_ECS_DENISE:0;
    currprefs.nr_floppies=1;currprefs.floppy_speed=100;currprefs.floppy_read_only=!uae_volatile_write;
    for(unsigned d=1;d<4;d++)currprefs.floppyslots[d].dfxtype=-1;
    currprefs.gfx_resolution=verify?0:1;currprefs.gfx_vresolution=0;
    currprefs.gfx_framerate=0;
    // Silent mode retains Paula DMA/interrupt behavior.
    currprefs.produce_sound=(options&UAE_OPT_AUDIO)?2:1;
    currprefs.sound_stereo=1;currprefs.sound_stereo_separation=10;
    if(options&UAE_OPT_AUDIO){
        currprefs.sound_freq=ad_get(uae_shared,UA_RATE);
        if(currprefs.sound_freq<20000 || currprefs.sound_freq>48000)return 12;
    }
    changed_prefs=currprefs;syncbase=1000000;
    gfxvidinfo.drawbuffer.bufmem=(uae_u8*)pixels;
    gfxvidinfo.drawbuffer.outwidth=verify?320:640;gfxvidinfo.drawbuffer.outheight=256;
    gfxvidinfo.drawbuffer.rowbytes=verify?640:1280;gfxvidinfo.drawbuffer.pixbytes=2;
    alloc_colors64k(5,6,5,11,5,0,0);
    // UAE's first FPS delta starts at zero. A board-uptime high bit otherwise
    // discards that first guest frame as a negative host-time delta.
    g_uae_epoch=zzuae_clock_us();
    inputdevice_init();memory_init();init_m68k();custom_init();custom_reset(true,false);
    if(options&UAE_OPT_AUDIO)zzuae_audio_init();
    /* Verify every mapped Chip RAM bank and detect aliases at expansion edges. */
    map_overlay(1); /* Reset overlay otherwise reads the ROM at address zero. */
    for(unsigned a=0;a<currprefs.chipmem_size;a+=0x10000){put_long(a,a^0x1234abcd);put_long(a+0xfffc,a^0xdead4321);}
    for(unsigned a=0;a<currprefs.chipmem_size;a+=0x10000)
        if(get_long(a)!=(a^0x1234abcdu) || get_long(a+0xfffc)!=(a^0xdead4321u))return 11;
    for(unsigned a=0;a<currprefs.chipmem_size;a+=0x10000){put_long(a,0);put_long(a+0xfffc,0);}
    if(currprefs.bogomem_size) {
        /* Exercise the CPU's mapped bank, including aliasing, before guest boot. */
        unsigned chip_before=get_long(0x100);
        for(unsigned a=0xc00000;a<0xc80000;a+=4)put_long(a,a^0xa55a1234u);
        for(unsigned a=0xc00000;a<0xc80000;a+=4)
            if(get_long(a)!=(a^0xa55a1234u))return 11;
        if(get_long(0x100)!=chip_before)return 11;
        for(unsigned a=0xc00000;a<0xc80000;a+=4)put_long(a,0);
    }
    if(uae_shared){
        ad_put(uae_shared,UAE_OPTIONS+8,currprefs.chipmem_size);
        ad_put(uae_shared,UAE_OPTIONS+12,currprefs.bogomem_size);
        ad_put(uae_shared,UAE_OPTIONS+16,1);
        ad_put(uae_shared,UAE_OPTIONS+24,currprefs.chipset_mask);
        ad_put(uae_shared,UAE_OPTIONS+28,currprefs.cs_compatible);
        ad_put(uae_shared,UAE_OPTIONS+32,currprefs.cs_ciaoverlay);
    }
    #ifdef ZZUAE_GUEST_FPU
    if(verify)return zu_fpu_verify(r,stop);
    #endif
    if(!verify) {
        if(!uae_shared)return 9;
        unsigned rom_size=zp_rom_size(profile);
        memcpy(kickmem_bank.baseaddr,(const void*)(uae_shared+UAE_ROM),rom_size);
        if(rom_size==0x40000)memcpy(kickmem_bank.baseaddr+rom_size,kickmem_bank.baseaddr,rom_size);
        kickstart_version=(kickmem_bank.baseaddr[12]<<8)|kickmem_bank.baseaddr[13];map_overlay(0);
        DISK_init();disk_insert_force(0,"wb12.adf",!uae_volatile_write);
        uae_frame_limit=ad_get(uae_shared,UAE_OPTIONS);
        if(!uae_frame_limit && !(options&UAE_OPT_LIVE))return 10;
        if(uae_frame_limit>6000)return 10;
        zzuae_cpu_reset();
#ifdef ZZUAE_GUEST_JIT
        if(engine)set_cache_state(1);
#endif
        uint32_t start=clock();
        const unsigned instruction_limit=(options&UAE_OPT_LIVE)?200000000u:20000000u;
        while(!uae_frame_limit || (r->checked<instruction_limit && timeframes<uae_frame_limit)) {
            if(stop()){cancelled=1;break;}
            unsigned remaining=uae_frame_limit?instruction_limit-r->checked:256;
#ifdef ZZUAE_GUEST_JIT
            if(engine)zzuae_run_accelerated(remaining<256?remaining:256,&r->checked,&r->cycles);
            else
#endif
            zzuae_run_batch(remaining<256?remaining:256,&r->checked,&r->cycles);
            if(regs.halted){r->errors=regs.halted;r->actual_pc=m68k_getpc();r->actual_regs=timeframes;r->mismatch=regs.opcode;return 3;}
        }
        r->ticks=clock()-start;
    } else {
    map_overlay(1);
    const uint16_t program[]={0x33fc,0x0f00,0x00df,0xf180,0x60fe};
    for(unsigned i=0;i<5;i++)put_word(0x100+2*i,program[i]);
    regs.s=1;regs.intmask=7;m68k_setpci(0x100);regs.ir=get_word(0x100);regs.irc=get_word(0x102);
    for(unsigned n=0;n<100000;n++) {
        if((n&255)==0 && stop())return 2;
        uae_u32 cycles=cpufunctbl[regs.ir](regs.ir);
        do_cycles(cycles);r->cycles+=cycles/(CYCLE_UNIT/2);r->checked++;
    }
    }
    unsigned count=gfxvidinfo.drawbuffer.outwidth*256;
    for(unsigned n=0;n<count;n++)r->hash=r->hash*31+pixels[n];
    if(uae_shared)memcpy((void*)(uae_shared+UAE_FRAME),pixels,count*2);
    r->actual_pc=m68k_getpc();r->actual_regs=timeframes;
    (void)verify;(void)stop;(void)clock;
#ifdef ZZUAE_NEON_BITPLANES
    extern unsigned zu_bitplanes_neon_rows,zu_bitplanes_scalar_rows;
    if(uae_shared){
        ad_put(uae_shared,UAE_OPTIONS+56,zu_bitplanes_neon_rows);
        ad_put(uae_shared,UAE_OPTIONS+60,zu_bitplanes_scalar_rows);
    }
#endif
#ifdef ZZUAE_EARLY_DRAW
    extern unsigned zu_drawn_frames,zu_skipped_frames;
    if(uae_shared){
        ad_put(uae_shared,UAE_OPTIONS+64,zu_drawn_frames);
        ad_put(uae_shared,UAE_OPTIONS+68,zu_skipped_frames);
    }
#endif
    zu_profile_finish();return cancelled?2:0;
}

/* The fatal boundary must outlive both execution and compiler cleanup. A fatal
 * exit is terminal for this worker; the outer host still restores/reset Core1. */
extern "C" int mesen_test(int verify,MesenResult *r,int (*stop)(),uint32_t (*clock)()) {
    memset(r,0,sizeof(*r));
    int result;
#ifdef ZZUAE_GUEST_FPU
    if(!zu_neon_available()){r->errors=97;return 1;}
    zu_neon_snapshot(zu_saved_fp);zu_fpu_clear();
#endif
    int failure=setjmp(uae_fatal);
    if(failure){r->errors=failure;result=1;}
    else {
        uae_fatal_active=1;
#ifdef ZZUAE_GUEST_JIT
        if(!zz_jit_fault_install()){r->errors=98;result=1;}
        else {
#endif
            result=run_machine(verify,r,stop,clock);
#ifdef ZZUAE_GUEST_JIT
            if(!result || result==2)compiler_exit();
        }
#endif
    }
#ifdef ZZUAE_GUEST_JIT
    zz_jit_fault_restore();
    ad_put(uae_shared,UAE_OPTIONS+48,zz_jit_translated);
    ad_put(uae_shared,UAE_OPTIONS+52,zz_jit_fallback);
#endif
    uae_fatal_active=0;
#ifdef ZZUAE_GUEST_FPU
    ad_put(uae_shared,UAE_OPTIONS+76,zz_fpu_instructions);
    ad_put(uae_shared,UAE_OPTIONS+84,zz_fpu_data_ops);
    ad_put(uae_shared,UAE_OPTIONS+88,zz_fpu_saves);
    ad_put(uae_shared,UAE_OPTIONS+92,zz_fpu_restores);
    zu_fpu_restore(zu_saved_fp);
    uint32_t restored[65] __attribute__((aligned(16)));
    zu_neon_snapshot(restored);
    unsigned mismatch=0;
    for(unsigned i=0;i<65;i++)if(restored[i]!=zu_saved_fp[i])++mismatch;
    ad_put(uae_shared,UAE_OPTIONS+80,mismatch);
    if(mismatch){r->errors=96;result=1;}
#endif
    return result;
}
