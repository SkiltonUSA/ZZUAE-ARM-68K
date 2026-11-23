#include <cstdint>
#include <cstring>
#include <cassert>
#include <cstdio>
using uae_u8=uint8_t;using uae_u16=uint16_t;using uae_u32=uint32_t;
struct {uint8_t apixels[128];} pixdata;
uint32_t palette[256],*p_acolors=palette;
uint16_t *xlinebuffer;unsigned bplxor,bpland;
int reference(int spix,int dpix,int dpix_end){
 uae_u16 *buf=xlinebuffer;uae_u8 xor_val=bplxor,and_val=bpland;
 if(false){
    } else {
        while (dpix < dpix_end) {
            uae_u32 spix_val;
            uae_u32 out_val;
        
            spix_val = (pixdata.apixels[spix++] ^ xor_val) & and_val;
            out_val = p_acolors[spix_val];
            *((uae_u32 *)&buf[dpix]) = out_val;
            dpix += 2;
        }
    }

    return spix;
}
int candidate(int spix,int dpix,int dpix_end){
 uae_u16 *buf=xlinebuffer;uae_u8 xor_val=bplxor,and_val=bpland;
 if(false){
    } else if (xor_val == 0 && and_val == 255) {
        /* Four independent palette lookups; retain the original two-pixel
         * tail and exact source advance for short or split spans. */
        while (dpix_end - dpix >= 8) {
            uae_u32 a = p_acolors[pixdata.apixels[spix]];
            uae_u32 b = p_acolors[pixdata.apixels[spix + 1]];
            uae_u32 c = p_acolors[pixdata.apixels[spix + 2]];
            uae_u32 d = p_acolors[pixdata.apixels[spix + 3]];
            *((uae_u32 *)&buf[dpix]) = a;
            *((uae_u32 *)&buf[dpix + 2]) = b;
            *((uae_u32 *)&buf[dpix + 4]) = c;
            *((uae_u32 *)&buf[dpix + 6]) = d;
            spix += 4;
            dpix += 8;
        }
        while (dpix < dpix_end) {
            *((uae_u32 *)&buf[dpix]) = p_acolors[pixdata.apixels[spix++]];
            dpix += 2;
        }
    } else {
        while (dpix < dpix_end) {
            uae_u32 spix_val;
            uae_u32 out_val;
        
            spix_val = (pixdata.apixels[spix++] ^ xor_val) & and_val;
            out_val = p_acolors[spix_val];
            *((uae_u32 *)&buf[dpix]) = out_val;
            dpix += 2;
        }
    }

    return spix;
}
int main(){
 alignas(16) uint16_t ref[128],test[128];
 for(unsigned i=0;i<256;i++)palette[i]=(i*7919u) ^ 0xdeadc0deu;
 for(unsigned i=0;i<128;i++)pixdata.apixels[i]=(i*73u+199u)&255;
 unsigned count=0;
 for(bplxor=0;bplxor<256;bplxor++)for(bpland=0;bpland<256;bpland++)
 for(int len=0;len<=65;len++)for(int start=0;start<=6;start+=2){
  memset(ref,0xa5,sizeof(ref));memset(test,0xa5,sizeof(test));
  xlinebuffer=ref;int r=reference(3,start,start+len);
  xlinebuffer=test;int c=candidate(3,start,start+len);
  assert(r==c);assert(!memcmp(ref,test,sizeof(ref)));count++;
 }
 printf("PASS %u exact palette, mask, short-span, odd-tail and guard comparisons\n",count);
}
