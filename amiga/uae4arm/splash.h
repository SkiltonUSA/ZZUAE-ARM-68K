/* Native splashes: paint immediately instead of relying on MUI redraw dispatch. */
#include <proto/graphics.h>
#include "splash-art.h"
static struct Window *loading_window;
static struct Screen *splash_screen;
static struct TextFont *splash_font;
static LONG splash_pens[128];
static void splash_text(struct Window*w,int x,int y,const char*s){Move(w->RPort,x,w->BorderTop+y);Text(w->RPort,(STRPTR)s,strlen(s));}
static void splash_draw(struct Window*w,int loading){
 struct RastPort*rp=w->RPort;unsigned x,y;
 if(splash_font)SetFont(rp,splash_font);
 SetAPen(rp,0);RectFill(rp,w->BorderLeft,w->BorderTop,w->Width-w->BorderRight-1,w->Height-w->BorderBottom-1);
 for(y=0;y<128;y++)for(x=0;x<128;x++){
  unsigned v=0;for(unsigned bit=0;bit<SPLASH_DEPTH;bit++)if(splash_body[(y*SPLASH_DEPTH+bit)*16+x/8]&(128>>(x&7)))v|=1u<<bit;
  if(v){SetAPen(rp,splash_pens[v]>=0?splash_pens[v]:1);WritePixel(rp,14+x,w->BorderTop+12+y);}
 }
 SetAPen(rp,1);SetDrMd(rp,JAM1);
 splash_text(w,160,24,loading?"LOADING":"ZZUAE");splash_text(w,160,42,"Version " ZU_VERSION);
 splash_text(w,160,60,"Amiga OCS/ECS/AGA on ZZ9000");
 splash_text(w,160,86,"Amiga+Esc   Menu / release mouse");
 splash_text(w,160,102,"F9          Fullscreen scanlines");
 splash_text(w,160,118,"Amiga+F10   Exit to launcher");
 splash_text(w,160,134,config.testing?"F5          Test screenshot":"");
 splash_text(w,160,151,loading?"Close this window to cancel.":"Starting launcher...");
}
static void splash_close(struct Window*w){
 if(w)CloseWindow(w);
 if(splash_screen){for(unsigned i=1;i<128;i++)if(splash_pens[i]>=0)ReleasePen(splash_screen->ViewPort.ColorMap,splash_pens[i]);UnlockPubScreen(NULL,splash_screen);splash_screen=NULL;}
 if(splash_font){CloseFont(splash_font);splash_font=NULL;}
}
static struct Window*splash_create(int loading){
 struct Window*w;struct TextAttr ta={(STRPTR)"topaz.font",8,0,0};
 splash_screen=LockPubScreen(NULL);if(!splash_screen)return NULL;
 for(unsigned i=0;i<128;i++)splash_pens[i]=-1;
 for(unsigned i=1;i<128;i++)splash_pens[i]=ObtainBestPen(splash_screen->ViewPort.ColorMap,splash_colours[i*3],splash_colours[i*3+1],splash_colours[i*3+2],TAG_DONE);
 splash_font=OpenFont(&ta);
 w=OpenWindowTags(NULL,WA_Title,(ULONG)(loading?"ZZUAE Loading":"ZZUAE Startup"),WA_PubScreen,(ULONG)splash_screen,
 WA_Left,(splash_screen->Width-536)/2,WA_Top,(splash_screen->Height-190)/2,WA_InnerWidth,528,WA_InnerHeight,163,
 WA_CloseGadget,TRUE,WA_DragBar,TRUE,WA_DepthGadget,TRUE,WA_Activate,TRUE,WA_IDCMP,IDCMP_CLOSEWINDOW|IDCMP_REFRESHWINDOW,TAG_DONE);
 if(w)splash_draw(w,loading);else splash_close(NULL);return w;
}
static int splash_events(struct Window*w,int loading){
 struct IntuiMessage*m;int close=0;if(!w)return 0;
 while((m=(struct IntuiMessage*)GetMsg(w->UserPort))){ULONG cl=m->Class;ReplyMsg((struct Message*)m);
 if(cl==IDCMP_CLOSEWINDOW)close=1;
 if(cl==IDCMP_REFRESHWINDOW){BeginRefresh(w);splash_draw(w,loading);EndRefresh(w,TRUE);}}
 return close;
}
static ULONG splash_signal(void){return loading_window?1ul<<loading_window->UserPort->mp_SigBit:0;}
static void loading_end(void){splash_close(loading_window);loading_window=NULL;set(win,MUIA_Window_Sleep,FALSE);}
static void loading_begin(void){set(win,MUIA_Window_Sleep,TRUE);loading_window=splash_create(1);}
static void startup_splash(void){
 struct Window*w=splash_create(0);if(!w)return;
 timer->tr_node.io_Command=TR_ADDREQUEST;timer->tr_time.tv_secs=3;timer->tr_time.tv_micro=0;
 SendIO((struct IORequest*)timer);timer_pending=1;
 while(!CheckIO((struct IORequest*)timer)&&!splash_events(w,0))Wait((1ul<<w->UserPort->mp_SigBit)|(1ul<<timerport->mp_SigBit));
 if(!CheckIO((struct IORequest*)timer))AbortIO((struct IORequest*)timer);
 WaitIO((struct IORequest*)timer);timer_pending=0;splash_close(w);
}
