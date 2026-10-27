#include "audio_wire.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 uint8_t pcm[4];
 ua_pcm(pcm,0x8000,0x7fff);
 assert(pcm[0]==0x80&&pcm[1]==0&&pcm[2]==0x7f&&pcm[3]==0xff);
 ua_pcm(pcm,0xffff,0);
 assert(pcm[0]==255&&pcm[1]==255&&pcm[2]==0&&pcm[3]==0);
 assert(ua_room(0,0)&&!ua_room(4,0));
 assert(ua_room(0,0xfffffffe)&&!ua_room(0,0xfffffffc));
 assert(UA_DATA+UA_SLOTS*UA_STRIDE<=0x490000);
 assert(!ua_defer_display(0,0,0));
 assert(ua_defer_display(1,0,0)&&ua_defer_display(1,3071,2));
 assert(!ua_defer_display(1,3072,0)&&!ua_defer_display(1,0,3));
 puts("PASS: PCM BE stereo encoding, signed extrema, ring wrap/full and DDR bound");
}
