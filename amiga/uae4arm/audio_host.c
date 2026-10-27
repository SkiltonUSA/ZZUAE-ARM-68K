/* GPL-3.0-or-later. Adapted from ZZDosBox batched audio worker.
 * Local transport and Paula backend; no DOSBox emulation dependency. */
#include <exec/memory.h>
#include <devices/ahi.h>
#include <devices/timer.h>
#include <proto/exec.h>
#include <clib/alib_protos.h>
#include <proto/dos.h>
#include <proto/timer.h>
#include <stdio.h>
#include <string.h>
#include "audio_wire.h"
#include "protocol.h"
#include <devices/audio.h>
#include <graphics/gfxbase.h>
#include <proto/graphics.h>
extern struct Device *TimerBase;
static ULONG us(void){struct timeval t;GetSysTime(&t);return t.tv_secs*1000000u+t.tv_micro;}
static ULONG audio_gaps,audio_samples,audio_backend,audio_rate=32000;
static volatile uint8_t *shared;
static const struct ad_io *syncio;
/* GPL-3.0-or-later. 68k-only producer/consumer; no PicoDrive code reused.
 * The worker exclusively owns AHI ports, requests and DMA buffers. It never
 * touches ARM shared memory, graphics, libc or the main task's timer.
 * It is a DOS Process because device initialization may use DOS internally.
 * Ring slots remain immutable until copied by the worker. On this single 68k
 * CPU, short Forbid/Permit sections publish indices and guard task lifetime. */
#include <dos/dostags.h>
#define AUDIO_SLOTS 4u
#define AUDIO_PREBUFFER 2u
struct audio_block { ULONG count; UBYTE data[4096]; };
static struct audio_block *audio_queue;
static struct Task *audio_task,*audio_parent;
static volatile ULONG audio_write,audio_read,audio_worker_mask;
static volatile ULONG audio_started,audio_done,audio_stop,audio_error,audio_force;
static volatile ULONG audio_highwater,audio_submitted,audio_completed,audio_inflight;
static LONG audio_parent_signal=-1;
static int audio_opened;

static void audio_wake(void){
 Forbid();
 if(audio_task&&!audio_done&&audio_worker_mask)Signal(audio_task,audio_worker_mask);
 Permit();
}
static void ahi_worker(void){
 struct MsgPort *port=NULL;
 struct AHIRequest *req[2]={NULL,NULL};
 UBYTE *data[2]={NULL,NULL};
 int active[2]={0,0},opened=0,slot=0,primed=0;
 ULONG submitted_count[2]={0,0};
 LONG signal=AllocSignal(-1);ULONG mask=0,i;
 if(signal<0)goto finish;
 mask=1UL<<signal;audio_worker_mask=mask;
 port=CreateMsgPort();if(!port)goto finish;
 for(i=0;i<2;i++){
  req[i]=(struct AHIRequest *)CreateIORequest(port,sizeof(struct AHIRequest));
  data[i]=AllocVec(4096,MEMF_PUBLIC);
  if(!req[i]||!data[i])goto finish;
 }
 req[0]->ahir_Version=4;
 if(OpenDevice(AHINAME,0,(struct IORequest *)req[0],0))goto finish;
 opened=1;
 req[1]->ahir_Std.io_Device=req[0]->ahir_Std.io_Device;
 req[1]->ahir_Std.io_Unit=req[0]->ahir_Std.io_Unit;req[1]->ahir_Version=4;
 audio_opened=1;audio_started=1;Signal(audio_parent,1UL<<audio_parent_signal);
 for(;;){
  ULONG available,n,index,pending=0;int other=slot^1;
  for(i=0;i<2;i++)if(active[i]&&!CheckIO((struct IORequest*)req[i]))pending+=submitted_count[i];
  audio_inflight=pending;
  if(audio_stop==1)break;
  Forbid();available=audio_write-audio_read;Permit();
  if(!primed&&(available>=AUDIO_PREBUFFER||audio_stop==2||audio_force))primed=1;
  /* Keep the previous request intact until its linked successor has been
   * submitted. Reap a slot only when it is about to be reused. */
  if(primed&&available&&(!active[slot]||CheckIO((struct IORequest *)req[slot]))){
   if(active[slot]){
    WaitIO((struct IORequest *)req[slot]);active[slot]=0;
    if(req[slot]->ahir_Std.io_Error){audio_error=1;break;}
    audio_completed+=submitted_count[slot];
   }
   index=audio_read%AUDIO_SLOTS;n=audio_queue[index].count;
   CopyMem(audio_queue[index].data,data[slot],n*4);
   Forbid();audio_read++;Permit();
   req[slot]->ahir_Std.io_Command=CMD_WRITE;
   req[slot]->ahir_Std.io_Data=data[slot];req[slot]->ahir_Std.io_Length=n*4;
   req[slot]->ahir_Std.io_Offset=0;req[slot]->ahir_Frequency=audio_rate;
   req[slot]->ahir_Type=AHIST_S16S;req[slot]->ahir_Volume=0x10000;
   req[slot]->ahir_Position=0x8000;
   if(active[other]&&CheckIO((struct IORequest *)req[other]))audio_gaps++;
   req[slot]->ahir_Link=active[other]?req[other]:NULL;
   /* AHI can rewrite io_Length from bytes to samples; retain our count. */
   submitted_count[slot]=n;SendIO((struct IORequest *)req[slot]);
   active[slot]=1;audio_submitted+=n;slot=other;
   continue;
  }
  if(audio_stop==2&&!available){
   int busy=0;
   for(i=0;i<2;i++)if(active[i]){
    if(!CheckIO((struct IORequest *)req[i]))busy=1;
   }
   if(!busy)break;
  }
  Wait(mask|(1UL<<port->mp_SigBit));
 }
finish:
 for(i=0;i<2;i++)if(active[i]){
  int aborted=!CheckIO((struct IORequest *)req[i]);
  if(aborted)AbortIO((struct IORequest *)req[i]);
  WaitIO((struct IORequest *)req[i]);
  if(!aborted&&!req[i]->ahir_Std.io_Error)audio_completed+=submitted_count[i];
  else if(!aborted)audio_error=1;
 }
 if(opened)CloseDevice((struct IORequest *)req[0]);
 for(i=0;i<2;i++){
  if(req[i])DeleteIORequest((struct IORequest *)req[i]);
  if(data[i])FreeVec(data[i]);
 }
 if(port)DeleteMsgPort(port);
 if(signal>=0)FreeSignal(signal);
 /* Return to the DOS process wrapper while still forbidden, so the parent
  * cannot unload our entry code before it returns. DOS owns process teardown. */
 Forbid();audio_worker_mask=0;audio_done=1;audio_started=1;
 Signal(audio_parent,1UL<<audio_parent_signal);
}
/* Two stereo blocks queued on audio.device. Never writes custom registers.
 * Paula requires chip memory and signed 8-bit planes. Period 128 works on
 * standard PAL/NTSC scan rates; the mixer uses the matching native clock. */
