/* Read-only Exec task sampling; no task priorities or system vectors replaced. */
#include <exec/execbase.h>
#include <exec/interrupts.h>
#include <exec/tasks.h>
#include <hardware/intbits.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <stdio.h>
#include <string.h>
extern void sample_entry(void);
struct sample { APTR task; char name[48]; BYTE priority,state; };
static struct sample samples[1200];
static volatile unsigned used;
void sample_body(void){
 unsigned n=used;
 struct Task *t=SysBase->ThisTask;
 if(n>=1200 || !t)return;
 samples[n].task=t;samples[n].priority=t->tc_Node.ln_Pri;samples[n].state=t->tc_State;
 const char *s=t->tc_Node.ln_Name;unsigned i=0;
 if(s)for(;i<47 && s[i];i++)samples[n].name[i]=s[i];
 samples[n].name[i]=0;used=n+1;
}
int main(void){
 struct Interrupt intr;memset(&intr,0,sizeof(intr));
 intr.is_Node.ln_Type=NT_INTERRUPT;intr.is_Node.ln_Pri=0;
 intr.is_Node.ln_Name="ZZUAE task timing probe";intr.is_Code=sample_entry;
 AddIntServer(INTB_VERTB,&intr);
 for(unsigned s=0;s<20;s++){Delay(50);if(SetSignal(0,SIGBREAKF_CTRL_C)&SIGBREAKF_CTRL_C)break;}
 RemIntServer(INTB_VERTB,&intr);
 printf("VBL samples=%u\n",used);
 for(unsigned i=0;i<used;i++)printf("SAMPLE %u %08lx %d state=%d %s\n",i,(unsigned long)samples[i].task,samples[i].priority,samples[i].state,samples[i].name);
 return 0;
}
