/* Called only with a completed frame held until host ACK. */
#pragma once
#include "live_pixels.h"
#include "scanlines.h"
static void capture_le32(UBYTE *p,ULONG n){p[0]=n;p[1]=n>>8;p[2]=n>>16;p[3]=n>>24;}
static int live_capture(unsigned mode){
    char folder[512],name[512];struct DateStamp stamp;BPTR lock,file=0;
    UBYTE header[54]={0},row[640*3];unsigned x,y;int ok=0;
    if(!NameFromLock(GetProgramDir(),folder,sizeof(folder)) ||
       !AddPart(folder,"Screenshots",sizeof(folder)))goto done;
    lock=Lock(folder,ACCESS_READ);
    if(!lock)lock=CreateDir(folder);
    if(!lock)goto done;
    UnLock(lock);DateStamp(&stamp);
    snprintf(name,sizeof(name),"%s/ZZUAE-%ld-%ld-%ld.bmp",folder,
        (long)stamp.ds_Days,(long)stamp.ds_Minute,(long)stamp.ds_Tick);
    lock=Lock(name,ACCESS_READ);if(lock){UnLock(lock);goto done;}
    file=Open(name,MODE_NEWFILE);if(!file)goto done;
    header[0]='B';header[1]='M';capture_le32(header+2,54+640*256*3);
    capture_le32(header+10,54);capture_le32(header+14,40);
    capture_le32(header+18,640);capture_le32(header+22,256);
    header[26]=1;header[28]=24;capture_le32(header+34,640*256*3);
    if(Write(file,header,sizeof(header))!=sizeof(header))goto done;
    syncio->pull(shared+UAE_FRAME,640*256*2,NULL);
    for(y=256;y-- >0;){
        const volatile UBYTE *src=shared+UAE_FRAME+y*1280;
        unsigned level=ul_scan_level(mode,y);
        for(x=0;x<640;x++){
            uint16_t rgb=src[x*2]|((uint16_t)src[x*2+1]<<8);
            uint32_t p=ul_scan_dim(ul_pixel(rgb,3),level);
            row[x*3]=p;row[x*3+1]=p>>8;row[x*3+2]=p>>16;
        }
        if(Write(file,row,sizeof(row))!=sizeof(row))goto done;
    }
    ok=1;
done:
    if(file){if(!Close(file))ok=0;if(!ok)DeleteFile(name);}
    if(ok)printf("STARTUP Screenshot saved: %s\n",name);
    else puts("STARTUP Screenshot could not be saved.");
    return ok;
}
