#include <cstdint>
#include <cstdio>
#include <cstdlib>
static uint32_t extract(uint32_t lo,uint32_t hi,unsigned shift,unsigned width){
 const uint32_t mask=0xffffu>>(16-width);
 if(shift>=32)return (hi>>(shift-32))&mask;
 uint32_t value=lo>>shift;
 if(shift && shift+width>32)value|=hi<<(32-shift);
 return value&mask;
}
int main(){
 uint32_t rng=0x28174395;unsigned count=0;
 for(unsigned shift=0;shift<64;shift++)for(unsigned bits=0;bits<=16;bits++)for(unsigned n=0;n<4096;n++){
  rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;uint32_t lo=rng;
  rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;uint32_t hi=rng;
  uint32_t expected=(uint64_t(hi)<<32|lo)>>shift&((1u<<bits)-1);
  if(extract(lo,hi,shift,bits)!=expected)std::abort();
  ++count;
 }
 std::printf("PASS %u bit-extraction comparisons, shifts 0..63, widths 0..16\n",count);
}
