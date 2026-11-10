#!/usr/bin/env python3
"""Exercise actual USB command completion/timeout cleanup with Exec mocks."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[3]
s=(root/'amiga/uae4arm/usb_disk.h').read_text();s=s[s.index('static int zu_usb_command'):s.index('static int zu_usb_read(')]
prefix=r'''
#include <stdint.h>
#include <string.h>
#include <assert.h>
#include <stdio.h>
#define HD_SCSICMD 1
#define SCSIF_READ 1
#define SCSIF_AUTOSENSE 2
#define TR_ADDREQUEST 2
struct IORequest {int io_Command,io_Length,io_Flags,io_Error;void *io_Data;};
struct SCSICmd {void *scsi_Data,*scsi_Command,*scsi_SenseData;unsigned scsi_Length,scsi_CmdLength,scsi_Flags,scsi_SenseLength,scsi_Status,scsi_Actual;};
struct MsgPort {unsigned mp_SigBit;};
struct timerequest {struct IORequest tr_node;struct {unsigned tv_secs,tv_micro;} tr_time;};
struct zu_usb_disk {struct IORequest *io;struct timerequest *timer;struct MsgPort *port,*timer_port;};
static struct IORequest io;static struct timerequest timer;
static int mode,io_done,timer_done,waits,reaped_io,reaped_timer,abort_io,abort_timer;
static void SendIO(struct IORequest *r){
 if(r==&io){struct SCSICmd*s=r->io_Data;s->scsi_Actual=s->scsi_Length;
  if(mode==0)io_done=1;if(mode==4)s->scsi_Status=2;if(mode==5)s->scsi_Actual--;
 }else {assert(r==&timer.tr_node);assert(timer.tr_time.tv_secs==5);}
}
static int CheckIO(struct IORequest*r){return r==&io?io_done:timer_done;}
static void Wait(unsigned long mask){
 assert(mask==((1ul<<2)|(1ul<<3)));assert(++waits<4);
 if(mode==2)timer_done=1;
 else if(mode==3){io_done=timer_done=1;}
 else io_done=1;
}
static void AbortIO(struct IORequest*r){if(r==&io){abort_io++;io_done=1;io.io_Error=1;}else{abort_timer++;timer_done=1;}}
static void WaitIO(struct IORequest*r){assert(CheckIO(r));if(r==&io)reaped_io++;else reaped_timer++;}
'''
suffix=r'''
int main(void){struct MsgPort p={2},t={3};struct zu_usb_disk d={&io,&timer,&p,&t};unsigned char cmd[10]={0},data[512];
 for(mode=0;mode<6;mode++){
  io_done=timer_done=waits=reaped_io=reaped_timer=abort_io=abort_timer=0;io.io_Error=0;
  int ok=zu_usb_command(&d,cmd,data,sizeof data);
  assert(ok==(mode==0||mode==1||mode==3));assert(reaped_io==1&&reaped_timer==1);
  assert(abort_io==(mode==2));assert(abort_timer==(mode!=2&&mode!=3));
  assert(waits==(mode!=0));
 }
 puts("PASS USB completion: immediate, delayed, timeout, simultaneous, device error, short read; both requests drained");
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'wait.c';p.write_text(prefix+s+suffix)
 subprocess.run(['cc','-std=c99','-fsanitize=address,undefined',str(p),'-o',d+'/test'],check=True)
 subprocess.run([d+'/test'],check=True)