static void paula_worker(void){
 struct MsgPort *port=NULL;
 struct IOAudio *alloc=NULL,*req[4]={NULL,NULL,NULL,NULL};
 UBYTE *data[2]={NULL,NULL},masks[]={3,5,10,12};
 int active[2]={0,0},replied[4]={0,0,0,0},opened=0,slot=0,primed=0;
 struct Message *message;
 ULONG counts[2]={0,0},i,mask=0,channels=0,left=0,right=0;
 LONG signal=AllocSignal(-1);
 if(signal<0)goto finish;
 mask=1UL<<signal;audio_worker_mask=mask;
 port=CreateMsgPort();if(!port)goto finish;
 alloc=(struct IOAudio*)CreateIORequest(port,sizeof(*alloc));if(!alloc)goto finish;
 alloc->ioa_Request.io_Message.mn_Node.ln_Pri=-10;
 alloc->ioa_Request.io_Flags=ADIOF_NOWAIT;
 alloc->ioa_Data=masks;alloc->ioa_Length=sizeof(masks);
 if(OpenDevice("audio.device",0,(struct IORequest*)alloc,0))goto finish;
 opened=1;channels=(ULONG)alloc->ioa_Request.io_Unit;
 left=channels&6;right=channels&9;
 if(!left||!right)goto finish;
 for(i=0;i<4;i++){
  req[i]=(struct IOAudio*)CreateIORequest(port,sizeof(*req[i]));if(!req[i])goto finish;
  req[i]->ioa_Request.io_Device=alloc->ioa_Request.io_Device;
  req[i]->ioa_Request.io_Unit=(struct Unit*)((i&1)?right:left);
  req[i]->ioa_AllocKey=alloc->ioa_AllocKey;
 }
 for(i=0;i<2;i++){data[i]=AllocVec(UA_FRAMES*2,MEMF_CHIP);if(!data[i])goto finish;}
 audio_opened=1;audio_started=1;Signal(audio_parent,1UL<<audio_parent_signal);
 for(;;){
  ULONG available,n,index,j;int ready=1,other=slot^1;
  while((message=GetMsg(port)))for(j=0;j<4;j++)if(message==(struct Message*)req[j])replied[j]=1;
  n=0;for(i=0;i<2;i++)if(active[i]&&(!replied[i*2]||!replied[i*2+1]))n+=counts[i];
  audio_inflight=n;
  if(audio_stop==1)break;
  Forbid();available=audio_write-audio_read;Permit();
  if(!primed&&(available>=AUDIO_PREBUFFER||audio_stop==2||audio_force))primed=1;
  if(active[slot])for(j=0;j<2;j++)if(!replied[slot*2+j])ready=0;
  if(primed&&available&&ready){
   if(active[slot]){
    for(j=0;j<2;j++){
     /* Both completion messages were removed through GetMsg above. */
     if(req[slot*2+j]->ioa_Request.io_Error)audio_error=1;
    }
    active[slot]=0;if(audio_error)break;
    audio_completed+=counts[slot];
   }
   index=audio_read%AUDIO_SLOTS;n=audio_queue[index].count;
   for(j=0;j<n;j++){
    data[slot][j]=audio_queue[index].data[j*4];
    data[slot][n+j]=audio_queue[index].data[j*4+2];
   }
   Forbid();audio_read++;Permit();
   if(active[other]&&replied[other*2]&&replied[other*2+1])audio_gaps++;
   for(j=0;j<2;j++){
    struct IOAudio *r=req[slot*2+j];
    r->ioa_Request.io_Command=CMD_WRITE;r->ioa_Request.io_Flags=ADIOF_PERVOL;
    r->ioa_Data=data[slot]+j*n;r->ioa_Length=n;r->ioa_Period=128;
    r->ioa_Volume=64;r->ioa_Cycles=1;
    replied[slot*2+j]=0;BeginIO((struct IORequest*)r);
   }
   counts[slot]=n;active[slot]=1;audio_submitted+=n;slot=other;continue;
  }
  if(audio_stop==2&&!available){
   int busy=0;
   for(i=0;i<2;i++)if(active[i])for(j=0;j<2;j++)if(!replied[i*2+j])busy=1;
   if(!busy)break;
  }
  Wait(mask|(1UL<<port->mp_SigBit));
 }
finish:
 for(i=0;i<2;i++)if(active[i]){
  ULONG j;int aborted=0;
  for(j=0;j<2;j++){
   unsigned k=i*2+j;
   if(!replied[k]){
    aborted=1;AbortIO((struct IORequest*)req[k]);
    while(!replied[k]){
     ULONG m;
     while((message=GetMsg(port)))for(m=0;m<4;m++)if(message==(struct Message*)req[m])replied[m]=1;
     if(!replied[k])Wait(1UL<<port->mp_SigBit);
    }
   }
   if(!aborted&&req[k]->ioa_Request.io_Error)audio_error=1;
  }
  if(!aborted&&!audio_error)audio_completed+=counts[i];
 }
 if(opened)CloseDevice((struct IORequest*)alloc);
 for(i=0;i<4;i++)if(req[i])DeleteIORequest((struct IORequest*)req[i]);
 for(i=0;i<2;i++)if(data[i])FreeVec(data[i]);
 if(alloc)DeleteIORequest((struct IORequest*)alloc);
 if(port)DeleteMsgPort(port);
 if(signal>=0)FreeSignal(signal);
 Forbid();audio_worker_mask=0;audio_done=1;audio_started=1;
 Signal(audio_parent,1UL<<audio_parent_signal);
}

