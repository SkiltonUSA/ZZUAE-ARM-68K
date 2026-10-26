#!/usr/bin/env python3
"""Create an original 256 KiB 68000/Paula diagnostic ROM, not a Kickstart image.
Version words only satisfy this prototype's media preflight. No OS code included.
"""
import struct,sys
from pathlib import Path
rom=bytearray(262144)
struct.pack_into('>II',rom,0,0x20000,0xfc0040)
struct.pack_into('>HH',rom,12,34,5)
program=bytearray.fromhex('13fc000200bfe001') # CIA-A: remove reset ROM overlay
def movew(value,address):program.extend(struct.pack('>HHI',0x33fc,value,address))
for i in range(16):movew(0x2020 if i<8 else 0xe0e0,0x2000+i*2)
for channel in range(2):
 reg=0xdff0a0+channel*16
 for offset,value in [(0,0),(2,0x2000),(4,16),(6,200+channel*200),(8,64)]:movew(value,reg+offset)
movew(0x030,0xdff180)
movew(0x8203,0xdff096)
program.extend(bytes.fromhex('60fe'))
rom[64:64+len(program)]=program
s=0
for (word,) in struct.iter_unpack('>I',rom):
 s+=word;s=(s&0xffffffff)+(s>>32)
struct.pack_into('>I',rom,len(rom)-4,(~s)&0xffffffff)
Path(sys.argv[1]).write_bytes(rom)
print('Created original Paula stereo diagnostic ROM:',sys.argv[1])
