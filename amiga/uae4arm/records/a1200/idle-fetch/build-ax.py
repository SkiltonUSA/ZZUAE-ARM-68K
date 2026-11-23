from pathlib import Path
import shutil
p=Path('.context/amiga/uae4arm/a1200');out=p/'gameplay/build-ax-compare'
shutil.copytree(p/'gameplay/build-pixel4',out,dirs_exist_ok=True)
old=Path('.context/ZZSNES-ARM-68K/development/output-quality-20261030')
shutil.copy2(old/'ax_queue.h',out/'ax_queue.h')
s=(old/'ax_stream.h').read_text().replace('#define EM_AUDIO_AHI\n#include "audio_output.h"','')
s=s.replace('choice=em_audio_load()','choice=4')
s=s.replace(' if(choice==0)choice=em_audio_unit0_paula()?2:1;','')
s=s.replace('unsigned score=em_audio_mode(choice,name,(unsigned)stereo,(unsigned)bits,(unsigned)realtime);','unsigned score=(strstr(name,"ZZ9000AX") && stereo && bits==16 && realtime)?1:0;')
s=s.replace('if(choice==1)goto fail;s->choice=choice;', 's->choice=choice;')
s=s.replace('if(selected==AHI_INVALID_ID)goto fail;s->mode=selected;', 'if(selected==AHI_INVALID_ID){goto fail;}\n s->mode=selected;')
s=s.replace('AX supports 32000, not SNES 32040.', 'AX mixer uses 32000; source PCM remains at the matched rate.')
(out/'ax_stream.h').write_text(s)
s=Path('amiga/uae4arm/audio_host.c').read_text()
a=s.index('static void ahi_worker(void)');z=s.index('/* Two stereo blocks',a);s=s[:a]+s[z:]
worker=r'''
#include "ax_stream.h"
static ULONG ax_mode,ax_mix,ax_callbacks,ax_silent;
static void ax_worker(void){
 struct ax_stream stream;int opened=0,primed=0;
 LONG signal=AllocSignal(-1);ULONG mask=0;
 if(signal<0)goto finish;
 mask=1UL<<signal;audio_worker_mask=mask;
 if(!ax_open(&stream,audio_rate,AHIST_S16S,4,mask))goto finish;
 opened=1;
 if(!ax_ready(&stream)){audio_error=1;goto finish;}
 ax_mode=stream.mode;ax_mix=stream.mixrate;
 audio_opened=1;audio_started=1;Signal(audio_parent,1UL<<audio_parent_signal);
 for(;;){
  ULONG available,n,index;int slot;unsigned i;
  Disable();
  audio_completed=stream.q.completed;audio_gaps=stream.q.starvations;
  ax_callbacks=stream.q.callbacks;ax_silent=stream.q.silence;
  audio_inflight=0;
  for(i=0;i<3;i++)if(stream.q.occupied[i])audio_inflight+=stream.q.count[i];
  Enable();
  if(audio_stop==1)break;
  Forbid();available=audio_write-audio_read;Permit();
  if(!primed&&(available>=AUDIO_PREBUFFER||audio_stop==2||audio_force))primed=1;
  if(primed&&available&&(slot=ax_free(&stream.q))>=0){
   index=audio_read%AUDIO_SLOTS;n=audio_queue[index].count;
   if(n>stream.capacity){audio_error=1;break;}
   CopyMem(audio_queue[index].data,stream.data[slot],n*4);
   Disable();ax_publish(&stream.q,n);Enable();
   Forbid();audio_read++;Permit();
   audio_submitted+=n;continue;
  }
  if(audio_stop==2&&!available){
   Disable();stream.q.draining=1;int idle=ax_idle(&stream.q);Enable();
   if(idle)break;
  }
  Wait(mask);
 }
finish:
 if(opened)ax_close(&stream);
 if(signal>=0)FreeSignal(signal);
 Forbid();audio_worker_mask=0;audio_done=1;audio_started=1;
 Signal(audio_parent,1UL<<audio_parent_signal);
}
'''
s=s.replace('static void player_audio_close(void)',worker+'\nstatic void player_audio_close(void)')
s=s.replace('audio_backend==1?paula_worker:ahi_worker','audio_backend==1?paula_worker:ax_worker')
s=s.replace('"AHI unit 0 16-bit"','"ZZ9000AX per-application AHI 16-bit"')
s=s.replace(' shared=b;syncio=io;audio_backend=enabled;',' shared=b;syncio=io;audio_backend=enabled;if(enabled==2)audio_rate=27710;')
s=s.replace(' printf("AUDIO_TASK queued=', ' printf("AX_COMPARE mode=%08x source_rate=%u mix_rate=%u callbacks=%u silence_blocks=%u\\n",ax_mode,audio_rate,ax_mix,ax_callbacks,ax_silent);\n printf("AUDIO_TASK queued=')
(out/'audio_ax.c').write_text(s)
extend=(p/'performance/extend-chipreads.py').read_text().replace("for variant in ('chipreads',):", "for variant in ('ax-compare',):").replace('a1200/performance/build-','a1200/gameplay/build-').replace("'amiga/uae4arm/audio_host.c'",repr(str(out/'audio_ax.c')))
exec(extend)