static void player_audio_close(void){
 if(audio_task){
  ULONG start=us();
  audio_stop=2;audio_wake(); /* Flush even a short stream below prebuffer. */
  while(!audio_done){
   if((ULONG)(us()-start)>2000000u){audio_error=1;audio_stop=1;audio_wake();}
   /* Never unload live worker code or free buffers on a timeout. */
   Delay(1);
  }
  audio_task=NULL;
 }
 audio_opened=0;
 if(audio_parent_signal>=0){SetSignal(0,1UL<<audio_parent_signal);FreeSignal(audio_parent_signal);audio_parent_signal=-1;}
 if(audio_queue){FreeVec(audio_queue);audio_queue=NULL;}
 printf("AUDIO_TASK queued=%u submitted=%u completed=%u highwater=%u error=%u stopped=%u gaps=%u\n",
  audio_samples,audio_submitted,audio_completed,audio_highwater,audio_error,audio_done,audio_gaps);
}
static int player_audio_open(void){
 audio_parent=FindTask(NULL);audio_parent_signal=AllocSignal(-1);
 if(audio_parent_signal<0)goto fail;
 audio_queue=AllocVec(sizeof(*audio_queue)*AUDIO_SLOTS,MEMF_PUBLIC|MEMF_CLEAR);
 if(!audio_queue)goto fail;
 /* AHI may load preferences/drivers using DOS: use a Process, not an Exec
  * Task. No shell file handles or CLI are inherited by the child. */
 audio_task=(struct Task *)CreateNewProcTags(NP_Entry,(ULONG)(audio_backend==1?paula_worker:ahi_worker),
  NP_Name,(ULONG)"ZZUAE audio",NP_Priority,5,NP_StackSize,32768,
  NP_Input,0,NP_Output,0,NP_CloseInput,FALSE,NP_CloseOutput,FALSE,TAG_DONE);
 if(!audio_task)goto fail;
 while(!audio_started)Wait(1UL<<audio_parent_signal);
 if(!audio_opened)goto fail;
 printf("STARTUP Sound: %s, %u Hz stereo, 2-block prebuffer\n",audio_backend==1?"Paula direct 8-bit":"AHI unit 0 16-bit",audio_rate);return 1;
fail:
 player_audio_close();puts("ERROR Sound device unavailable: choose another output or Off");return 0;
}

