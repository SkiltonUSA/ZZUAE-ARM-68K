#pragma once
/* Experimental read-only USB disk. No write command is implemented. */
#include <devices/scsidisk.h>
#include <devices/timer.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include "usb_rdb.h"
struct zu_usb_disk {struct MsgPort *port,*timer_port;struct IOStdReq *io;struct timerequest *timer;uint64_t bytes;int opened,timer_opened;};
static uint32_t zu_usb_word(const unsigned char*p){return (uint32_t)p[0]<<24|(uint32_t)p[1]<<16|(uint32_t)p[2]<<8|p[3];}
static void zu_usb_close(struct zu_usb_disk*d){
 if(d->timer_opened)CloseDevice((struct IORequest*)d->timer);
 if(d->timer)DeleteIORequest((struct IORequest*)d->timer);
 if(d->timer_port)DeleteMsgPort(d->timer_port);
 if(d->opened)CloseDevice((struct IORequest*)d->io);
 if(d->io)DeleteIORequest((struct IORequest*)d->io);
 if(d->port)DeleteMsgPort(d->port);
 memset(d,0,sizeof(*d));
}
static int zu_usb_command(struct zu_usb_disk*d,unsigned char*cmd,void*data,unsigned bytes){
 struct SCSICmd s;unsigned char sense[32];memset(&s,0,sizeof s);memset(sense,0,sizeof sense);
 s.scsi_Data=data;s.scsi_Length=bytes;s.scsi_Command=cmd;s.scsi_CmdLength=10;
 s.scsi_Flags=SCSIF_READ|SCSIF_AUTOSENSE;s.scsi_SenseData=sense;s.scsi_SenseLength=sizeof sense;
 d->io->io_Command=HD_SCSICMD;d->io->io_Data=&s;d->io->io_Length=sizeof s;d->io->io_Flags=0;
 SendIO((struct IORequest*)d->io);
 /* Wake on actual completion, with a separate five-second deadline. Delay(1)
  * rounded every read up to a scheduler tick while ARM audio was stalled. */
 d->timer->tr_node.io_Command=TR_ADDREQUEST;
 d->timer->tr_time.tv_secs=5;d->timer->tr_time.tv_micro=0;
 SendIO((struct IORequest*)d->timer);
 while(!CheckIO((struct IORequest*)d->io)&&!CheckIO((struct IORequest*)d->timer))
  Wait((1UL<<d->port->mp_SigBit)|(1UL<<d->timer_port->mp_SigBit));
 if(!CheckIO((struct IORequest*)d->io))AbortIO((struct IORequest*)d->io);
 WaitIO((struct IORequest*)d->io);
 if(!CheckIO((struct IORequest*)d->timer))AbortIO((struct IORequest*)d->timer);
 WaitIO((struct IORequest*)d->timer);
 return !d->io->io_Error&&!s.scsi_Status&&s.scsi_Actual==bytes;
}
static int zu_usb_read(struct zu_usb_disk*d,uint64_t offset,void*data,unsigned bytes){
 if(!bytes||(offset&511)||(bytes&511)||bytes>16384||offset>d->bytes||bytes>d->bytes-offset)return 0;
 uint64_t lba=offset>>9;if(lba>0xffffffffu)return 0;
 unsigned char cmd[10]={0x28,0,(unsigned char)(lba>>24),(unsigned char)(lba>>16),(unsigned char)(lba>>8),(unsigned char)lba,0,0,0,0};
 cmd[7]=(bytes>>9)>>8;cmd[8]=bytes>>9;return zu_usb_command(d,cmd,data,bytes);
}
static int zu_usb_read_sector(void *disk,uint64_t offset,void *data,unsigned bytes){
 return zu_usb_read((struct zu_usb_disk*)disk,offset,data,bytes);
}
static int zu_usb_open(struct zu_usb_disk*d,const char*path){
 char*end;unsigned long unit;if(strncmp(path,"USBSD:",6))return 0;
 unit=strtoul(path+6,&end,10);if(end==path+6||*end||unit>255)return 0;
 memset(d,0,sizeof(*d));d->port=CreateMsgPort();if(!d->port)goto fail;
 d->io=(struct IOStdReq*)CreateIORequest(d->port,sizeof(*d->io));if(!d->io)goto fail;
 if(OpenDevice("usbscsi.device",unit,(struct IORequest*)d->io,0))goto fail;
 d->opened=1;
 d->timer_port=CreateMsgPort();if(!d->timer_port)goto fail;
 d->timer=(struct timerequest*)CreateIORequest(d->timer_port,sizeof(*d->timer));if(!d->timer)goto fail;
 if(OpenDevice(TIMERNAME,UNIT_MICROHZ,(struct IORequest*)d->timer,0))goto fail;
 d->timer_opened=1;
 unsigned char cmd[10]={0x25},data[512];
 if(!zu_usb_command(d,cmd,data,8)||zu_usb_word(data+4)!=512||zu_usb_word(data)==0xffffffffu)goto fail;
 d->bytes=((uint64_t)zu_usb_word(data)+1)*512;
 if(!zu_usb_find_rdb(d,d->bytes,zu_usb_read_sector))goto fail;
 return 1;
 fail:zu_usb_close(d);return 0;
}
