#include <assert.h>
#include <stdio.h>
#include "audio_rate.h"
int main(void){
 assert(ua_pcm_valid(22050));assert(ua_pcm_valid(27000));
 assert(ua_pcm_period(3546895,27000,128)==131);assert(ua_pcm_period(3579545,27000,128)==133);assert(ua_pcm_valid(0));assert(!ua_pcm_valid(8000));
 assert(ua_pcm_period(3546895,22050,128)==161);
 assert(ua_pcm_period(3579545,22050,128)==162);
 assert(ua_pcm_period(3546895,0,128)==128);
 assert(ua_pcm_period(3579545,0,128)==128);
 assert(3546895/ua_pcm_period(3546895,22050,128)==22030);
 assert(3579545/ua_pcm_period(3579545,22050,128)==22095);
 puts("PASS 22/27 kHz and original PCM rates, PAL/NTSC Paula period agreement");
}
