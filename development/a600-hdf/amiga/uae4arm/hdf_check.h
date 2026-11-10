#pragma once
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
/* Inspect only the RDB search area. Guest filesystem validation belongs to the
 * guest driver; this check rejects unsupported containers before Core1 starts. */
enum { ZU_HDF_OK, ZU_HDF_OPEN, ZU_HDF_SIZE, ZU_HDF_NO_RDB, ZU_HDF_BAD_RDB };
struct zu_hdf_info {unsigned bytes;};
static uint32_t zu_hdf_word(const unsigned char *p){return (uint32_t)p[0]<<24|(uint32_t)p[1]<<16|(uint32_t)p[2]<<8|p[3];}
static int zu_hdf_check(const char *path,struct zu_hdf_info *info){
 unsigned char b[512];info->bytes=0;
 FILE *f=fopen(path,"rb");if(!f)return ZU_HDF_OPEN;
 int result=ZU_HDF_SIZE;
 if(fseek(f,0,SEEK_END))goto done;
 long bytes=ftell(f);
 if(bytes<512 || bytes>0x7ffffe00L || (bytes&511))goto done;
 info->bytes=(unsigned)bytes;
 if(fseek(f,0,SEEK_SET)){result=ZU_HDF_OPEN;goto done;}
 result=ZU_HDF_NO_RDB;
 for(unsigned sector=0;sector<16 && sector<info->bytes/512;sector++){
  if(fread(b,1,sizeof b,f)!=sizeof b){result=ZU_HDF_OPEN;break;}
  if(memcmp(b,"RDSK",4))continue;
  result=ZU_HDF_BAD_RDB;
  unsigned words=zu_hdf_word(b+4);uint32_t sum=0;
  if(words<64 || words>128 || zu_hdf_word(b+16)!=512)break;
  for(unsigned i=0;i<words;i++)sum+=zu_hdf_word(b+i*4);
  if(!sum)result=ZU_HDF_OK;
  break;
 }
 done:if(fclose(f))result=ZU_HDF_OPEN;return result;
}
static const char *zu_hdf_message(int result){
 switch(result){
 case ZU_HDF_OK:return "HDF ready. Eject DF0/DF1 to boot from the hard disk.";
 case ZU_HDF_OPEN:return "HDF unavailable: check the SD/USB volume and file path.";
 case ZU_HDF_SIZE:return "HDF must be sector-aligned and smaller than 2 GiB.";
 case ZU_HDF_NO_RDB:return "An RDB hard-disk image is required; unpack ZIP/XZ first. Partition-only HDF is not supported.";
 default:return "HDF has an invalid RDB checksum or unsupported sector size.";
 }
}
