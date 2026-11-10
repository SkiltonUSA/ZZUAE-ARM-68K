#!/usr/bin/env python3
"""Original AGA 256-colour/8-bitplane fixture. Contains no Commodore ROM code."""
import struct,sys
from pathlib import Path
height=240 if "--ntsc" in sys.argv else 256
plane_bytes=height*40
rom=bytearray(524288)
struct.pack_into('>II',rom,0,0x1ffff0,0xf80040)
struct.pack_into('>HH',rom,12,40,68) # diagnostic media profile only
code=bytearray.fromhex('13fc000200bfe001')
def w(v,a):code.extend(struct.pack('>HHI',0x33fc,v,a))
w(0x7fff,0xdff096);w(0x7fff,0xdff09a)
# Copy original planar artwork from ROM to Chip RAM.
code.extend(struct.pack('>HIHIHH',0x207c,0xf90000,0x227c,0x20000,0x303c,plane_bytes*2-1))
code.extend(bytes.fromhex('22d851c8fffc'))
w(0x1581 if height==240 else 0x2c81,0xdff08e);w(0x05c1 if height==240 else 0x2cc1,0xdff090)
w(0x0038,0xdff092);w(0x00d0,0xdff094)
w(0,0xdff1fc);w(0,0xdff108);w(0,0xdff10a);w(0,0xdff102)
# Reset bitplane pointers every frame using an original Copper list.
for plane in range(8):
 addr=0x20000+plane*plane_bytes;at=0x10000+plane*8
 w(0xe0+plane*4,at);w(addr>>16,at+2)
 w(0xe2+plane*4,at+4);w(addr&65535,at+6)
w(0xffff,0x10040);w(0xfffe,0x10042)
w(1,0xdff080);w(0,0xdff082);w(0,0xdff088)
for bank in range(8):
 for low in (0,1):
  w(bank<<13 | low<<9,0xdff106)
  for i in range(32):
   c=bank*32+i
   r=(c>>5)*255//7;g=((c>>2)&7)*255//7;b=(c&3)*255//3
   w(((r&15)<<8)|((g&15)<<4)|(b&15) if low else ((r>>4)<<8)|((g>>4)<<4)|(b>>4),0xdff180+2*i)
w(0,0xdff106);w(0x0211,0xdff100);w(0x8380,0xdff096)
code.extend(bytes.fromhex('60fe'))
rom[64:64+len(code)]=code
for plane in range(8):
 for y in range(height):
  for x in range(320):
   color=(x//20)+(y//(height//16))*16
   if color&(1<<plane):rom[65536+plane*plane_bytes+y*40+x//8]|=128>>(x&7)
s=0
for word, in struct.iter_unpack('>I',rom):s+=word;s=(s&0xffffffff)+(s>>32)
struct.pack_into('>I',rom,len(rom)-4,~s&0xffffffff)
Path(sys.argv[1]).write_bytes(rom)
print('Original AGA fixture created:',sys.argv[1])
