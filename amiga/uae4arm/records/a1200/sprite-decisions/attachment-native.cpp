#include <cstdint>
#include <cstring>
#include <cstdio>
using uae_u8=uint8_t;using uae_u32=uint32_t;
union {uae_u8 bytes[1024];uae_u32 words[256];} spixstate;
void reference(int word_offs,int width,uae_u8 state){int i;		uae_u8 *stb1 = spixstate.bytes + word_offs;	
		for (i = 0; i < width; i += 8) {
			stb1[0] |= state;
			stb1[1] |= state;
			stb1[2] |= state;
			stb1[3] |= state;
			stb1[4] |= state;
			stb1[5] |= state;
			stb1[6] |= state;
			stb1[7] |= state;
			stb1 += 8;
  	}}
void candidate(int word_offs,int width,uae_u8 state){int i;/* Use the existing word view only when the byte offset is aligned. */
        if ((word_offs & 3) == 0) {
            uae_u32 *words = spixstate.words + word_offs / 4;
            uae_u32 packed = (uae_u32)state * 0x01010101u;
            for (i = 0; i < width; i += 8) {
                words[0] |= packed;
                words[1] |= packed;
                words += 2;
            }
        } else {
		uae_u8 *stb1 = spixstate.bytes + word_offs;	
		for (i = 0; i < width; i += 8) {
			stb1[0] |= state;
			stb1[1] |= state;
			stb1[2] |= state;
			stb1[3] |= state;
			stb1[4] |= state;
			stb1[5] |= state;
			stb1[6] |= state;
			stb1[7] |= state;
			stb1 += 8;
  	}
        }
}
static uint32_t r=0x2917bb13;
uint32_t rnd(){r^=r<<13;r^=r>>17;r^=r<<5;return r;}
int main(){
 unsigned fast=0;
 for(unsigned t=0;t<200000;t++){
  uint8_t before[1024],expected[1024];for(auto &b:before)b=rnd();
  int offset=16+rnd()%16,width=4<<(rnd()%7);uint8_t state=3u<<(rnd()%4*2);
  memcpy(spixstate.bytes,before,1024);reference(offset,width,state);memcpy(expected,spixstate.bytes,1024);
  memcpy(spixstate.bytes,before,1024);candidate(offset,width,state);
  if(memcmp(expected,spixstate.bytes,1024)){printf("FAIL %u\n",t);return 1;}
  fast+=(offset&3)==0;
 }
 printf("PASS 200000 attachment comparisons, aligned=%u; overlapping masks, guards and all offsets\n",fast);
}
