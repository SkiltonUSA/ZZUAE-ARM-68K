/* Experimental 68000-only adapter. Included in newcpu.cpp so event ordering
 * remains the same as cpu_batch.inc. Cyclone owns instruction exceptions;
 * UAE owns chipset events, interrupt recognition and STOP wake-up. */
#include "Cyclone.h"
static Cyclone cyclone;
extern "C" unsigned cyclone_checkpc(unsigned hostpc) {
    unsigned guest=(hostpc-cyclone.membase)&0xffffff;
    unsigned ptr=(uintptr_t)get_real_address(guest);
    cyclone.membase=ptr-guest;
    return ptr;
}
extern "C" unsigned cyclone_read8(unsigned a) { return get_byte(a&0xffffff); }
extern "C" unsigned cyclone_read16(unsigned a) { return get_word(a&0xffffff); }
extern "C" unsigned cyclone_read32(unsigned a) { return get_long(a&0xffffff); }
extern "C" void cyclone_write8(unsigned a,unsigned char v) { put_byte(a&0xffffff,v); }
extern "C" void cyclone_write16(unsigned a,unsigned short v) { put_word(a&0xffffff,v); }
extern "C" void cyclone_write32(unsigned a,unsigned v) { put_long(a&0xffffff,v); }
extern "C" unsigned cyclone_fetch8(unsigned a) { return cyclone_read8(a); }
extern "C" unsigned cyclone_fetch16(unsigned a) { return cyclone_read16(a); }
extern "C" unsigned cyclone_fetch32(unsigned a) { return cyclone_read32(a); }
static void cyclone_export() {
    memcpy(regs.regs,cyclone.d,32);memcpy(regs.regs+8,cyclone.a,32);
    unsigned sr=CycloneGetSr(&cyclone),oldmask=regs.intmask;
    regs.sr=sr;regs.s=(sr>>13)&1;regs.t1=sr>>15;regs.t0=regs.m=0;regs.intmask=(sr>>8)&7;
    SET_XFLG((sr>>4)&1);SET_NFLG((sr>>3)&1);SET_ZFLG((sr>>2)&1);SET_VFLG((sr>>1)&1);SET_CFLG(sr&1);
    if(regs.s)regs.usp=cyclone.osp;else regs.isp=cyclone.osp;
    regs.pc=(cyclone.pc-cyclone.membase)&0xffffff;
    if(oldmask!=regs.intmask)doint();
    if(cyclone.state_flags&1)m68k_set_stop();
    regs.halted=(cyclone.state_flags&16)!=0;
}
static void cyclone_import() {
    memcpy(cyclone.d,regs.regs,32);memcpy(cyclone.a,regs.regs+8,32);
    MakeSR();CycloneSetSr(&cyclone,regs.sr);
    cyclone.osp=regs.s?regs.usp:regs.isp;
    cyclone.pc=cyclone_checkpc(regs.pc+cyclone.membase);
    if(!regs.stopped)cyclone.state_flags&=~1;
}
static void cyclone_reset_instruction() {
    unsigned pc=(cyclone.pc-cyclone.membase)&0xffffff;
    cyclone_export();regs.pc=pc-2;cpureset();
    cyclone.pc=cyclone_checkpc(pc+cyclone.membase);
}
extern "C" void zzuae_cpu_reset(void) {
    m68k_reset(false);memset(&cyclone,0,sizeof(cyclone));CycloneInit();
    cyclone.jumptab=(uintptr_t)CycloneJumpTab;cyclone.checkpc=cyclone_checkpc;
    cyclone.read8=cyclone.fetch8=cyclone_read8;
    cyclone.read16=cyclone.fetch16=cyclone_read16;
    cyclone.read32=cyclone.fetch32=cyclone_read32;
    cyclone.write8=cyclone_write8;cyclone.write16=cyclone_write16;cyclone.write32=cyclone_write32;
    cyclone.ResetCallback=cyclone_reset_instruction;
    cyclone_import();
}
extern "C" void zzuae_run_batch(unsigned limit,uint32_t *checked,uint32_t *cycles) {
    volatile unsigned count=0,cost=0;
#ifdef ZZ_CYCLONE_EVENT_SYNC
    cyclone_import();
#endif
    while(count<limit && (!uae_frame_limit || timeframes<uae_frame_limit) && !regs.halted) {
        TRY(prb) {
            while(count<limit && (!uae_frame_limit || timeframes<uae_frame_limit) && !regs.halted) {
                do_cycles(cpu_cycles);
                regs.instruction_pc=regs.pc;
#ifndef ZZ_CYCLONE_EVENT_SYNC
                cyclone_import();
#endif
                cyclone.cycles=0;CycloneRun(&cyclone);
#ifdef ZZ_CYCLONE_EVENT_SYNC
                regs.pc=(cyclone.pc-cyclone.membase)&0xffffff;
                regs.s=(cyclone.srh>>5)&1;
                if(regs.spcflags || (cyclone.state_flags&17) || regs.intmask!=(cyclone.srh&7))cyclone_export();
#else
                cyclone_export();
#endif
                cpu_cycles=adjust_cycles((-cyclone.cycles)*(CYCLE_UNIT/2));
                cost=cpu_cycles/(CYCLE_UNIT/2);
                // Trace is already handled by Cyclone, not a second UAE exception.
                unset_special(SPCFLAG_TRACE|SPCFLAG_DOTRACE);
                if(regs.spcflags) {
                    do_specialties(cpu_cycles);
#ifdef ZZ_CYCLONE_EVENT_SYNC
                    cyclone_import();
#endif
                }
                *cycles+=cost;++*checked;++count;cost=0;
            }
        } CATCH(prb) {
#ifdef ZZ_CYCLONE_EVENT_SYNC
            cyclone_export();
#endif
            bus_error();
#ifdef ZZ_CYCLONE_EVENT_SYNC
            cyclone_import();
#endif
            *cycles+=cost;++*checked;++count;cost=0;
        } ENDTRY
    }
#ifdef ZZ_CYCLONE_EVENT_SYNC
    cyclone_export();
#endif
}