int ua_audio_host_open(volatile uint8_t*b,const struct ad_io*io,unsigned enabled){
 shared=b;syncio=io;audio_backend=enabled;
 if(enabled==1){
  struct GfxBase *gfx=(struct GfxBase*)OpenLibrary("graphics.library",0);
  if(!gfx)return 0;
  audio_rate=((gfx->DisplayFlags&PAL)?3546895u:3579545u)/128u;
  CloseLibrary((struct Library*)gfx);
 }
 ad_put(b,UA_RATE,audio_rate);ad_put(b,UA_RESERVE,0);ad_put(b,UA_PACING,enabled?1:0);io->push(b+UA_RATE,12,NULL);
 ad_put(b,UA_WRITE,0);ad_put(b,UA_READ,0);
 io->push(b+UA_WRITE,4,NULL);io->push(b+UA_READ,4,NULL);
 if(!enabled)return 1;
 return player_audio_open();
}
int ua_audio_host_service(void){
 ULONG r,w,n,first,count,i;volatile uint8_t*b=shared;
 if(!audio_opened)return 1;
 if(audio_error||audio_done)return 0;
 r=ad_get(b,UA_READ);syncio->pull(b+UA_WRITE,4,NULL);w=ad_get(b,UA_WRITE);syncio->barrier(NULL);
 if(w-r>UA_SLOTS)return 0;
 Forbid();first=audio_write;n=first-audio_read;i=audio_inflight;Permit();
 ad_put(b,UA_RESERVE,n*UA_FRAMES+i);syncio->push(b+UA_RESERVE,4,NULL);
 count=w-r;if(count>AUDIO_SLOTS-n)count=AUDIO_SLOTS-n;
 if(!count)return 1;
 /* Copy the occupied snapshot before publishing either consumer or producer.
  * The audio task may free more local slots meanwhile; that only makes this
  * batch conservative. It cannot consume unpublished slots. */
 for(i=0;i<count;i++){
  ULONG source=((r+i)&(UA_SLOTS-1))*UA_STRIDE,index=(first+i)%AUDIO_SLOTS;
  syncio->pull(b+UA_DATA+source,UA_STRIDE,NULL);
  CopyMem((APTR)(b+UA_DATA+source),audio_queue[index].data,UA_STRIDE);
  audio_queue[index].count=UA_FRAMES;
 }
 ad_put(b,UA_READ,r+count);syncio->push(b+UA_READ,4,NULL);syncio->barrier(NULL);
 Forbid();audio_write=first+count;
 n=audio_write-audio_read;if(n>audio_highwater)audio_highwater=n;Permit();
 audio_samples+=count*UA_FRAMES;audio_wake();
 return 1;
}

int ua_audio_host_pending(void){
 if(!audio_opened)return 0;
 syncio->pull(shared+UA_WRITE,4,NULL);return ad_get(shared,UA_WRITE)!=ad_get(shared,UA_READ);
}
int ua_audio_host_close(void){
 if(audio_task||audio_queue){
  syncio->pull(shared+UA_NONZERO,8,NULL);
  printf("AUDIO_PACING deferred=%u\n",ad_get(shared,UA_DEFERRED));
  printf("AUDIO_PCM nonzero_frames=%u rate=%u backend=%u\n",ad_get(shared,UA_NONZERO),audio_rate,audio_backend);
  player_audio_close();
 }
 return !audio_error;
}
