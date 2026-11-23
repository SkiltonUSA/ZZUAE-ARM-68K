/* GPL-3.0-or-later. CLI-only experimental Core0 clock diagnostic.
 * Default is QUERY. CONTROL runs stock; TRIAL [MHZ 700|800] is temporary.
 */
#include <devices/timer.h>
#include <libraries/expansion.h>
#include <libraries/expansionbase.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <proto/expansion.h>
#include <proto/timer.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
struct ExpansionBase *ExpansionBase;
struct Device *TimerBase;
static volatile UWORD *reg;
static volatile ULONG *box;
static ULONG saved[13],reply[13];
static int saved_ok;
static unsigned command_abi=1;
static uint64_t eclock(ULONG *hz)
{struct EClockVal t;*hz=ReadEClock(&t);return ((uint64_t)t.ev_hi<<32)|t.ev_lo;}
static int command(unsigned op,unsigned nonce,unsigned target)
{
 if(*reg)return 0;
 ULONG rate,unused;uint64_t begin=eclock(&rate);
 memset(reply,0,sizeof reply);reply[0]=op;reply[1]=command_abi;reply[2]=nonce;reply[3]=target;
 for(unsigned i=0;i<13;i++)box[i]=reply[i];
 CacheClearE((APTR)box,64,CACRF_ClearD);*reg=0x7a13;
 unsigned i;UWORD status=0;
 for(i=0;i<500;i++){status=*reg;if(status==2||status==3)break;Delay(1);}
 uint64_t end=eclock(&unused);
 printf("CLOCK_HOST command=%u elapsed_us=%u (includes 20ms polling)\n",op,
  (ULONG)((end-begin)*1000000ull/rate));
 if(i==500){puts("Clock command timed out. Do not repeat; reboot before another test.");return 0;}
 CacheClearE((APTR)box,64,CACRF_ClearD);
 for(i=0;i<13;i++)reply[i]=box[i];
 *reg=0;for(i=0;i<25&&*reg;i++)Delay(1);
 return status==2&&!*reg&&reply[0]==op&&reply[1]==command_abi&&reply[2]==nonce&&reply[4]==0x5a434c31;
}
static void show_query(void)
{
 if(command_abi>=2){
  printf("CLOCK_SESSION error=%u target_div=%u temp=%u.%u C ctrl=%08x cfg=%08x cpu=%08x nonce=%u fault=%u core1_idle=%u\n",
   reply[3],reply[5],reply[6]/10,reply[6]%10,reply[7],reply[8],reply[9],reply[10],reply[11],reply[12]&1);
  if(command_abi==3)printf("CLOCK_KEEP held=%u\n",(reply[12]>>1)&1);
  return;
 }
 printf("CLOCK_QUERY temp=%u.%u C ctrl=%08x cfg=%08x cpu=%08x fault=%u core1_idle=%u max_div=%u\n",
  reply[6]/10,reply[6]%10,reply[7],reply[8],reply[9],reply[11],reply[12],reply[5]);
}
int main(void)
{
 LONG args[9]={0};struct RDArgs *rd=ReadArgs("CONTROL/S,TRIAL/S,MHZ/N,SESSION/S,BEGIN/S,END/S,NONCE/N,KEEP/S,STATUS/S",args,NULL);
 struct MsgPort *port=NULL;struct timerequest *timer=NULL;
 int rc=20,owned=0,timeropen=0;unsigned target=42;
 if(!rd)return 20;
 unsigned modes=(!!args[0])+(!!args[1])+(!!args[3])+(!!args[4])+(!!args[5])+(!!args[7])+(!!args[8]);
 if(modes>1){puts("Choose CONTROL, TRIAL, SESSION, BEGIN, END, KEEP or STATUS");goto done;}
 unsigned nonce=0;
 if(args[4]||args[5]||args[7]){
  if(!args[6]||*(LONG*)args[6]<=0){puts("BEGIN, KEEP and END require a positive NONCE");goto done;}
  nonce=(unsigned)*(LONG*)args[6];
 }else if(args[6]){puts("NONCE requires BEGIN, KEEP or END");goto done;}
 if(args[3]||args[4]||args[5])command_abi=2;
 if(args[7]||args[8])command_abi=3;
 if(args[2]){
  LONG mhz=*(LONG*)args[2];
  if((!args[1]&&!args[4]&&!args[7])||(mhz!=700&&mhz!=800)){puts("Use TRIAL, BEGIN or KEEP with MHZ 700 or MHZ 800");goto done;}
  target=mhz==800?48:42;
 }
 if((args[4]||args[7])&&!args[2]){puts("BEGIN or KEEP requires MHZ 700 or MHZ 800");goto done;}
 if(args[0])target=40;
 port=CreateMsgPort();if(!port)goto done;
 Forbid();
 if(!FindPort("Sixies.ARM.Debug.Owner")){
  port->mp_Node.ln_Name="Sixies.ARM.Debug.Owner";AddPort(port);owned=1;
 }
 Permit();
 if(!owned){puts("ARM application is active; close it before the clock diagnostic");goto done;}
 timer=(struct timerequest*)CreateIORequest(port,sizeof *timer);if(!timer)goto done;
 if(OpenDevice(TIMERNAME,UNIT_MICROHZ,(struct IORequest*)timer,0))goto done;
 timeropen=1;TimerBase=timer->tr_node.io_Device;
 ExpansionBase=(struct ExpansionBase*)OpenLibrary("expansion.library",0);if(!ExpansionBase)goto done;
 struct ConfigDev *card=FindConfigDev(NULL,0x6d6e,4);if(!card)goto done;
 reg=(volatile UWORD*)((ULONG)card->cd_BoardAddr+0x64);
 box=(volatile ULONG*)((ULONG)card->cd_BoardAddr+0x4010000UL);
 if(*reg){puts("XACP is busy");goto done;}
 CacheClearE((APTR)box,64,CACRF_ClearD);
 for(unsigned i=0;i<13;i++)saved[i]=box[i];
 saved_ok=1;
 if(!command(0,0,0)){puts("Clock diagnostic firmware unavailable");goto done;}
 show_query();if(reply[3])goto done;
 rc=0;
 /* Already-stock END is harmless, including after a reset or refused startup. */
 if(args[5]&&!reply[10]&&!reply[11]&&reply[7]==0x28008&&reply[8]==0xfa220&&reply[9]==0x1f000200)goto done;
 if(args[4]||args[5]||args[7]){
  rc=20;
  if((args[4]||args[7])&&(reply[11]||!(reply[12]&1)||reply[6]>600||
     (reply[10]&&reply[10]!=nonce))){
   puts("Clock session refused by preflight");goto done;
  }
  if(!command(args[7]?4:args[4]?2:3,nonce,target))goto done;
  show_query();if(reply[3]||reply[11])goto done;
  if(args[4]||args[7]){
   unsigned cfg=target==48?0xfa240:0xfa3c0;
   if(reply[5]!=target||reply[10]!=nonce||reply[7]!=((target<<12)|8)||reply[8]!=cfg)goto done;
   if(args[7]){if(!(reply[12]&2))goto done;puts("Clock held until END or reset.");}
   else puts("Session active. END with the same NONCE after Core1 exits. Expiry restores only when idle.");
  }else if(reply[10]||reply[7]!=0x28008||reply[8]!=0xfa220)goto done;
  if(reply[9]!=0x1f000200)goto done;
  rc=0;
 }
 if(args[0]||args[1]){
  rc=20;
  if(reply[11]||!reply[12]||reply[6]>600){puts("Clock trial refused by preflight");goto done;}
  if(target>reply[5]){puts("Firmware does not support the requested clock trial");goto done;}
  ULONG hz;unsigned nonce=(unsigned)eclock(&hz)^(unsigned)(uintptr_t)FindTask(NULL);
  if(!nonce)nonce=1;
  if(!command(1,nonce,target))goto done;
  printf("CLOCK_TRIAL error=%u target_div=%u before_us=%u trial_us=%u after_us=%u hashes=%08x/%08x/%08x restored=%u\n",
   reply[3],reply[5],reply[6],reply[7],reply[8],reply[9],reply[10],reply[11],reply[12]);
  int good=reply[3]==0&&reply[5]==target&&reply[9]==0x05ae1110&&reply[10]==reply[9]&&reply[11]==reply[9]&&reply[12]==1;
  if(!command(0,0,0))goto done;
  show_query();
  if(good&&!reply[11]&&reply[7]==0x28008&&reply[8]==0xfa220&&reply[9]==0x1f000200)rc=0;
 }
 done:
 if(saved_ok&&reg&&!*reg){for(unsigned i=0;i<13;i++)box[i]=saved[i];CacheClearE((APTR)box,64,CACRF_ClearD);}
 if(ExpansionBase)CloseLibrary((struct Library*)ExpansionBase);
 if(timeropen)CloseDevice((struct IORequest*)timer);
 if(timer)DeleteIORequest((struct IORequest*)timer);
 if(owned){Forbid();RemPort(port);Permit();}
 if(port)DeleteMsgPort(port);
 FreeArgs(rd);return rc;
}
