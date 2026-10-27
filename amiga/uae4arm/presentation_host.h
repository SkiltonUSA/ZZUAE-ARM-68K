/* Draw only in the host-owned window, after the ARM bitmap is unlocked. */
#include "presentation.h"
static struct ul_fps live_fps;
static LONG live_pens[8]={-1,-1,-1,-1,-1,-1,-1,-1};
static const ULONG live_colours[8]={0x101820,0xe8e4d9,0x46505a,0xd52932,0xf39724,0xf5d539,0x3baf63,0x408bd0};
static int live_palette(void){
    for(unsigned i=0;i<(fullscreen_mode?8u:2u);i++){
        ULONG c=live_colours[i];
        ULONG r=((c>>16)&255)*0x01010101u,g=((c>>8)&255)*0x01010101u,b=(c&255)*0x01010101u;
        if(fullscreen_mode){
            /* Our private screen owns its palette; Workbench pens are untouched. */
            SetRGB32(&live_screen->ViewPort,i,r,g,b);live_pens[i]=i;
        }else{
            live_pens[i]=ObtainBestPenA(live_screen->ViewPort.ColorMap,r,g,b,NULL);
            if(live_pens[i]<0)return 0;
        }
    }
    return 1;
}
static void live_rect(unsigned colour,int x,int y,int w,int h){
    SetAPen(live_window->RPort,live_pens[colour]);
    RectFill(live_window->RPort,x,y,x+w-1,y+h-1);
}
static void live_border(void){
    if(!fullscreen_mode)return;
    /* Native PAL uses the whole raster. Keep the decoration to its outer
     * pixel instead of shrinking or cropping the guest picture into a bezel. */
    live_rect(2,0,0,live_width,1);
    live_rect(2,0,live_height-1,live_width,1);
    live_rect(2,0,0,1,live_height);
    live_rect(2,live_width-1,0,1,live_height);
    for(unsigned i=0;i<5;i++)live_rect(3+i,4+i*10,live_height-1,10,1);

}
static void live_fps_paint(void){
    if(!show_fps)return;
    char text[40];
    snprintf(text,sizeof(text),"ZZ9000  %u.%u FPS",(unsigned)live_fps.tenths/10,(unsigned)live_fps.tenths%10);
    int x=live_window->BorderLeft+8;
    int y=live_window->BorderTop+4;
    live_rect(0,x,y,176,14);
    SetDrMd(live_window->RPort,JAM1);SetAPen(live_window->RPort,live_pens[1]);
    Move(live_window->RPort,x+4,y+10);Text(live_window->RPort,text,strlen(text));
}
