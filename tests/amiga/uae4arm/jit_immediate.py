#!/usr/bin/env python3
"""All ARM rotated-immediate patterns through the adapted upstream encoder."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[3]
p=root/'.context/amiga/uae4arm/jit-probe/platform-audit/codegen_arm.h'
s=p.read_text();start=s.index('#define IMM32(c)');end=s.index('\n\n',start);macro=s[start:end]
assert '(uae_u32)(c)' in macro
with tempfile.TemporaryDirectory() as d:
 f=Path(d)/'test.cpp';binary=Path(d)/'test'
 f.write_text('#include <stdint.h>\n#include <assert.h>\n#include <stdio.h>\ntypedef uint32_t uae_u32;\n'+macro+r'''
static uint32_t ror(uint32_t v,unsigned n){return n?(v>>n)|(v<<(32-n)):v;}
static uint32_t decode(uint32_t v){assert(v<4096);return ror(v&255,2*(v>>8));}
int main(){
 assert(decode(IMM32(0x40000000))==0x40000000u);
 assert(decode(IMM32(0x20000000))==0x20000000u);
 assert(decode(IMM32(0x10000000))==0x10000000u);
 for(unsigned rot=0;rot<16;rot++)for(unsigned bits=0;bits<256;bits++){
  uint32_t v=ror(bits,2*rot);assert(decode(IMM32(v))==v);
  int32_t signed_v=(int32_t)v;assert(decode(IMM32(signed_v))==v);
 }
 puts("PASS upstream JIT IMM32: all 4096 rotated-immediate patterns, signed and unsigned operands; high flag constants; UBSan");
}
''')
 subprocess.run(['clang++','-std=c++11','-Wall','-Wextra','-Werror','-fsanitize=undefined',str(f),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
