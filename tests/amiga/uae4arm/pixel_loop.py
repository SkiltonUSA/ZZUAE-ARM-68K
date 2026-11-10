"""Compare prepared AGA pixel loops against the pinned upstream implementation."""
from pathlib import Path
import subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from prepare_uae4arm_pixels import aga_pixel_loop
base=ROOT/'.context/uae4arm-review/src/linetoscr.cpp'
with tempfile.TemporaryDirectory(dir=ROOT/'.context') as temp:
 p=Path(temp);candidate=p/'linetoscr.cpp'
 candidate.write_text(aga_pixel_loop(base.read_text()))
 def extract(path,name):
  s=path.read_text();start=s.index('static int NOINLINE linetoscr_16_stretch1_aga');end=s.index('\n#endif',start);s=s[start:end]
  token='    } else if (xor_val == 0 && and_val == 255)' if name=='candidate' else '    } else {'
  start=s.index(token,s.index('} else if (bplehb)'))
  return f'''int {name}(int spix,int dpix,int dpix_end){{
  uae_u16 *buf=xlinebuffer;uae_u8 xor_val=bplxor,and_val=bpland;
  if(false){{
 '''+s[start:]
 s='''#include <cstdint>
 #include <cstring>
 #include <cassert>
 #include <cstdio>
 using uae_u8=uint8_t;using uae_u16=uint16_t;using uae_u32=uint32_t;
 struct {uint8_t apixels[128];} pixdata;
 uint32_t palette[256],*p_acolors=palette;
 uint16_t *xlinebuffer;unsigned bplxor,bpland;
 '''+extract(base,'reference')+'\n'+extract(candidate,'candidate')+'''
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
  printf("PASS %u exact palette, mask, short-span, odd-tail and guard comparisons\\n",count);
 }
 '''
 (p/'test-pixels.cpp').write_text(s)
 subprocess.run(['clang++','-O2','-fsanitize=address,undefined',str(p/'test-pixels.cpp'),'-o',str(p/'test-pixels')],check=True)
 subprocess.run([str(p/'test-pixels')],check=True)
