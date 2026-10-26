/* Native MUI splash lifecycle, adapted from the ZZDosBox launcher. */
#include "splash-art.h"
enum {ID_SPLASH_DISMISS=700};
static Object *loading_window;
static Object *splash_create(int loading){
    Object *window,*button;
    window=WindowObject,MUIA_Window_Title,(ULONG)(loading?"ZZUAE Loading":"ZZUAE Startup"),
        MUIA_Window_Borderless,TRUE,MUIA_Window_CloseGadget,FALSE,
        MUIA_Window_SizeGadget,FALSE,MUIA_Window_DepthGadget,FALSE,
        MUIA_Window_DragBar,FALSE,MUIA_Window_Activate,TRUE,
        MUIA_Window_LeftEdge,MUIV_Window_LeftEdge_Centered,
        MUIA_Window_TopEdge,MUIV_Window_TopEdge_Centered,
        WindowContents,HGroup,GroupFrame,InnerSpacing(18,18),MUIA_Group_Spacing,18,
            Child,BodychunkObject,MUIA_FixWidth,128,MUIA_FixHeight,128,
                MUIA_Bitmap_Width,128,MUIA_Bitmap_Height,128,MUIA_Bodychunk_Depth,SPLASH_DEPTH,
                MUIA_Bodychunk_Body,(ULONG)splash_body,MUIA_Bodychunk_Compression,0,
                MUIA_Bodychunk_Masking,0,MUIA_Bitmap_SourceColors,(ULONG)splash_colours,
                MUIA_Bitmap_Transparent,0,End,
            Child,VGroup,MUIA_Group_Spacing,8,
                Child,TextObject,MUIA_Font,MUIV_Font_Big,
                    MUIA_Text_Contents,(ULONG)(loading?"LOADING":"ZZUAE"),End,
                Child,TextObject,MUIA_Text_Contents,(ULONG)"Version " ZU_VERSION,End,
                Child,TextObject,MUIA_Text_Contents,(ULONG)"Amiga OCS/ECS Emulation on ZZ9000",End,
                Child,ColGroup(2),Child,label("F5"),Child,TextObject,MUIA_Text_Contents,(ULONG)"Screenshot",End,
                    Child,label("F9"),Child,TextObject,MUIA_Text_Contents,(ULONG)"Cycle scanlines",End,
                    Child,label("F10"),Child,TextObject,MUIA_Text_Contents,(ULONG)"Exit to launcher",End,End,
                Child,button=SimpleButton(loading?"Cancel":"Continue"),End,
        End,End;
    if(window){
        DoMethod(app,OM_ADDMEMBER,(ULONG)window);
        notify(button,MUIA_Pressed,FALSE,loading?MUIV_Application_ReturnID_Quit:ID_SPLASH_DISMISS);
        set(window,MUIA_Window_Open,TRUE);
    }
    return window;
}
static void splash_close(Object *window){
    if(!window)return;
    set(window,MUIA_Window_Open,FALSE);
    DoMethod(app,OM_REMMEMBER,(ULONG)window);MUI_DisposeObject(window);
}
static void loading_end(void){
    splash_close(loading_window);loading_window=NULL;set(win,MUIA_Window_Sleep,FALSE);
}
static void loading_begin(void){set(win,MUIA_Window_Sleep,TRUE);loading_window=splash_create(1);}
static void startup_splash(void){
    Object *window=splash_create(0);ULONG signals,id;
    if(!window)return;
    timer->tr_node.io_Command=TR_ADDREQUEST;timer->tr_time.tv_secs=3;timer->tr_time.tv_micro=0;
    SendIO((struct IORequest*)timer);timer_pending=1;
    for(;;){
        id=DoMethod(app,MUIM_Application_NewInput,(ULONG)&signals);
        if(id==ID_SPLASH_DISMISS || CheckIO((struct IORequest*)timer))break;
        if(!id && signals)Wait(signals|(1ul<<timerport->mp_SigBit));
    }
    if(!CheckIO((struct IORequest*)timer))AbortIO((struct IORequest*)timer);
    WaitIO((struct IORequest*)timer);timer_pending=0;splash_close(window);
}
