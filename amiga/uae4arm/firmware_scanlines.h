/* GPL-3.0-or-later. Xanxi ZZScanlines register interface: 0x100c/0x100e.
 * These FPGA controls are write-only and global. Own them only for a private
 * low-resolution screen, and disable on exit; never invent a saved readback. */
#pragma once
#include <stdint.h>
#define ZU_SCAN_REGISTER 0x100cu
struct zu_scanlines {volatile uint16_t *regs;unsigned mode;};
static const char *const zu_scan_names[]={"Off","Classic","Soft","Gradient"};
static void zu_scan_apply(struct zu_scanlines *s){
    s->regs[1]=0; /* upstream default: odd lines dark */
    s->regs[0]=s->mode;
}
static void zu_scan_begin(struct zu_scanlines *s,volatile uint16_t *regs,
                          unsigned fullscreen,unsigned mode){
    if(!fullscreen)return;
    s->regs=regs;s->mode=mode;zu_scan_apply(s);
}
static void zu_scan_next(struct zu_scanlines *s){
    if(!s->regs)return;
    s->mode=(s->mode+1)%4;zu_scan_apply(s);
}
static void zu_scan_end(struct zu_scanlines *s){
    if(!s->regs)return;
    s->regs[0]=0;s->regs=0;
}
