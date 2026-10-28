#include <dos/dos.h>
#include <exec/types.h>
#include <exec/memory.h>
#include <devices/timer.h>
#include <proto/exec.h>
#include <proto/timer.h>
#include <stdio.h>
struct Device *TimerBase;
static ULONG now(void){struct timeval t;GetSysTime(&t);return t.tv_secs*1000000u+t.tv_micro;}
int main(void){
 struct MsgPort *p=CreateMsgPort();if(!p)return 20;
 struct timerequest *t=(struct timerequest*)CreateIORequest(p,sizeof(*t));if(!t){DeleteMsgPort(p);return 20;}
 if(OpenDevice("timer.device",UNIT_MICROHZ,(struct IORequest*)t,0)){DeleteIORequest((struct IORequest*)t);DeleteMsgPort(p);return 20;}
 TimerBase=t->tr_node.io_Device;LONG old=SetTaskPri(FindTask(NULL),0);int priorities[]={0,10,20};
 for(unsigned i=0;i<3;i++){
  ULONG worst=0,stalls=0,start=now(),count=0;SetTaskPri(FindTask(NULL),priorities[i]);
  while(now()-start<16000000u){
   if(SetSignal(0,SIGBREAKF_CTRL_C)&SIGBREAKF_CTRL_C)goto done;
   ULONG before=now();t->tr_node.io_Command=TR_ADDREQUEST;t->tr_time.tv_secs=0;t->tr_time.tv_micro=1000;DoIO((struct IORequest*)t);
   ULONG delta=now()-before;if(delta>worst)worst=delta;if(delta>100000u)stalls++;count++;
  }
  SetTaskPri(FindTask(NULL),old);printf("SCHED priority=%d wakeups=%u max_us=%u over100ms=%u\n",priorities[i],count,worst,stalls);
 }
 done:SetTaskPri(FindTask(NULL),old);CloseDevice((struct IORequest*)t);DeleteIORequest((struct IORequest*)t);DeleteMsgPort(p);return 0;
}
