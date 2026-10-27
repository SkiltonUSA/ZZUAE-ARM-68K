/* Included by the diagnostic host after its shared-memory/timer helpers.
 * LIVE uses an ARM-written P96 bitmap; COPY retains the slow pixel-array
 * baseline. Neither path writes directly into the Workbench screen bitmap. */
#include <intuition/intuitionbase.h>
#include <devices/inputevent.h>
#include <proto/intuition.h>
#include <proto/Picasso96.h>
#include <proto/expansion.h>
#include <proto/graphics.h>
#include <libraries/configvars.h>
#include <graphics/gfxbase.h>
#include "live.h"
#include "joystick.h"
#include "aspect.h"
#include "firmware_scanlines.h"
static struct zu_scanlines live_scan;
struct Library *LowLevelBase;
static unsigned live_keys,live_stick,live_joy_sent;
static int live_focused=1;
#include "frame_pacing.h"
#include "../common/rtg_mapping.h"
extern struct IntuitionBase *IntuitionBase;
extern struct Library *P96Base;
static struct Window *live_window;
static char live_title[80];
static struct Screen *live_screen;
static UWORD *live_pointer;
static ULONG live_stop_time;
static struct timerequest *live_timer;
static struct RenderInfo live_render;
struct GfxBase *GfxBase;
static struct BitMap *live_bitmap,*live_screen_bitmap;
static ULONG live_lock;
static int live_locked,live_direct,live_ready;
static unsigned live_width,live_height;
static UWORD *live_copy_pixels;
static unsigned short live_xmap[640],live_ymap[512];
static UBYTE *live_board;
static ULONG live_format,live_active,live_copy_start,live_copy_us,live_elapsed;
static ULONG live_frames,live_started,live_last,live_draw_us,live_inputs,live_overflow;
static int live_failed,live_quit;
static unsigned live_capture_pending,live_capture_active;
#include "capture.h"
#include "presentation_host.h"
#include "mouse_capture_host.h"
/* Fullscreen owns a temporary Intuition screen, never ScreenMode prefs.
 * Keep the same validated offscreen ARM bitmap and WaitBlit handoff. */
