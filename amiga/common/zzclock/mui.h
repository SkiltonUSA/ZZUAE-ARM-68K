/* GPL-3.0-or-later. Optional clock control; opening the UI never changes clocks. */
#pragma once
#include <dos/dostags.h>
#include <dos/dosextens.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <proto/muimaster.h>
#include <libraries/mui.h>
#include "policy.h"

enum { ZZCLOCK_REFRESH=7901, ZZCLOCK_APPLY=7902 };
static Object *zzclock_choice,*zzclock_apply,*zzclock_refresh,*zzclock_text;
static struct zo_status zzclock_status;
static int zzclock_valid;
static const char *zzclock_labels[]={"666.7 MHz (standard)","800 MHz (experimental)",NULL};
static char zzclock_report[2048],zzclock_message[160];

static Object *zzclock_button(const char *s){
 return TextObject,ButtonFrame,MUIA_InputMode,MUIV_InputMode_RelVerify,
  MUIA_Background,MUII_ButtonBack,MUIA_CycleChain,TRUE,
  MUIA_FixWidthTxt,(ULONG)s,MUIA_InnerLeft,8,MUIA_InnerRight,8,
  MUIA_Text_PreParse,(ULONG)"\33c",MUIA_Text_Contents,(ULONG)s,End;
}
static Object *zzclock_panel(void){
 return VGroup,GroupFrameT("ZZOverclock"),MUIA_VertWeight,0,
  Child,HGroup,MUIA_VertWeight,0,
   Child,zzclock_choice=CycleObject,MUIA_Cycle_Entries,(ULONG)zzclock_labels,
    MUIA_CycleChain,TRUE,MUIA_FixWidth,216,MUIA_Disabled,TRUE,End,
   Child,zzclock_apply=zzclock_button("Apply"),
   Child,zzclock_refresh=zzclock_button("Refresh"),Child,HSpace(0),End,
  Child,zzclock_text=TextObject,MUIA_Text_SetMin,FALSE,
   MUIA_Text_Contents,(ULONG)"Refresh to check clock firmware.",End,
  Child,TextObject,MUIA_Text_Contents,(ULONG)"Optional. Standard speed works without the clock service.",End,
  End;
}
static void zzclock_wire(Object *application){
 set(zzclock_apply,MUIA_Disabled,TRUE);
 DoMethod(zzclock_refresh,MUIM_Notify,MUIA_Pressed,FALSE,(ULONG)application,2,MUIM_Application_ReturnID,ZZCLOCK_REFRESH);
 DoMethod(zzclock_apply,MUIM_Notify,MUIA_Pressed,FALSE,(ULONG)application,2,MUIM_Application_ReturnID,ZZCLOCK_APPLY);
 set(zzclock_choice,MUIA_ShortHelp,(ULONG)"Board-wide clock. Apply only after closing ARM apps.\n800 MHz is experimental; firmware checks temperature and activity.\nThis does not change startup preferences or flash firmware.");
}
static int zzclock_helper(const char *args){
 /* Each launch owns the standard Core1 exclusion port, including STATUS.
  * Shell arguments and helper locations are fixed, never user-supplied. */
 BPTR lock,input,output;
 char tool[512],quoted[1026],command[1100],logpath[64];LONG rc;FILE *f;
 zzclock_report[0]=0;
 if(!NameFromLock(GetProgramDir(),(STRPTR)tool,sizeof tool)||
    !AddPart((STRPTR)tool,"ZZClock",sizeof tool))return 0;
 /* PROGDIR changes inside SystemTags' shell. Resolve it in this process. */
 {
  unsigned i,n=0;quoted[n++]='"';
  for(i=0;tool[i];i++){
   if(tool[i]=='\n'||tool[i]=='\r')return 0;
   if(tool[i]=='*'||tool[i]=='"'||tool[i]=='$'||tool[i]=='`')quoted[n++]='*';
   quoted[n++]=tool[i];
  }
  quoted[n++]='"';quoted[n]=0;
 }
 lock=Lock((STRPTR)tool,ACCESS_READ);
 if(!lock)return 0;
 UnLock(lock);
 snprintf(logpath,sizeof logpath,"T:ZZClock-%08lx.log",(unsigned long)FindTask(NULL));
 input=Open("NIL:",MODE_OLDFILE);output=Open((STRPTR)logpath,MODE_NEWFILE);
 if(!input||!output){if(input)Close(input);if(output)Close(output);return 0;}
 snprintf(command,sizeof command,"%s %s",quoted,args);
 {
  struct Process *process=(struct Process*)FindTask(NULL);
  APTR previous=process->pr_WindowPtr;process->pr_WindowPtr=(APTR)-1;
  rc=SystemTags((STRPTR)command,SYS_Input,input,SYS_Output,output,NP_StackSize,32768,TAG_DONE);
  process->pr_WindowPtr=previous;
 }
 Close(input);Close(output);
 f=fopen(logpath,"r");if(f){size_t n=fread(zzclock_report,1,sizeof zzclock_report-1,f);zzclock_report[n]=0;fclose(f);}
 return rc==0;
}
static int zzclock_query(void){
 zzclock_valid=zzclock_helper("STATUS")&&zo_parse(zzclock_report,&zzclock_status);
 return zzclock_valid;
}
static const char *zzclock_event(ULONG id,int busy){
 ULONG selected=0;
 if(id!=ZZCLOCK_REFRESH&&id!=ZZCLOCK_APPLY)return NULL;
 get(zzclock_choice,MUIA_Cycle_Active,&selected);
 if(busy){strcpy(zzclock_message,"Close the emulator before changing the ARM clock.");goto done;}
 if(!zzclock_query()){
  strcpy(zzclock_message,"Clock control unavailable or ARM busy. Normal launch is available.");goto done;
 }
 if(id==ZZCLOCK_APPLY){
  if(selected>1||!zo_can_apply(&zzclock_status)){
   strcpy(zzclock_message,"Clock unchanged: firmware, activity or temperature check refused.");goto done;
  }
  if(!zzclock_helper(selected?"KEEP MHZ 800 NONCE 800171117":"END NONCE 800171117")){
   zzclock_valid=0;strcpy(zzclock_message,"Clock change refused. Refresh before trying again.");goto done;
  }
  if(!zzclock_query()||zzclock_status.mhz10!=(selected?8000u:6667u)){
   zzclock_valid=0;strcpy(zzclock_message,"Clock reply not verified. Check the ZZClock log in T:.");goto done;
  }
 }
 SetAttrs(zzclock_choice,MUIA_NoNotify,TRUE,MUIA_Cycle_Active,zzclock_status.mhz10==8000,TAG_DONE);
 snprintf(zzclock_message,sizeof zzclock_message,"Current: %u.%u MHz   Temperature: %u.%u C",
  zzclock_status.mhz10/10,zzclock_status.mhz10%10,zzclock_status.temp10/10,zzclock_status.temp10%10);
done:
 set(zzclock_text,MUIA_Text_Contents,(ULONG)zzclock_message);
 set(zzclock_choice,MUIA_Disabled,busy||!zzclock_valid);
 set(zzclock_apply,MUIA_Disabled,busy||!zzclock_valid||!zo_can_apply(&zzclock_status));
 return zzclock_message;
}
