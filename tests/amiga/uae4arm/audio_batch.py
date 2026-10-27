#!/usr/bin/env python3
"""Compile the actual host drain function with a deterministic consumer fixture."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[3]
s=(root/'amiga/uae4arm/audio_host.c').read_text();s=s[s.index('int ua_audio_host_service(void)'):s.index('int ua_audio_host_pending(void)')]
prefix=r'''
#include <assert.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include "audio_wire.h"
#include "protocol.h"
typedef uint32_t ULONG; typedef void *APTR;
#define AUDIO_SLOTS 4u
#define Forbid() ((void)0)
#define Permit() ((void)0)
static uint8_t memory[0x490000];
static volatile uint8_t *shared=memory;
static struct {ULONG count;uint8_t data[UA_STRIDE];} audio_queue[4];
static unsigned audio_opened=1,audio_error,audio_done,audio_write,audio_read,audio_highwater,audio_samples,audio_inflight,wakes,pulls,pushes,consume;
static void audio_wake(void){wakes++;}
static void CopyMem(APTR a,APTR b,ULONG n){memcpy(b,a,n);if(consume){audio_read++;consume=0;}}
static void pull(volatile void*p,size_t n,void*o){(void)o;if(p==shared+UA_WRITE){assert(n==4);return;} assert(n==UA_STRIDE);pulls++;}
static void push(volatile void*p,size_t n,void*o){(void)o;if(p==shared+UA_RESERVE){assert(n==4);return;} assert(p==shared+UA_READ&&n==4);pushes++;}
static void barrier(void*o){(void)o;}
static const struct ad_io callbacks={.pull=pull,.push=push,.barrier=barrier};
static const struct ad_io *syncio=&callbacks;
'''
suffix=r'''
int main(void){
 for(unsigned local=0;local<=4;local++)for(unsigned remote=0;remote<=4;remote++)for(unsigned wrap=0;wrap<2;wrap++){
  unsigned origin=wrap?0xfffffffeu:3,first=wrap?0xfffffffeu:7;
  audio_read=first-local;audio_write=first;audio_inflight=2048;audio_samples=wakes=pulls=pushes=0;
  ad_put(shared,UA_READ,origin);ad_put(shared,UA_WRITE,origin+remote);
  for(unsigned i=0;i<remote;i++)memset(memory+UA_DATA+((origin+i)%4)*UA_STRIDE,17+i,UA_STRIDE);
  unsigned want=remote<4-local?remote:4-local;
  assert(ua_audio_host_service());assert(ad_get(shared,UA_READ)==origin+want);
  assert(audio_write==first+want && audio_samples==want*1024);
  assert(ad_get(shared,UA_RESERVE)==local*1024+2048);
  assert(pulls==want&&pushes==!!want&&wakes==!!want);
  for(unsigned i=0;i<want;i++)for(unsigned j=0;j<UA_STRIDE;j++)assert(audio_queue[(first+i)%4].data[j]==17+i);
 }
 /* Consumer release while copy is in progress must not expose unfilled data. */
 audio_write=3;audio_read=2;consume=1;ad_put(shared,UA_READ,0);ad_put(shared,UA_WRITE,4);
 assert(ua_audio_host_service());assert(audio_write==6&&audio_read==3&&ad_get(shared,UA_READ)==3);
 ad_put(shared,UA_WRITE,9);assert(!ua_audio_host_service());
 puts("PASS host audio batch: exact occupied blocks, empty/full, shared/local wrap, consumer progress, corrupt occupancy");
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'test.c';p.write_text(prefix+s+suffix);binary=Path(d)/'test'
 subprocess.run(['clang','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(root/'amiga/uae4arm'),'-I'+str(root/'amiga/arm_debug'),str(p),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
