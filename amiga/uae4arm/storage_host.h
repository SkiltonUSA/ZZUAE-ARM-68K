#pragma once
#include "storage_file.h"
#include "usb_disk.h"
#include "storage_reply.h"
static struct zu_usb_disk us_usb;
struct us_host_file {const char*path;unsigned size;BPTR lock;char lockpath[1024];};
static struct us_host_file us_files[3];
static unsigned us_last,us_reads,us_writes,us_errors;
static int us_open_file(unsigned unit,const char*path,int writable){
 struct us_host_file*f=&us_files[unit];f->path=path;if(!*path)return 1;
 if(unit==2&&!strncmp(path,"USBSD:",6)){
  if(writable){puts("ERROR Physical USB SD is read only; select Read only.");return 0;}
  if(!zu_usb_open(&us_usb,path))return 0;
  f->size=(unsigned)us_usb.bytes;return 1;
 }
 /* Open an exclusive session marker. A stale marker is reusable after crash. */
 struct zn_journal_paths j;if(!zn_journal_paths(path,&j))return 0;
 snprintf(f->lockpath,sizeof f->lockpath,"%s",j.temporary);
 size_t n=strlen(f->lockpath);memcpy(f->lockpath+n-3,"zul",3);
 f->lock=Open((STRPTR)f->lockpath,MODE_NEWFILE);if(!f->lock)return 0;
 if(writable){if(!zn_journal_recover(path))return 0;}
 else if(!zn_journal_absent(j.pending)||!zn_journal_absent(j.temporary)){
  puts("ERROR Image needs journal recovery; open read/write first.");return 0;
 }
 FILE*image=fopen(path,"rb");if(!image)return 0;
 int ok=!fseek(image,0,SEEK_END);long size=ok?ftell(image):-1;
 if(fclose(image))ok=0;
 if(!ok || size<512 || size>0x7ffffe00L || (size&511))return 0;
 if(unit<2 && size!=UAE_DISK_SIZE)return 0;
 f->size=(unsigned)size;return 1;
}
static int us_host_open(){
 int writable=persistent_mode!=0;
 if(!us_open_file(0,disk_path,writable)||!us_open_file(1,disk1_path,writable)||!us_open_file(2,hdf_path,writable)){
  puts("ERROR Storage unavailable, busy, invalid or needs recovery.");return 0;
 }
 ad_put(shared,US_HDF_SIZE,us_files[2].size);ad_put(shared,US_WRITABLE,writable);
 ad_put(shared,US_USB_DISK,us_usb.opened);ad_put(shared,US_HDF_HIGH,(unsigned)(us_usb.bytes>>32));
 syncio->push(shared+US_HDF_SIZE,16,NULL);syncio->barrier(NULL);
 if(us_usb.opened)printf("STORAGE USB SD sectors=%lu read only\n",(unsigned long)(us_usb.bytes>>9));
 else if(*hdf_path)printf("STORAGE IDE %s bytes=%u %s\n",hdf_path,us_files[2].size,writable?"journalled read/write":"read only");
 return 1;
}
static int us_host_service(){
 syncio->pull(shared+US_REQUEST,24,NULL);unsigned seq=ad_get(shared,US_REQUEST);
 if(seq==us_last)return 1;
 unsigned op=ad_get(shared,US_OPERATION),unit=ad_get(shared,US_UNIT),off=ad_get(shared,US_OFFSET),n=ad_get(shared,US_LENGTH);
 unsigned high=ad_get(shared,US_OFFSET_HIGH);
 int raw=unit==2&&us_usb.opened;
 uint64_t offset=((uint64_t)high<<32)|off;
 int ok=raw ? us_bounds64(us_usb.bytes,offset,n) : (!high&&unit<3&&us_files[unit].size&&us_bounds(us_files[unit].size,off,n));
 static unsigned char data[US_CAPACITY];
 if(ok&&op==US_READ){
  ok=raw?zu_usb_read(&us_usb,offset,data,n):us_file_read(us_files[unit].path,us_files[unit].size,off,data,n);
  if(ok){CopyMem(data,(APTR)(shared+US_DATA),n);syncio->push(shared+US_DATA,n,NULL);us_reads++;}
 }else if(ok&&op==US_WRITE&&persistent_mode&&!raw){
  syncio->pull(shared+US_DATA,n,NULL);CopyMem((APTR)(shared+US_DATA),data,n);
  ok=us_file_write(us_files[unit].path,us_files[unit].size,off,data,n);if(ok)us_writes++;
 }else ok=0;
 if(!ok){us_errors++;puts("ERROR Guest disk IO failed; journal retained if recovery is needed.");}
 us_publish_reply(shared,syncio,seq,ok?n:0);us_last=seq;
 return ok;
}
static void us_host_close(){
 zu_usb_close(&us_usb);
 for(unsigned i=0;i<3;i++)if(us_files[i].lock){Close(us_files[i].lock);us_files[i].lock=0;DeleteFile((STRPTR)us_files[i].lockpath);}
 printf("STORAGE reads=%u writes=%u errors=%u\n",us_reads,us_writes,us_errors);
}
