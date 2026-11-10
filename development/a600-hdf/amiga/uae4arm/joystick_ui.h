/* Native port-2 tester. Drawing follows the project's ZZDosBox MUI tester. */
#include "joystick.h"
#include <proto/graphics.h>
#include <graphics/gfxbase.h>
struct Library *LowLevelBase;
struct GfxBase *GfxBase;
static Object *joywin,*joy_status,*joy_diagram;
static struct MUI_CustomClass *joy_class;
static int joy_testing;
static ULONG joy_last=~0ul;
struct joy_data {unsigned bits;LONG green;};
/* Same bit order as the host/ARM input wire: R, L, U, D, fire 1/2/3. */
static const short joy_xy[7][2]={{164,80},{44,80},{104,28},{104,132},{260,80},{324,80},{388,80}};
static const char *joy_labels[]={"Right","Left","Up","Down","1","2","3"};
static ULONG joy_dispatch(struct IClass *cl __asm("a0"),Object *obj __asm("a2"),Msg msg __asm("a1")){
 struct joy_data *d=INST_DATA(cl,obj);ULONG result;
 switch(msg->MethodID){
 case MUIM_Setup:
  d->green=-1;if(!DoSuperMethodA(cl,obj,msg))return FALSE;
  d->green=ObtainBestPen(_screen(obj)->ViewPort.ColorMap,0x44444444u,0xccccccccu,0x66666666u,TAG_DONE);return TRUE;
 case MUIM_Cleanup:
  if(d->green>=0)ReleasePen(_screen(obj)->ViewPort.ColorMap,d->green);
  d->green=-1;break;
 case MUIM_AskMinMax:{struct MUIP_AskMinMax *m=(struct MUIP_AskMinMax*)msg;
  result=DoSuperMethodA(cl,obj,msg);
  m->MinMaxInfo->MinWidth+=420;m->MinMaxInfo->DefWidth+=420;m->MinMaxInfo->MaxWidth=MUI_MAXMAX;
  m->MinMaxInfo->MinHeight+=160;m->MinMaxInfo->DefHeight+=160;m->MinMaxInfo->MaxHeight+=160;return result;}
 case MUIM_Draw:{unsigned i;struct RastPort *rp;LONG left,top;
  result=DoSuperMethodA(cl,obj,msg);
  if(!(((struct MUIP_Draw*)msg)->flags&(MADF_DRAWOBJECT|MADF_DRAWUPDATE)))return result;
  rp=_rp(obj);left=_mleft(obj)+(_mwidth(obj)-420)/2;top=_mtop(obj);
  SetAPen(rp,_pens(obj)[MPEN_BACKGROUND]);RectFill(rp,_mleft(obj),top,_mright(obj),_mbottom(obj));
  for(i=0;i<7;i++){
   LONG x=left+joy_xy[i][0],y=top+joy_xy[i][1],rx=i<4?32:22,ry=i<4?18:22,dy;
   const char *label=joy_labels[i];ULONG len=strlen(label);
   SetAPen(rp,(d->bits&(1u<<i))&&d->green>=0?d->green:_pens(obj)[MPEN_FILL]);
   for(dy=-ry;dy<=ry;dy++){
    LONG dx=rx;while(dx*dx*ry*ry+dy*dy*rx*rx>rx*rx*ry*ry)dx--;
    Move(rp,x-dx,y+dy);Draw(rp,x+dx,y+dy);
   }
   SetAPen(rp,_pens(obj)[MPEN_SHADOW]);DrawEllipse(rp,x,y,rx,ry);
   SetAPen(rp,_pens(obj)[MPEN_TEXT]);Move(rp,x-TextLength(rp,label,len)/2,y+rp->TxBaseline-rp->TxHeight/2);Text(rp,label,len);
   if(i>=4){const char *name=i==4?"Fire 1":i==5?"Fire 2":"Fire 3";
    Move(rp,x-TextLength(rp,name,6)/2,y+37);Text(rp,name,6);}
  }return result;}
 }
 return DoSuperMethodA(cl,obj,msg);
}
static void joy_sample(void){
 ULONG raw=LowLevelBase?ReadJoyPort(1):0,type=raw&JP_TYPE_MASK;
 struct joy_data *d=INST_DATA(joy_class->mcc_Class,joy_diagram);
 if(raw==joy_last)return;joy_last=raw;d->bits=uj_sample(raw);
 MUI_Redraw(joy_diagram,MADF_DRAWOBJECT);
 set(joy_status,MUIA_Text_Contents,(ULONG)(!LowLevelBase?"lowlevel.library V40 unavailable":
  type==JP_TYPE_JOYSTK?"Standard joystick - port 2":type==JP_TYPE_GAMECTLR?"Controller - port 2":
  type==JP_TYPE_MOUSE?"Mouse detected on port 2":"Port 2 - waiting for input"));
}
static Object *joy_window(void){return WindowObject,MUIA_Window_Title,(ULONG)"ZZUAE Joystick test",
 MUIA_Window_ID,0x5a55414a,MUIA_Window_Width,440,
 WindowContents,VGroup,Child,joy_status=readout("Amiga game port 2"),
 Child,joy_diagram=NewObject(joy_class->mcc_Class,NULL,TAG_DONE),End,End;}
static void joy_close(void){set(joywin,MUIA_Window_Open,FALSE);joy_testing=0;}
