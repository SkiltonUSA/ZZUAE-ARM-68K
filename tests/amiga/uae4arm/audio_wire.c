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
 for(unsigned policy=1;policy<=2;policy++){
  assert(!ua_defer_display(0,0,0,policy));
  assert(ua_defer_display(1,0,0,policy));
  assert(ua_defer_display(1,ua_reserve_blocks(policy)*UA_FRAMES-1,2,policy));
  assert(!ua_defer_display(1,ua_reserve_blocks(policy)*UA_FRAMES,0,policy));
  assert(!ua_defer_display(1,0,3,policy));
 }
 assert(ua_host_slots(1)==4&&ua_prebuffer(1)==2&&ua_reserve_blocks(1)==3);
 assert(ua_host_slots(2)==8&&ua_prebuffer(2)==4&&ua_reserve_blocks(2)==5);
 puts("PASS: PCM BE stereo encoding, signed extrema, ring wrap/full and DDR bound");
}
