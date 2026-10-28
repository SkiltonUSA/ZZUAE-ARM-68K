/* Draw only in the host-owned window, after the ARM bitmap is unlocked. */
#include "presentation.h"
#include "disk_light.h"
static struct ul_fps live_fps;
static LONG live_pens[8]={-1,-1,-1,-1,-1,-1,-1,-1};
static const ULONG live_colours[8]={0x101820,0xe8e4d9,0x46505a,0xd52932,0xf39724,0xf5d539,0x3baf63,0x408bd0};
static int live_palette(void){
    if(!frame_limit && fullscreen_mode)return 1;
    for(unsigned i=0;i<8u;i++){
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
    if(!frame_limit || !fullscreen_mode)return;
    /* Native PAL uses the whole raster. Keep the decoration to its outer
     * pixel instead of shrinking or cropping the guest picture into a bezel. */
    live_rect(2,0,0,live_width,1);
    live_rect(2,0,live_height-1,live_width,1);
    live_rect(2,0,0,1,live_height);
    live_rect(2,live_width-1,0,1,live_height);
    for(unsigned i=0;i<5;i++)live_rect(3+i,4+i*10,live_height-1,10,1);

}
static void live_fps_paint(void){
    if(!frame_limit || !show_fps)return;
    char text[40];
    snprintf(text,sizeof(text),"ZZ9000  %u.%u FPS",(unsigned)live_fps.tenths/10,(unsigned)live_fps.tenths%10);
    int x=live_window->BorderLeft+8;
    int y=live_window->BorderTop+4;
    live_rect(0,x,y,176,14);
    SetDrMd(live_window->RPort,JAM1);SetAPen(live_window->RPort,live_pens[1]);
    Move(live_window->RPort,x+4,y+10);Text(live_window->RPort,text,strlen(text));
}

/* A separate strip keeps power and drive lamps outside the picture. */
static int live_status=-1;
static unsigned live_disk_on[2],live_disk_off[2];
static struct zu_disk_light live_disk_light[2];
static ULONG live_status_polled;
static void live_status_paint(int force){
    if(fullscreen_mode)return;
    ULONG now=us();
    if(!force && (ULONG)(now-live_status_polled)<20000u)return;
    live_status_polled=now;
    syncio->pull(shared+UAE_LIVE+UL_DISK_READS,8,NULL);
    int state=live_ready && !live_quit?1:0;
    for(unsigned drive=0;drive<2;drive++){
        int on=zu_disk_light_update(&live_disk_light[drive],ad_get(shared+UAE_LIVE,UL_DISK_READS+4*drive),now,!live_quit);
        unsigned bit=2u<<drive;
        if(on)state|=bit;
        if(live_status>=0 && ((state^live_status)&bit)){
            if(on)live_disk_on[drive]++;else live_disk_off[drive]++;
        }
    }
    if(!force && state==live_status)return;
    live_status=state;
    int x=live_window->BorderLeft,y=live_window->BorderTop+live_height;
    live_rect(2,x,y,live_width,UL_STATUS_HEIGHT);
    x+=live_width-36;
    live_rect(0,x,y+2,8,8);live_rect(state&1?6:2,x+1,y+3,6,6);
    for(unsigned drive=0;drive<2;drive++){
        int lamp=x+12+drive*12;
        live_rect(0,lamp,y+2,8,8);
        live_rect(state&(2u<<drive)?3:2,lamp+1,y+3,6,6);
    }
}
