#pragma once
#include <stdint.h>
#include <string.h>

static uint32_t zu_rdb_word(const unsigned char *p){
 return (uint32_t)p[0]<<24|(uint32_t)p[1]<<16|(uint32_t)p[2]<<8|p[3];
}
/* RDB headers may occupy any of the first 16 sectors, not only sector zero.
 * Stop at the first RDSK header: a damaged header must not be accepted. */
static int zu_usb_find_rdb(void *disk,uint64_t bytes,
 int (*read_sector)(void *,uint64_t,void *,unsigned)){
 unsigned char block[512];
 for(unsigned sector=0;sector<16 && sector<bytes/512;sector++){
  if(!read_sector(disk,(uint64_t)sector*512,block,sizeof block))return 0;
  if(memcmp(block,"RDSK",4))continue;
  unsigned words=zu_rdb_word(block+4);uint32_t sum=0;
  if(words<64||words>128||zu_rdb_word(block+16)!=512)return 0;
  for(unsigned i=0;i<words;i++)sum+=zu_rdb_word(block+4*i);
  return sum==0;
 }
 return 0;
}
