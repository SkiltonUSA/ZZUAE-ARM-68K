/* Bounded A500/OCS diagnostic: upstream CPU, chipset and in-memory floppy.
 * No interactive display, host input or audio delivery yet. */
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
#include "profiles.h"
#include "live.h"
#include "audio_wire.h"
#include "audio.h"
extern "C" void zzuae_audio_init(void);
#include "protocol.h"
#include <setjmp.h>
extern "C" { extern jmp_buf uae_fatal;extern int uae_fatal_active; }
extern "C" void fb_heap_init(void*,size_t);
static uint16_t pixels[640*256];
static unsigned char heap[0x800000] __attribute__((aligned(64)));
extern cpuop_func *cpufunctbl[65536];
extern "C" int mesen_test(int verify,MesenResult *r,int (*stop)(),uint32_t (*clock)()) {
    int cancelled=0;
    memset(r,0,sizeof(*r));
    int failure=setjmp(uae_fatal);if(failure){r->errors=failure;return 1;}
    uae_fatal_active=1;uae_stop=stop;
    unsigned options=(!verify && uae_shared)?ad_get(uae_shared,UAE_OPTIONS+4):0;
    if((options&~127u) || ((options&UAE_OPT_DIRECT) && !(options&UAE_OPT_LIVE)))return 10;
    uae_input_mode=options&3u;uae_volatile_write=(options&4u)!=0;
    fb_heap_init(heap,sizeof(heap));
    memset(&currprefs,0,sizeof(currprefs));
    currprefs.cpu_model=68000;currprefs.cpu_compatible=true;
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
    if(!verify) {
        if(!uae_shared)return 9;
        unsigned rom_size=zp_rom_size(profile);
        memcpy(kickmem_bank.baseaddr,(const void*)(uae_shared+UAE_ROM),rom_size);
        if(rom_size==0x40000)memcpy(kickmem_bank.baseaddr+rom_size,kickmem_bank.baseaddr,rom_size);
        kickstart_version=(kickmem_bank.baseaddr[12]<<8)|kickmem_bank.baseaddr[13];map_overlay(0);
        DISK_init();disk_insert_force(0,"wb12.adf",!uae_volatile_write);
        uae_frame_limit=ad_get(uae_shared,UAE_OPTIONS);
        if(!uae_frame_limit)uae_frame_limit=UAE_BOOT_FRAMES;
        if(uae_frame_limit>6000)return 10;
        zzuae_cpu_reset();
        uint32_t start=clock();
        for(unsigned n=0;n<((options&UAE_OPT_LIVE)?200000000u:20000000u) && timeframes<uae_frame_limit;n++) {
            if((n&255)==0 && stop()){
                cancelled=1;break;
            }
            r->cycles+=zzuae_step();r->checked++;
            if(regs.halted){r->errors=regs.halted;return 3;}
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
    r->actual_pc=m68k_getpci();r->actual_regs=timeframes;
    (void)verify;(void)stop;(void)clock;
    uae_fatal_active=0;return cancelled?2:0;
}
