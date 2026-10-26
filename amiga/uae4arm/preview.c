/* Static diagnostic capture viewer. The ARM worker has already stopped. */
#include <exec/memory.h>
#include <graphics/gfxbase.h>
#include <intuition/intuitionbase.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <proto/graphics.h>
#include <proto/intuition.h>
#include <proto/Picasso96.h>
#include <stdio.h>
#include <string.h>

struct GfxBase *GfxBase;
struct IntuitionBase *IntuitionBase;
struct Library *P96Base;

int main(int argc, char **argv) {
    struct Screen *screen=NULL;
    struct Window *window=NULL;
    struct RenderInfo render;
    BPTR file=0;
    UBYTE *raw=NULL, *rgb=NULL;
    ULONG n, v;
    int rc=20, quit=0;
    if(argc!=2){puts("Usage: ZZUAEPreview <640x256 RGB565 capture>");return 20;}
    GfxBase=(struct GfxBase *)OpenLibrary("graphics.library",39);
    IntuitionBase=(struct IntuitionBase *)OpenLibrary("intuition.library",39);
    P96Base=OpenLibrary("Picasso96API.library",2);
    if(!GfxBase || !IntuitionBase || !P96Base)goto done;
    raw=AllocVec(640*256*2,MEMF_PUBLIC);
    rgb=AllocVec(640*256*3,MEMF_PUBLIC);
    if(!raw || !rgb)goto done;
    file=Open(argv[1],MODE_OLDFILE);
    if(!file || Read(file,raw,640*256*2)!=640*256*2)goto done;
    Close(file);file=0;
    for(n=0;n<640*256;n++){
        v=raw[n*2]|((ULONG)raw[n*2+1]<<8);
        rgb[n*3]=(v>>11)*255/31;
        rgb[n*3+1]=((v>>5)&63)*255/63;
        rgb[n*3+2]=(v&31)*255/31;
    }
    screen=LockPubScreen(NULL);if(!screen)goto done;
    window=OpenWindowTags(NULL,WA_PubScreen,(ULONG)screen,
        WA_Title,(ULONG)"ZZUAE - captured ARM boot frame",
        WA_Left,16,WA_Top,30,WA_InnerWidth,640,WA_InnerHeight,256,
        WA_DragBar,TRUE,WA_DepthGadget,TRUE,WA_CloseGadget,TRUE,
        WA_Activate,TRUE,WA_SimpleRefresh,TRUE,
        WA_IDCMP,IDCMP_CLOSEWINDOW|IDCMP_REFRESHWINDOW,TAG_DONE);
    if(!window)goto done;
    memset(&render,0,sizeof(render));
    render.Memory=rgb;render.BytesPerRow=640*3;render.RGBFormat=RGBFB_R8G8B8;
    p96WritePixelArray(&render,0,0,window->RPort,window->BorderLeft,window->BorderTop,640,256);
    while(!quit){
        struct IntuiMessage *message;
        ULONG signals=Wait((1UL<<window->UserPort->mp_SigBit)|SIGBREAKF_CTRL_C);
        if(signals&SIGBREAKF_CTRL_C)quit=1;
        while((message=(struct IntuiMessage *)GetMsg(window->UserPort))){
            ULONG cl=message->Class;ReplyMsg((struct Message *)message);
            if(cl==IDCMP_CLOSEWINDOW)quit=1;
            if(cl==IDCMP_REFRESHWINDOW){
                BeginRefresh(window);
                p96WritePixelArray(&render,0,0,window->RPort,window->BorderLeft,window->BorderTop,640,256);
                EndRefresh(window,TRUE);
            }
        }
    }
    rc=0;
done:
    if(window)CloseWindow(window);
    if(screen)UnlockPubScreen(NULL,screen);
    if(file)Close(file);
    if(rgb)FreeVec(rgb);
    if(raw)FreeVec(raw);
    if(P96Base)CloseLibrary(P96Base);
    if(IntuitionBase)CloseLibrary((struct Library *)IntuitionBase);
    if(GfxBase)CloseLibrary((struct Library *)GfxBase);
    return rc;
}