static int live_open_screen(void) {
    if(fullscreen_mode){
        live_width=fullscreen_mode==2?640:320;live_height=fullscreen_mode==2?512:256;
        ULONG mode=p96BestModeIDTags(P96BIDTAG_NominalWidth,live_width,
            P96BIDTAG_NominalHeight,live_height,P96BIDTAG_Depth,32,TAG_DONE);
        if(mode==0xffffffffu || p96GetModeIDAttr(mode,P96IDA_WIDTH)!=live_width ||
           p96GetModeIDAttr(mode,P96IDA_HEIGHT)!=live_height || p96GetModeIDAttr(mode,P96IDA_DEPTH)!=32){
            printf("ERROR Fullscreen needs an installed %ux%u 32-bit RTG mode\n",live_width,live_height);return 0;
        }
        ULONG format=p96GetModeIDAttr(mode,P96IDA_RGBFORMAT),error=0;
        if(format!=RGBFB_B8G8R8A8 && format!=RGBFB_A8R8G8B8){
            puts("ERROR Fullscreen mode must use a supported 32-bit pixel format");return 0;
        }
        live_screen_bitmap=p96AllocBitMap(live_width,live_height,32,BMF_DISPLAYABLE|BMF_CLEAR,NULL,format);
        if(!live_screen_bitmap){puts("ERROR Cannot allocate fullscreen RTG bitmap");return 0;}
        live_screen=OpenScreenTags(NULL,SA_DisplayID,mode,SA_BitMap,(ULONG)live_screen_bitmap,SA_ErrorCode,(ULONG)&error,
            SA_Width,live_width,SA_Height,live_height,SA_Depth,32,SA_Type,CUSTOMSCREEN,
            SA_Quiet,TRUE,SA_ShowTitle,FALSE,SA_AutoScroll,FALSE,SA_Title,(ULONG)"ZZUAE",TAG_DONE);
        if(!live_screen){printf("ERROR Cannot open fullscreen RTG screen: %u\n",error);return 0;}
    } else {
        live_screen=LockPubScreen(NULL);if(!live_screen)return 0;
        if(live_screen->Width<=32 || live_screen->Height<=64 ||
           !ul_view_size(live_screen->Width-32,live_screen->Height-64,&live_width,&live_height)){
            puts("ERROR Workbench is too small for a 320x240 display area");return 0;
        }
    }
    return 1;
}
static int live_open(struct timerequest *timer) {
    live_timer=timer;
    if(joystick_mode){LowLevelBase=OpenLibrary("lowlevel.library",40);if(!LowLevelBase){puts("ERROR Joystick needs lowlevel.library V40; select Joystick Off");return 0;}}
    live_direct=(boot_options&UAE_OPT_DIRECT)!=0;
    GfxBase=(struct GfxBase *)OpenLibrary("graphics.library",39);if(!GfxBase)return 0;
    if(!live_open_screen())return 0;
    if(!live_palette())return 0;
    ul_scale_map(live_xmap,live_width,640);ul_scale_map(live_ymap,live_height,256);
    if(live_direct) {
        struct ConfigDev *card=FindConfigDev(NULL,0x6d6e,4);if(!card)return 0;
        live_board=card->cd_BoardAddr;
        live_format=p96GetBitMapAttr(live_screen->RastPort.BitMap,P96BMA_RGBFORMAT);
        if(live_format!=RGBFB_B8G8R8A8 && live_format!=RGBFB_A8R8G8B8){
            puts("LIVE direct mode requires a 32-bit RTG Workbench");return 0;
        }
        live_bitmap=p96AllocBitMap(live_width,live_height,32,BMF_DISPLAYABLE|BMF_CLEAR,
            live_screen->RastPort.BitMap,live_format);
        if(!live_bitmap || !p96GetBitMapAttr(live_bitmap,P96BMA_ISONBOARD))return 0;
    }
    snprintf(live_title,sizeof(live_title),"ZZUAE - %s - %sF9 scanlines / F10 exit",profile==0?"A1000":profile==2?"A500 Plus":profile==3?"A600":"A500",frame_limit?"F5 capture / ":"");
    live_window=OpenWindowTags(NULL,fullscreen_mode?WA_CustomScreen:WA_PubScreen,(ULONG)live_screen,
        WA_Title,fullscreen_mode?0:(ULONG)live_title,
        WA_Left,fullscreen_mode?0:16,WA_Top,fullscreen_mode?0:30,WA_InnerWidth,live_width,WA_InnerHeight,live_height+(fullscreen_mode?0:UL_STATUS_HEIGHT),
        WA_Borderless,fullscreen_mode,WA_Backdrop,fullscreen_mode,
        WA_DragBar,!fullscreen_mode,WA_DepthGadget,!fullscreen_mode,WA_CloseGadget,!fullscreen_mode,
        WA_Activate,TRUE,WA_SimpleRefresh,TRUE,WA_ReportMouse,TRUE,WA_RMBTrap,TRUE,WA_MouseQueue,32,
        WA_IDCMP,IDCMP_CLOSEWINDOW|IDCMP_REFRESHWINDOW|IDCMP_RAWKEY|
            IDCMP_MOUSEBUTTONS|IDCMP_MOUSEMOVE|IDCMP_DELTAMOVE|IDCMP_INACTIVEWINDOW|IDCMP_ACTIVEWINDOW,TAG_DONE);
    if(!live_window)return 0;
    live_pointer=AllocMem(12,MEMF_CHIP|MEMF_CLEAR);
    if(!live_pointer)return 0;
    if(!fullscreen_mode && !live_mouse_open())return 0;
    if(fullscreen_mode){
        SetPointer(live_window,live_pointer,1,16,0,0);
        ScreenToFront(live_screen);
    }
    live_border();
    memset(&live_render,0,sizeof(live_render));
    if(!live_direct){
        live_copy_pixels=AllocVec(live_width*live_height*2,MEMF_ANY);
        if(!live_copy_pixels)return 0;
    }
    live_render.Memory=live_copy_pixels;
    live_render.BytesPerRow=live_width*2;live_render.RGBFormat=RGBFB_R5G6B5PC;
    printf("STARTUP %s: %ux%u %s\n",fullscreen_mode?"Fullscreen":"Window",live_width,live_height,fullscreen_mode?"(native PAL)":"(4:3)");
    if(audio_mode)printf("STARTUP PAL audio clock; display limit %u FPS\n",display_rate);
    else printf("STARTUP Frame rate: %s\n",frame_period==40000?"25 FPS":frame_period==33334?"30 FPS":frame_period==20000?"50 FPS":"MAX FPS (uncapped)");
    if(fullscreen_mode==1){
        struct ConfigDev *card=FindConfigDev(NULL,0x6d6e,4);
        if(!card)return 0;
        zu_scan_begin(&live_scan,(volatile uint16_t*)((UBYTE*)card->cd_BoardAddr+ZU_SCAN_REGISTER),1,scanline_mode);
        printf("STARTUP ZZScanlines firmware: %s (off on exit)\n",zu_scan_names[live_scan.mode]);
    } else puts("STARTUP ZZScanlines requires low-resolution fullscreen; disabled for window/HiRes");
    live_started=live_last=us();ul_fps_start(&live_fps,live_started);live_fps_paint();live_status_paint(1);return 1;
}
static void live_unlock(void) {
    if(live_locked){p96UnlockBitMap(live_bitmap,live_lock);live_locked=0;}
}
static void live_paint(void) {
    BltBitMapRastPort(live_bitmap,0,0,live_window->RPort,
        live_window->BorderLeft,live_window->BorderTop,live_width,live_height,0xc0);
    WaitBlit();live_border();
}
static void live_stop(void) {
    if(live_quit)return;
    live_quit=1;live_stop_time=us();ad_put(shared,ZZ_STOP,1);
    syncio->push(shared+ZZ_STOP,4,NULL);syncio->barrier(NULL);
    if(!live_locked)live_status_paint(0);
}
static void live_abort(void) {live_failed=1;live_stop();}
static void live_input(unsigned kind,int value) {
    volatile uint8_t *p=shared+UAE_LIVE;
    ULONG head=ad_get(p,UL_HEAD),tail;
    syncio->pull(p+UL_TAIL,4,NULL);tail=ad_get(p,UL_TAIL);
    /* Never drop a release silently: stop rather than leave a guest key held. */
    if(!ul_room(head,tail)){live_overflow++;live_abort();return;}
    ad_put(p,UL_EVENTS+(head%UL_CAPACITY)*4,ul_event(kind,value));
    syncio->push(p+UL_EVENTS+(head%UL_CAPACITY)*4,4,NULL);syncio->barrier(NULL);
    ad_put(p,UL_HEAD,head+1);syncio->push(p+UL_HEAD,4,NULL);syncio->barrier(NULL);
    live_inputs++;
}
static void live_joystick(void){
    unsigned now=uj_merge(live_keys,live_stick),changes=now^live_joy_sent,i;
    for(i=0;i<7;i++)if(changes&(1u<<i))live_input(UL_JOY,i|((now&(1u<<i))?0:128));
    live_joy_sent=now;
}
static void live_poll(void) {
    struct IntuiMessage *m;
    ULONG seq,now;
    volatile uint8_t *p=shared+UAE_LIVE;
    if(live_quit)return;
    if(live_active) {
        syncio->pull(p+UL_DONE,8,NULL);
        if(ad_get(p,UL_DONE)!=live_active) {
            if(SetSignal(0,SIGBREAKF_CTRL_C)&SIGBREAKF_CTRL_C)live_stop();
            return; /* No Intuition drawing while the bitmap is locked. */
        }
        live_copy_us+=us()-live_copy_start;live_unlock();
        if(ad_get(p,UL_ERROR)){printf("LIVE ARM render error=%u\n",(ULONG)ad_get(p,UL_ERROR));live_abort();return;}
        if(live_capture_active){live_capture();live_capture_active=0;}
        /* Release the CPU frame before the host blit. The ARM can emulate its
         * next frame in private RAM, but cannot touch this bitmap again until
         * a NEW grant, issued only after WaitBlit below has completed. */
        syncio->barrier(NULL);ad_put(p,UL_ACK,live_active);syncio->push(p+UL_ACK,4,NULL);
        syncio->barrier(NULL);live_active=0;
        now=us();live_paint();ul_fps_frame(&live_fps,us());live_fps_paint();live_draw_us+=us()-now;
        live_frames++;live_ready=1;live_status_paint(0);
        if(live_frames==1)puts("STARTUP First frame ready");
        if(live_frames%250==0)printf("PROGRESS frames=%u elapsed_us=%u\n",live_frames,(ULONG)(us()-live_started));
    }
    while((m=(struct IntuiMessage *)GetMsg(live_window->UserPort))) {
        ULONG cl=m->Class;UWORD code=m->Code,qual=m->Qualifier;
        int x=m->MouseX,y=m->MouseY;ReplyMsg((struct Message *)m);
        if(cl==IDCMP_CLOSEWINDOW)live_stop();
        if(cl==IDCMP_ACTIVEWINDOW)live_focused=1;
        if(cl==IDCMP_INACTIVEWINDOW){if(!fullscreen_mode)live_mouse_release(1);live_focused=0;live_keys=live_stick=live_joy_sent=0;live_input(UL_RESET_INPUT,0);}
        if(cl==IDCMP_RAWKEY && !(qual&IEQUALIFIER_REPEAT)) {
            unsigned key=code&127,up=code&128;
            if(key==0x59){if(!up)live_stop();}
            else if(key==0x57 && !fullscreen_mode){if(!up)live_mouse_release(1);}
            else if(key==0x54 && frame_limit){if(!up)live_capture_pending=1;}
            else if(key==0x58){if(!up){
                if(live_scan.regs){
                    zu_scan_next(&live_scan);
                    printf("STARTUP ZZScanlines firmware: %s\n",zu_scan_names[live_scan.mode]);
                } else puts("STARTUP ZZScanlines requires low-resolution fullscreen");
            }}
            else {
                live_input(UL_KEY,code);
                if(key>=0x4c && key<=0x4f) {
                    static const unsigned dirs[]={2,3,1,0};
                    unsigned mask=1u<<dirs[key-0x4c];
                    if(up)live_keys&=~mask;else live_keys|=mask;
                    live_joystick();
                }
                if(key==0x64){if(up)live_keys&=~16u;else live_keys|=16u;live_joystick();} /* left Alt = joystick fire */
            }
        }
        if(cl==IDCMP_MOUSEBUTTONS && !fullscreen_mode)live_mouse_click(code);
        if(cl==IDCMP_MOUSEBUTTONS && fullscreen_mode) {
            if(code==SELECTDOWN || code==SELECTUP)live_input(UL_LEFT,code==SELECTDOWN);
            if(code==MENUDOWN || code==MENUUP)live_input(UL_RIGHT,code==MENUDOWN);
        }
        /* Intuition deltas continue even when its pointer reaches an edge.
         * Never derive guest movement from the clamped host pointer position. */
        if(cl==IDCMP_MOUSEMOVE && live_focused && fullscreen_mode) {
            if(x)live_input(UL_MOUSE_X,x);
            if(y)live_input(UL_MOUSE_Y,y);
        }
        if(cl==IDCMP_REFRESHWINDOW){
            BeginRefresh(live_window);
            live_border();
            if(live_ready){
                if(live_direct)live_paint();
                else p96WritePixelArray(&live_render,0,0,live_window->RPort,live_window->BorderLeft,live_window->BorderTop,live_width,live_height);
            }
            live_fps_paint();live_status_paint(1);
            EndRefresh(live_window,TRUE);
        }
    }
    if(!fullscreen_mode)live_mouse_drain();
    if(live_focused&&LowLevelBase){live_stick=uj_sample(ReadJoyPort(1));live_joystick();}
    if(SetSignal(0,SIGBREAKF_CTRL_C)&SIGBREAKF_CTRL_C)live_stop();
    if(live_quit)return;
    syncio->pull(p+UL_FRAME,4,NULL);seq=ad_get(p,UL_FRAME);now=us();
    if(seq!=ad_get(p,UL_ACK) && zu_frame_due(now,live_last,frame_period)) {
        ULONG start=us();
        if(live_direct) {
            struct RenderInfo ri;ULONG address,span,pitch,format,nonce;
            memset(&ri,0,sizeof(ri));live_lock=p96LockBitMap(live_bitmap,(UBYTE*)&ri,sizeof(ri));live_locked=1;
            pitch=ri.BytesPerRow;format=live_format==RGBFB_B8G8R8A8?RTG_BGRA32:RTG_ARGB32;
            if(!ri.Memory || (ULONG)ri.RGBFormat!=live_format || pitch<live_width*4 || pitch>4096 ||
               !p96GetBitMapAttr(live_bitmap,P96BMA_ISONBOARD) ||
               (ULONG)ri.Memory<(ULONG)live_board+0x10000u ||
               (ULONG)ri.Memory>(ULONG)live_board+0x4000000u-live_height*pitch){live_abort();return;}
            address=(ULONG)ri.Memory-(ULONG)live_board+0x1f0000u;
            span=rtg_span_size(address,pitch,format,live_width,live_height);if(!span){live_abort();return;}
            nonce=ad_get(shared,ZZ_CONTROL)^seq^0x55414531u;
            ad_put(ri.Memory,0,nonce);ad_put(ri.Memory,span-4,nonce^0x31415926u);
            syncio->push(ri.Memory,4,NULL);syncio->push((UBYTE*)ri.Memory+span-4,4,NULL);
            ad_put(p,UL_ADDRESS,address);ad_put(p,UL_PITCH,pitch);
            ad_put(p,UL_FORMAT,format);ad_put(p,UL_NONCE,nonce);
            live_capture_active=live_capture_pending;live_capture_pending=0;
            ad_put(p,UL_SCAN_RESERVED,0);ad_put(p,UL_CAPTURE,live_capture_active);
            ad_put(p,UL_WIDTH,live_width);ad_put(p,UL_HEIGHT,live_height);
            syncio->push(p+UL_ADDRESS,32,NULL);syncio->barrier(NULL);
            ad_put(p,UL_GRANT,seq);syncio->push(p+UL_GRANT,4,NULL);syncio->barrier(NULL);
            live_active=seq;live_copy_start=start;live_last=now;return;
        }
        syncio->pull(shared+UAE_FRAME,640*256*2,NULL);
        for(unsigned y=0;y<live_height;y++){
            const volatile UWORD *src=(const volatile UWORD *)(shared+UAE_FRAME+live_ymap[y]*1280);
            UWORD *row=live_copy_pixels+y*live_width;
            for(unsigned x=0;x<live_width;x++)row[x]=src[live_xmap[x]];
        }
        p96WritePixelArray(&live_render,0,0,live_window->RPort,
            live_window->BorderLeft,live_window->BorderTop,live_width,live_height);
        live_border();ul_fps_frame(&live_fps,us());live_fps_paint();
        live_draw_us+=us()-start;live_frames++;live_last=now;live_ready=1;live_status_paint(0);
        if(live_frames==1)puts("STARTUP First frame ready");
        if(live_capture_pending){live_capture();live_capture_pending=0;}
        syncio->barrier(NULL);ad_put(p,UL_ACK,seq);syncio->push(p+UL_ACK,4,NULL);
        syncio->barrier(NULL);
    }
}
static void live_idle(void) {
    live_timer->tr_node.io_Command=TR_ADDREQUEST;
    live_timer->tr_time.tv_secs=0;live_timer->tr_time.tv_micro=1000;
    DoIO((struct IORequest *)live_timer);
}
static void live_close(void) {
    live_mouse_close();
    /* Called by the launcher's FF_DIRECT cleanup, AFTER synchronous Core1 reset. */
    live_unlock();
    if(live_scan.regs){zu_scan_end(&live_scan);puts("ZZSCANLINES cleanup: disabled");}
    if(live_window) {
        if(!fullscreen_mode)printf("STATUS disk_on=%u disk_off=%u\n",live_disk_on,live_disk_off);
        printf("LIVE direct=%u frames=%u elapsed_us=%u p96_us=%u copy_wait_us=%u input_events=%u overflow=%u user_exit=%u failed=%u\n",
            live_direct,live_frames,live_elapsed,live_draw_us,live_copy_us,live_inputs,live_overflow,live_quit,live_failed);
        if(live_pointer)ClearPointer(live_window);
        CloseWindow(live_window);live_window=NULL;
    }
    if(live_pointer){FreeMem(live_pointer,12);live_pointer=NULL;}
    if(live_copy_pixels){FreeVec(live_copy_pixels);live_copy_pixels=NULL;}
    if(live_bitmap){p96FreeBitMap(live_bitmap);live_bitmap=NULL;}
    if(live_screen && !fullscreen_mode)for(unsigned i=0;i<8;i++)if(live_pens[i]>=0){ReleasePen(live_screen->ViewPort.ColorMap,live_pens[i]);live_pens[i]=-1;}
    if(live_screen){if(fullscreen_mode)CloseScreen(live_screen);else UnlockPubScreen(NULL,live_screen);live_screen=NULL;}
    if(live_screen_bitmap){p96FreeBitMap(live_screen_bitmap);live_screen_bitmap=NULL;}
    if(LowLevelBase){CloseLibrary(LowLevelBase);LowLevelBase=NULL;}
    if(GfxBase){CloseLibrary((struct Library*)GfxBase);GfxBase=NULL;}
}
