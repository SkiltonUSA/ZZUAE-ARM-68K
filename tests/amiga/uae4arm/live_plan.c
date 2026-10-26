#include "live.h"
#include <assert.h>
#include <stdio.h>
int main(void) {
    int remainder=0,sum=0;
    assert(ul_room(0,0) && ul_room(63,0) && !ul_room(64,0));
    assert(ul_room(1,0xfffffffeu));
    assert(!ul_room(0x20u,0xffffffe0u));
    /* Slow single-pixel motion must accumulate, including negative movement
     * and reversal. Division of each separate event loses these movements. */
    for(int i=0;i<101;i++)sum+=ul_mouse_half(1,&remainder);
    assert(sum==50 && remainder==1);
    for(int i=0;i<202;i++)sum+=ul_mouse_half(-1,&remainder);
    assert(sum==-50 && remainder==-1);
    for(int i=0;i<101;i++)sum+=ul_mouse_half(1,&remainder);
    assert(sum==0 && remainder==0);
    puts("PASS: bounded input ring wraparound and fractional mouse motion");
}
