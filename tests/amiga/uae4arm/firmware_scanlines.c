#include "firmware_scanlines.h"
#include <assert.h>
#include <stdio.h>
int main(void){
    volatile uint16_t regs[2]={99,99};
    struct zu_scanlines s={0};
    zu_scan_begin(&s,regs,0,2);
    zu_scan_next(&s);zu_scan_end(&s);
    assert(regs[0]==99 && regs[1]==99); /* windows never change global state */
    zu_scan_begin(&s,regs,1,2);
    assert(regs[0]==2 && regs[1]==0);
    for(unsigned i=0;i<5;i++){
        zu_scan_next(&s);assert(regs[0]==(3+i)%4 && regs[1]==0);
    }
    zu_scan_end(&s);assert(regs[0]==0 && !s.regs);
    regs[0]=99;zu_scan_end(&s);assert(regs[0]==99); /* cleanup once */
    puts("PASS: firmware mode cycle, fullscreen-only writes, disable on exit");
}
