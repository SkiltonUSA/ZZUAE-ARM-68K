#!/usr/bin/env python3
"""Compile ZZUAE source PNG to embedded MUI art and a Workbench ColorIcon."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
def prepare_png(master,name,out):
 """Convert supplied artwork to embedded palette/planar resources, preserving alpha."""
 out.mkdir(parents=True,exist_ok=True)
 for size,kind in [(64,'icon'),(80,'sidebar'),(128,'splash')]:
  raw=subprocess.check_output(['magick',str(master),'-resize',f'{size}x{size}!','+dither','-colors','127','-depth','8','rgba:-'])
  palette=[(0,0,0)];lookup={};indices=[]
  for at in range(0,len(raw),4):
   r,g,b,a=raw[at:at+4];rgb=(r,g,b)
   if a<128:indices.append(0);continue
   if rgb not in lookup:lookup[rgb]=len(palette);palette.append(rgb)
   indices.append(lookup[rgb])
  assert len(palette)<=128;palette += [(0,0,0)]*(128-len(palette));depth=7
  body=bytearray(size*(size//8)*depth);planes=[0]*(2*size*(size//16))
  for y in range(size):
   for x in range(size):
    v=indices[y*size+x]
    for bit in range(depth):
     if v&(1<<bit):body[(y*depth+bit)*(size//8)+x//8]|=1<<(7-x%8)
    # Classic fallback retains a readable silhouette on old icon libraries.
    r,g,b=palette[v];classic=0 if not v else 1 if r+g+b<384 else 2
    for bit in range(2):
     if classic&(1<<bit):planes[bit*size*(size//16)+y*(size//16)+x//16]|=1<<(15-x%16)
  if kind=='icon':
   text='#define ICON_COLOR 1\nstatic UWORD icon_planes[]={'+','.join(map(str,planes))+'};\n'
   text+='static UBYTE icon_pixels[]={'+','.join(map(str,indices))+'};\n'
   text+='static struct ColorRegister icon_palette[]={'+','.join('{'+','.join(map(str,c))+'}'for c in palette)+'};\n'
  else:
   text=f'#define {kind.upper()}_DEPTH {depth}\nstatic const UBYTE {kind}_body[]={{'+','.join(map(str,body))+'};\n'
   text+=f'static const ULONG {kind}_colours[]={{'+','.join(hex(c*0x01010101)for rgb in palette for c in rgb)+'};\n'
  (out/(kind+'-art.h')).write_text('/* Generated from supplied '+master.name+'; do not edit. */\n'+text)
 subprocess.run(['magick',str(master),'-resize','256x256',str(out/(name+'.png'))],check=True)

if __name__=='__main__':
 prepare_png(ROOT/'amiga/uae4arm/assets/zzuae-logo.png','ZZUAE',ROOT/'.context/amiga/uae4arm/launcher')
