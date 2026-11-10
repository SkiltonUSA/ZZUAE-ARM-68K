#pragma once
/* Undo transaction for an exclusively unmounted shared image. No Core1 writer.
 * .njt is incomplete preparation; .nju is a verified, durable undo journal.
 * Presence of .nju always means restore the old blocks before mounting.
 * Never rename/move a journal separately from its image. */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include "block_store.h"
#include "journal_io.h"
#define ZN_JOURNAL_HEADER 32u
#define ZN_JOURNAL_RECORD (4u+ZN_BLOCK_BYTES)
struct zn_journal_paths {char pending[1024],temporary[1024];};
static int zn_journal_paths(const char *image,struct zn_journal_paths *p){
 const char *leaf=image;for(const char*q=image;*q;q++)if(*q=='/'||*q==':')leaf=q+1;
 char base[1024];int n;
 if(strlen(leaf)<=26)n=snprintf(base,sizeof base,"%s",image);
 else{
  /* Stay below classic 30-character limits, including for setup .tmp files. */
  uint64_t hash=14695981039346656037ULL;for(const unsigned char*q=(const unsigned char*)leaf;*q;q++){hash^=*q;hash*=1099511628211ULL;}
  n=snprintf(base,sizeof base,"%.*s~ZN%08lx%08lx",(int)(leaf-image),image,(unsigned long)(hash>>32),(unsigned long)(uint32_t)hash);
 }
 if(n<1||(unsigned)n>=sizeof base)return 0;
 int a=snprintf(p->pending,sizeof p->pending,"%s.nju",base),b=snprintf(p->temporary,sizeof p->temporary,"%s.njt",base);
 return *image&&a>0&&b>0&&(unsigned)a<sizeof p->pending&&(unsigned)b<sizeof p->temporary;
}
static uint32_t zn_journal_word(const uint8_t *p){return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static inline void zn_journal_put(uint8_t*p,uint32_t v){for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(v>>(8*i));}
static uint32_t zn_journal_hash(const uint8_t*p,unsigned n){uint32_t h=2166136261u;while(n--){h^=*p++;h*=16777619u;}return h;}
static int zn_journal_absent(const char*p){FILE*f=fopen(p,"rb");if(f){fclose(f);return 0;}return errno==ENOENT;}
static unsigned zn_journal_block_size(unsigned total,unsigned block){unsigned n=total-block*ZN_BLOCK_BYTES;return n>ZN_BLOCK_BYTES?ZN_BLOCK_BYTES:n;}
static uint8_t *zn_journal_record(uint8_t*j,unsigned i){return j+ZN_JOURNAL_HEADER+i*ZN_JOURNAL_RECORD;}
/* Bind the journal to untouched image data. Amiga fib_DiskKey is an
 * enumeration key on some handlers, not a portable persistent inode. */
static int zn_journal_fingerprint(FILE*f,unsigned total,unsigned block,uint32_t *hash){
 uint8_t buffer[ZN_BLOCK_BYTES];unsigned n=zn_journal_block_size(total,block);
 if(fseek(f,block*ZN_BLOCK_BYTES,SEEK_SET)||fread(buffer,1,n,f)!=n)return 0;
 *hash=zn_journal_hash(buffer,n);return 1;
}
static int zn_journal_image(const char *image,const uint8_t*j){
 unsigned total=zn_journal_word(j+8),count=zn_journal_word(j+12);
 FILE*f=fopen(image,"rb");if(!f)return 0;int ok=!fseek(f,0,SEEK_END)&&ftell(f)==(long)total;
 for(unsigned i=0;ok&&i<2;i++){
  unsigned block=zn_journal_word(j+16+i*8);uint32_t hash=0;
  if(block==0xffffffffu){if(zn_journal_word(j+20+i*8))ok=0;continue;}
  if(block>=(total+ZN_BLOCK_BYTES-1)/ZN_BLOCK_BYTES){ok=0;break;}
  for(unsigned k=0;k<count;k++)if(zn_journal_word(j+ZN_JOURNAL_HEADER+k*ZN_JOURNAL_RECORD)==block)ok=0;
  if(ok)ok=zn_journal_fingerprint(f,total,block,&hash)&&hash==zn_journal_word(j+20+i*8);
 }
 if(fclose(f))ok=0;
 return ok;
}
/* Parse and checksum the entire journal before allowing a single image write. */
static uint8_t *zn_journal_read(const char *path,const char *image){
 uint8_t h[ZN_JOURNAL_HEADER],*j=NULL;FILE*f=fopen(path,"rb");if(!f)return NULL;
 if(fread(h,1,sizeof h,f)!=sizeof h||memcmp(h,"ZNUNDO2",8))goto done;
 unsigned total=zn_journal_word(h+8),count=zn_journal_word(h+12);
 if(total<512||total>=0x80000000u||(total&511)||!count||count>ZN_OVERLAY_BLOCKS)goto done;
 unsigned bytes=ZN_JOURNAL_HEADER+count*ZN_JOURNAL_RECORD;
 j=malloc(bytes+4);if(!j)goto done;memcpy(j,h,sizeof h);
 if(fread(j+sizeof h,1,bytes+4-sizeof h,f)!=bytes+4-sizeof h||fgetc(f)!=EOF||ferror(f)||
    zn_journal_hash(j,bytes)!=zn_journal_word(j+bytes))goto invalid;
 for(unsigned i=0;i<count;i++){
  unsigned b=zn_journal_word(zn_journal_record(j,i));
  if(b>=(total+ZN_BLOCK_BYTES-1)/ZN_BLOCK_BYTES||(i&&b<=zn_journal_word(zn_journal_record(j,i-1))))goto invalid;
 }
 if(!zn_journal_image(image,j))goto invalid;
 goto done;
 invalid:free(j);j=NULL;
 done:if(fclose(f)){free(j);j=NULL;}return j;
}
static int zn_journal_verify(const char *image,uint8_t*j){
 unsigned total=zn_journal_word(j+8),count=zn_journal_word(j+12);uint8_t buffer[ZN_BLOCK_BYTES];
 FILE*f=fopen(image,"rb");if(!f)return 0;int ok=1;
 for(unsigned i=0;ok&&i<count;i++){
  uint8_t*r=zn_journal_record(j,i);unsigned block=zn_journal_word(r),n=zn_journal_block_size(total,block);
  ok=!fseek(f,block*ZN_BLOCK_BYTES,SEEK_SET)&&fread(buffer,1,n,f)==n&&!memcmp(buffer,r+4,n);
 }
 if(fclose(f))ok=0;
 return ok;
}
static int zn_journal_retire(const char *image,const struct zn_journal_paths *paths){
 /* The image is already durable before removal. Flush the directory as well. */
 return !remove(paths->pending)&&zn_journal_sync(image);
}
static int zn_journal_recover(const char *image){
 struct zn_journal_paths paths;if(!zn_journal_paths(image,&paths))return 0;
 if(!zn_journal_absent(paths.pending)){
  uint8_t*j=zn_journal_read(paths.pending,image);if(!j){puts("ERROR Invalid shared-drive recovery journal; image left unmounted.");return 0;}
  unsigned total=zn_journal_word(j+8),count=zn_journal_word(j+12);FILE*f=fopen(image,"r+b");int ok=f!=NULL;
  for(unsigned i=0;ok&&i<count;i++){
   uint8_t*r=zn_journal_record(j,i);unsigned block=zn_journal_word(r),n=zn_journal_block_size(total,block);
   ok=!fseek(f,block*ZN_BLOCK_BYTES,SEEK_SET)&&fwrite(r+4,1,n,f)==n;
  }
  if(f&&fclose(f))ok=0;
  if(ok)ok=zn_journal_sync(image)&&zn_journal_verify(image,j);
  free(j);if(!ok||!zn_journal_retire(image,&paths)){puts("ERROR Recovery incomplete; journal retained where available. Do not mount the image.");return 0;}
  printf("NEXT_FAT Recovered %u shared-drive blocks.\n",count);
 }
 /* Preparation never changes the image until .nju is durable. */
 return zn_journal_absent(paths.temporary)||(!remove(paths.temporary)&&zn_journal_sync(image));
}
