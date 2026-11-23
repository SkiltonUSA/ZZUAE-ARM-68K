#!/usr/bin/env python3
"""Exercise the real pause-drain API with delayed device completion and failure."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[3]
s=(root/'amiga/uae4arm/audio_host.c').read_text()
s=s[s.index('int ua_audio_host_pause_drain(void)'):s.index('int ua_audio_host_close(void)')]
fixture=r'''
#include <assert.h>
#include <stdio.h>
typedef unsigned ULONG;
static unsigned audio_opened,audio_drained,audio_force,now,queued,steps,mode,wakes;
static ULONG us(void){return now;}
#define Forbid() ((void)0)
#define Permit() ((void)0)
static void audio_wake(void){wakes++;}
static void Delay(unsigned ticks){now+=ticks*20000;steps++;if(mode==1){if(queued)queued--;else audio_drained=1;}}
static int ua_audio_host_service(void){return mode!=3;}
static int ua_audio_host_pending(void){return queued!=0;}
'''
checks=r'''
int main(void){
 assert(ua_audio_host_pause_drain());assert(!wakes);
 audio_opened=1;queued=3;mode=1;
 assert(ua_audio_host_pause_drain());assert(!queued&&steps==4&&!audio_force);
 mode=2;now=steps=0;queued=1;
 assert(!ua_audio_host_pause_drain());assert(now==2000000&&!audio_force&&queued==1);
 mode=3;now=steps=0;
 assert(!ua_audio_host_pause_drain());assert(!steps&&!audio_force);
 puts("PASS audio pause: disabled, delayed completion, bounded timeout, worker failure");
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'test.c';p.write_text(fixture+s+checks);out=Path(d)/'test'
 subprocess.run(['clang','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(p),'-o',str(out)],check=True)
 subprocess.run([str(out)],check=True)
