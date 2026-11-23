from pathlib import Path
import subprocess
p=Path('.context/amiga/uae4arm/a1200/sprite-decisions');s=(p.parent/'gameplay/build-pixel4/src/custom.cpp').read_text()
a=s.index('\t\tuae_u8 *stb1 = spixstate.bytes + word_offs;');z=s.index('\n\t\te->has_attached = 1;',a);old=s[a:z]
new=(p/'attachment.inc').read_text().replace('ORIGINAL',old)
source='''#include <cstdint>
#include <cstring>
#include <cstdio>
using uae_u8=uint8_t;using uae_u32=uint32_t;
union {uae_u8 bytes[1024];uae_u32 words[256];} spixstate;
void reference(int word_offs,int width,uae_u8 state){int i;'''+old+'''}
void candidate(int word_offs,int width,uae_u8 state){int i;'''+new+'''}
static uint32_t r=0x2917bb13;
uint32_t rnd(){r^=r<<13;r^=r>>17;r^=r<<5;return r;}
int main(){
 unsigned fast=0;
 for(unsigned t=0;t<200000;t++){
  ua e_dummy;
  uint8_t before[1024],expected[1024];for(auto &b:before)b=rnd();
  int offset=16+rnd()%16,width=4<<(rnd()%7);uint8_t state=3u<<(rnd()%4*2);
  memcpy(spixstate.bytes,before,1024);reference(offset,width,state);memcpy(expected,spixstate.bytes,1024);
  memcpy(spixstate.bytes,before,1024);candidate(offset,width,state);
  if(memcmp(expected,spixstate.bytes,1024)){printf("FAIL %u\\n",t);return 1;}
  fast+=(offset&3)==0;
 }
 printf("PASS 200000 attachment comparisons, aligned=%u; overlapping masks, guards and all offsets\\n",fast);
}
'''.replace('  ua e_dummy;\n','')
(p/'attachment-native.cpp').write_text(source)
subprocess.run(['clang++','-O2','-std=c++11','-fsanitize=address,undefined','-fno-sanitize-recover=all',str(p/'attachment-native.cpp'),'-o',str(p/'attachment-native')],check=True)
subprocess.run([str(p/'attachment-native')],check=True)
