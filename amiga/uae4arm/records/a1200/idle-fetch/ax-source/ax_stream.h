/* GPL-3.0-or-later. Per-application AHI output. No ENV writes.
 * AHIBase belongs to this worker. Hook only retires/schedules buffers and signals;
 * no allocation, file I/O, waiting, PCM copies or ARM/graphics access in IRQ. */
#include <devices/ahi.h>
#include <utility/hooks.h>
#include <proto/ahi.h>
#include "ax_queue.h"

struct Library *AHIBase;
struct ax_stream {
 struct MsgPort *port;struct AHIRequest *request;struct AHIAudioCtrl *control;
 struct Hook hook;struct ax_queue q;struct Task *task;
 UBYTE *data[4];ULONG mask,rate,type,bytes,capacity,silent_frames,mode,mixrate,choice;
 int opened,playing;
};
static ULONG ax_hook(struct Hook *hook __asm("a0"),
 struct AHIAudioCtrl *control __asm("a2"),struct AHISoundMessage *message __asm("a1")){
 struct ax_stream *s=(struct ax_stream *)hook->h_Data;int next;
 if(message->ahism_Channel)return 0;
 next=ax_started(&s->q);
 AHI_SetSound(0,next,0,next==3?s->silent_frames:s->q.count[next],control,0);
 Signal(s->task,s->mask);return 0;
}
static void ax_close(struct ax_stream *s){
 /* Synchronous FreeAudio removes the hook and stops the driver before storage
  * or its signal/task lifetime ends. Never free live dynamic samples. */
 if(s->control){if(s->playing)AHI_ControlAudio(s->control,AHIC_Play,FALSE,TAG_DONE);AHI_FreeAudio(s->control);s->control=NULL;}
 if(s->opened){CloseDevice((struct IORequest *)s->request);s->opened=0;}
 if(s->request){DeleteIORequest((struct IORequest *)s->request);s->request=NULL;}
 if(s->port){DeleteMsgPort(s->port);s->port=NULL;}
 {int i;for(i=0;i<4;i++)if(s->data[i]){FreeVec(s->data[i]);s->data[i]=NULL;}}
 AHIBase=NULL;s->playing=0;
}
static int ax_open(struct ax_stream *s,ULONG rate,ULONG type,ULONG bytes,ULONG mask){
 ULONG id=AHI_INVALID_ID,selected=AHI_INVALID_ID,i,minframes=0,choice=4,mix;unsigned best=0;char name[128];
 if(choice==1)return 0;
 memset(s,0,sizeof(*s));ax_init(&s->q);s->rate=rate;s->type=type;s->bytes=bytes;
 s->task=FindTask(NULL);s->mask=mask;s->capacity=3072;s->silent_frames=(rate+49)/50;
 s->port=CreateMsgPort();if(!s->port)goto fail;
 s->request=(struct AHIRequest *)CreateIORequest(s->port,sizeof(*s->request));if(!s->request)goto fail;
 s->request->ahir_Version=4;
 if(OpenDevice(AHINAME,AHI_NO_UNIT,(struct IORequest *)s->request,0))goto fail;
 s->opened=1;AHIBase=(struct Library *)s->request->ahir_Std.io_Device;

 s->choice=choice;/* Source and device clocks are separate. AX mixer uses 32000; source PCM remains at the matched rate. */
 mix=choice==2?22050:choice==3?28000:32000;
 /* Resolve a registered mode; never assume a firmware or preference ID. */
 while((id=AHI_NextAudioID(id))!=AHI_INVALID_ID){ULONG stereo=0,bits=0,realtime=0;
  name[0]=0;
  if(AHI_GetAudioAttrs(id,NULL,AHIDB_BufferLen,sizeof(name),AHIDB_Name,(ULONG)name,
     AHIDB_Stereo,(ULONG)&stereo,AHIDB_Bits,(ULONG)&bits,AHIDB_Realtime,(ULONG)&realtime,TAG_DONE)){
   unsigned score=(strstr(name,"ZZ9000AX") && stereo && bits==16 && realtime)?1:0;
   if(score>best){best=score;selected=id;}
  }
 }
 if(selected==AHI_INVALID_ID){goto fail;}
 s->mode=selected;
 s->hook.h_Entry=(ULONG (*)())ax_hook;s->hook.h_Data=s;
 s->control=AHI_AllocAudio(AHIA_AudioID,selected,AHIA_MixFreq,mix,AHIA_Channels,1,
  AHIA_Sounds,4,AHIA_SoundFunc,(ULONG)&s->hook,TAG_DONE);
 if(!s->control)goto fail;
 if(!AHI_GetAudioAttrs(AHI_INVALID_ID,s->control,AHIDB_MaxPlaySamples,(ULONG)&minframes,TAG_DONE))goto fail;
 if(AHI_ControlAudio(s->control,AHIC_MixFreq_Query,(ULONG)&s->mixrate,TAG_DONE)||!s->mixrate)goto fail;
 minframes=(ULONG)(((unsigned long long)minframes*rate+s->mixrate-1)/s->mixrate);
 if(minframes>65536)goto fail;
 if(minframes>s->capacity)s->capacity=minframes;

 for(i=0;i<4;i++){
  struct AHISampleInfo sample;
  ULONG frames=s->capacity;
  s->data[i]=AllocVec(frames*bytes,MEMF_PUBLIC|MEMF_CLEAR);if(!s->data[i])goto fail;
  sample.ahisi_Type=type;sample.ahisi_Address=s->data[i];sample.ahisi_Length=frames;
  if(AHI_LoadSound(i,AHIST_DYNAMICSAMPLE,&sample,s->control))goto fail;
 }
 return 1;
fail:ax_close(s);return 0;
}
static int ax_start(struct ax_stream *s){
 if(AHI_ControlAudio(s->control,AHIC_Play,TRUE,TAG_DONE))return 0;
 s->playing=1;AHI_SetVol(0,0x10000,0x8000,s->control,AHISF_IMM);
 AHI_SetFreq(0,s->rate,s->control,AHISF_IMM);
 AHI_SetSound(0,3,0,s->silent_frames,s->control,AHISF_IMM);return 1;
}

/* A successful AllocAudio/Play does not prove that the device advances.
 * Probe AX using silence before accepting game PCM. No register/firmware reset. */
static int ax_ready(struct ax_stream *s){
 if(!ax_start(s))return 0;
 for(unsigned ticks=0;ticks<25&&!s->q.callbacks;ticks++)Delay(1);
 return s->q.callbacks!=0;
}
