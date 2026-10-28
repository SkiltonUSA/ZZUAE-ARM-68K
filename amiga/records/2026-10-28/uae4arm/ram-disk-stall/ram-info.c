#include <dos/dos.h>
#include <devices/timer.h>
#include <proto/exec.h>
#include <proto/timer.h>
#include <proto/dos.h>
#include <stdio.h>
struct Device *TimerBase;
static ULONG now(void){struct timeval t;GetSysTime(&t);return t.tv_secs*1000000u+t.tv_micro;}
int main(void){
 struct MsgPort *p=CreateMsgPort();if(!p)return 20;
 struct timerequest *t=(struct timerequest*)CreateIORequest(p,sizeof(*t));if(!t){DeleteMsgPort(p);return 20;}
 if(OpenDevice("timer.device",UNIT_MICROHZ,(struct IORequest*)t,0)){DeleteIORequest((struct IORequest*)t);DeleteMsgPort(p);return 20;}
 TimerBase=t->tr_node.io_Device;BPTR lock=Lock("RAM:",ACCESS_READ);
 if(lock){struct InfoData info;for(unsigned i=0;i<5;i++){ULONG start=now();LONG ok=Info(lock,&info);ULONG elapsed=now()-start;printf("RAM_INFO ok=%d elapsed_us=%u blocks=%d used=%d bytesperblock=%d\n",ok,elapsed,info.id_NumBlocks,info.id_NumBlocksUsed,info.id_BytesPerBlock);}UnLock(lock);}
 CloseDevice((struct IORequest*)t);DeleteIORequest((struct IORequest*)t);DeleteMsgPort(p);return lock?0:20;
}
