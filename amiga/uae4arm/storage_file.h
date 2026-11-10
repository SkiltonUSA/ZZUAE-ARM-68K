#pragma once
/* Reuse ZZ8-Bit's verified undo-journal format and recovery ordering.
 * Each write commits only the affected 4 KiB blocks, not the entire image.
 * Caller holds a session lock and forbids simultaneous host mounting. */
#include "support/storage/journal.h"
#include "storage_wire.h"
static int us_file_read(const char*path,unsigned total,unsigned off,void*data,unsigned size){
 if(!us_bounds(total,off,size))return 0;
 FILE*f=fopen(path,"rb");if(!f)return 0;
 int ok=!fseek(f,off,SEEK_SET)&&fread(data,1,size,f)==size;
 if(fclose(f))ok=0;
 return ok;
}
/* Prepare old blocks and bind the undo record to unaffected image blocks. */
static uint8_t *us_prepare(const char*path,unsigned total,unsigned off,unsigned size){
 unsigned first=off/ZN_BLOCK_BYTES,last=(off+size-1)/ZN_BLOCK_BYTES,count=last-first+1;
 unsigned bytes=ZN_JOURNAL_HEADER+count*ZN_JOURNAL_RECORD;
 uint8_t*j=calloc(1,bytes+4);if(!j)return NULL;
 memcpy(j,"ZNUNDO2",8);zn_journal_put(j+8,total);zn_journal_put(j+12,count);
 FILE*f=fopen(path,"rb");int ok=f&&!fseek(f,0,SEEK_END)&&ftell(f)==(long)total;
 for(unsigned i=0;ok&&i<count;i++){
  uint8_t*r=zn_journal_record(j,i);unsigned b=first+i,n=zn_journal_block_size(total,b);
  zn_journal_put(r,b);ok=!fseek(f,b*ZN_BLOCK_BYTES,SEEK_SET)&&fread(r+4,1,n,f)==n;
 }
 unsigned anchors[2]={first?0:last+1,last+1<(total+4095)/4096?(total+4095)/4096-1:first?first-1:0xffffffffu};
 for(unsigned i=0;ok&&i<2;i++){
  uint32_t hash=0,b=anchors[i];if(b>=(total+4095)/4096)b=0xffffffffu;
  if(b!=0xffffffffu)ok=zn_journal_fingerprint(f,total,b,&hash);
  zn_journal_put(j+16+i*8,b);zn_journal_put(j+20+i*8,hash);
 }
 if(f&&fclose(f))ok=0;
 if(!ok){free(j);return NULL;}
 zn_journal_put(j+bytes,zn_journal_hash(j,bytes));return j;
}
static int us_publish(const char*path,const struct zn_journal_paths*p,uint8_t*j){
 unsigned bytes=ZN_JOURNAL_HEADER+zn_journal_word(j+12)*ZN_JOURNAL_RECORD+4;
 FILE*f=fopen(p->temporary,"wb");if(!f)return 0;
 int ok=fwrite(j,1,bytes,f)==bytes;if(fclose(f))ok=0;
 if(ok)ok=zn_journal_sync(p->temporary);
 uint8_t*check=ok?zn_journal_read(p->temporary,path):NULL;
 ok=check&&!memcmp(check,j,bytes);free(check);
 return ok&&!rename(p->temporary,p->pending)&&zn_journal_sync(p->pending);
}
static int us_file_write(const char*path,unsigned total,unsigned off,const void*data,unsigned size){
 struct zn_journal_paths paths;
 if(!us_bounds(total,off,size)||!zn_journal_paths(path,&paths)||
    !zn_journal_absent(paths.pending)||!zn_journal_absent(paths.temporary))return 0;
 uint8_t*j=us_prepare(path,total,off,size);if(!j)return 0;
 /* Skip unchanged writes without a journal or flush. */
 unsigned count=zn_journal_word(j+12),changed=0;
 for(unsigned i=0;i<count;i++){
  uint8_t*r=zn_journal_record(j,i);unsigned base=zn_journal_word(r)*4096;
  unsigned begin=off>base?off:base,end=off+size<base+4096?off+size:base+4096;
  if(memcmp(r+4+begin-base,(const uint8_t*)data+begin-off,end-begin))changed=1;
 }
 if(!changed){free(j);return 1;}
 int ok=us_publish(path,&paths,j);
 if(ok){
  FILE*f=fopen(path,"r+b");ok=f&&!fseek(f,off,SEEK_SET)&&fwrite(data,1,size,f)==size;
  if(f&&fclose(f))ok=0;
  if(ok)ok=zn_journal_sync(path);
  /* The durable journal remains OLD; in-memory expected blocks become NEW. */
  for(unsigned i=0;i<count;i++){
   uint8_t*r=zn_journal_record(j,i);unsigned base=zn_journal_word(r)*4096;
   unsigned begin=off>base?off:base,end=off+size<base+4096?off+size:base+4096;
   memcpy(r+4+begin-base,(const uint8_t*)data+begin-off,end-begin);
  }
  if(ok)ok=zn_journal_verify(path,j)&&zn_journal_retire(path,&paths);
 }
 free(j);
 if(!ok)zn_journal_recover(path);
 return ok;
}
