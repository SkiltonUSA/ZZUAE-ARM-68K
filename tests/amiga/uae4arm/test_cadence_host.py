#!/usr/bin/env python3
"""Compile the transformed host setup and exercise sound-off/on rate selection."""
from pathlib import Path
import subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from prepare_uae4arm_cadence import host_cadence
source='''#include <assert.h>
#define UAE_OPT_LIVE 8
static unsigned frame_period,display_rate,audio_mode,ntsc_mode,boot_options;
static int setup(void){
        if(audio_mode){
            if(!(boot_options&UAE_OPT_LIVE))return 20;
            display_rate=frame_period==40000?25:frame_period==33334?30:frame_period==20000?50:frame_period==16667?60:ntsc_mode?60:50;
            frame_period=0;
        }
 return 0;
}
int main(void){
 unsigned periods[]={40000,33334,20000,16667,0};
 unsigned rates[]={25,30,50,60,0};
 for(unsigned ntsc=0;ntsc<2;++ntsc)for(unsigned audio=0;audio<2;++audio)for(unsigned n=0;n<5;++n){
  frame_period=periods[n];display_rate=50;audio_mode=audio;ntsc_mode=ntsc;boot_options=UAE_OPT_LIVE;
  assert(!setup());
  unsigned hz=ntsc?60:50,rate=rates[n];
  if(audio){assert(!frame_period);assert(display_rate==(rate?rate:hz));}
  else {if(rate>hz)rate=hz;assert(display_rate==rate);assert(frame_period==(rate?(1000000u+rate-1)/rate:0));}
 }
 audio_mode=1;boot_options=0;assert(setup()==20);
 return 0;
}
'''
prepared=host_cadence(source)
assert host_cadence(prepared)==prepared
with tempfile.TemporaryDirectory() as directory:
 p=Path(directory);(p/'test.c').write_text(prepared)
 subprocess.run(['clang','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(ROOT/'amiga/uae4arm'),str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
print('PASS transformed host: PAL/NTSC, sound off/on, 25/30/50/60/MAX, LIVE refusal, idempotence')
