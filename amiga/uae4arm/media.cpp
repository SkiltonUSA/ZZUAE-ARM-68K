/* Bounded in-memory, raw-image backend. Host files will be staged by the 68K.
 * No POSIX filesystem access or compressed-media fallback on the ARM worker. */
#include "sysconfig.h"
#include "sysdeps.h"
#include "zfile.h"
#include "crc32.h"
#include "machine.h"
#include "protocol.h"
/* Linker-owned, cache-line-isolated staging storage inside the runtime block.
 * Host loads it after ARM ready, before MB_BENCH. ARM never writes this image. */
unsigned char zzuae_disk1_image[UAE_DISK_SIZE] __attribute__((aligned(64)));
unsigned uae_disk1_present;
struct zfile { unsigned char *data;size_t size,pos;char *name; };
zfile *zfile_fopen_empty(zfile*,const char *name,uae_u64 size) {
 if(size>0x400000)return NULL;
 zfile *f=(zfile*)calloc(1,sizeof(zfile));if(!f)return NULL;
 f->data=(unsigned char*)calloc(1,(size_t)size);f->name=strdup(name);f->size=size;
 if(!f->data||!f->name){zfile_fclose(f);return NULL;}return f;
}
zfile *zfile_fopen_data(const char *name,uae_u64 n,const uae_u8 *data) {
 zfile *f=zfile_fopen_empty(NULL,name,n);if(f)memcpy(f->data,data,n);return f;
}
void zfile_fclose(zfile *f){if(f){free(f->data);free(f->name);free(f);}}
uae_s64 zfile_ftell(zfile *f){return f?f->pos:-1;}
uae_s64 zfile_size(zfile *f){return f?f->size:-1;}
uae_s64 zfile_fseek(zfile *f,uae_s64 off,int mode){
 if(!f)return -1;
 uae_s64 origin=mode==SEEK_SET?0:mode==SEEK_CUR?f->pos:mode==SEEK_END?f->size:-1;
 if(origin<0 || off < -origin || off > (uae_s64)f->size-origin)return -1;
 f->pos=(size_t)(origin+off);return 0;
}
size_t zfile_fread(void *p,size_t size,size_t count,zfile *f){
 if(!f||!size)return 0;size_t n=(f->size-f->pos)/size;if(count<n)n=count;
 memcpy(p,f->data+f->pos,n*size);f->pos+=n*size;return n;
}
size_t zfile_fwrite(const void *p,size_t size,size_t count,zfile *f){
 if(!f||!size)return 0;size_t n=(f->size-f->pos)/size;if(count<n)n=count;
 memcpy(f->data+f->pos,p,n*size);f->pos+=n*size;return n;
}
char *zfile_getname(zfile *f){return f?f->name:NULL;}
char *zfile_getfilename(zfile *f){return zfile_getname(f);}
uae_u32 zfile_crc32(zfile *f){return f?get_crc32(f->data,f->size):0;}
int zfile_iscompressed(zfile*){return 0;}
zfile *zfile_fopen_load_zfile(zfile *f){return f;}
// Optional writes affect this private image object only; no host-file writes.
zfile *zfile_fopen(const char *name,const char *mode,int){
 if(!zfile_exists(name) || strchr(mode,'w') || (!uae_volatile_write && strchr(mode,'+')))return NULL;
 const uae_u8 *data=(const uae_u8*)(uae_shared+UAE_DISK);
 if(!strcmp(name,"df1.adf")){
  data=zzuae_disk1_image;
  /* Host writes bypass this private ARM cache mapping. Invalidate only our
   * untouched, whole-line staging array before reading the published image. */
  for(uintptr_t at=(uintptr_t)data;at<(uintptr_t)data+UAE_DISK_SIZE;at+=32)
   __asm__ volatile("mcr p15,0,%0,c7,c6,1"::"r"(at):"memory");
  __asm__ volatile("dsb sy":::"memory");
  ad_put(uae_shared,UAE_DF1_CRC,get_crc32(zzuae_disk1_image,UAE_DISK_SIZE));
 }
 return zfile_fopen_data(name,UAE_DISK_SIZE,data);
}
zfile *zfile_fopen(const char *n,const char *m){return zfile_fopen(n,m,0);}
int zfile_exists(const char *name){return uae_shared && (!strcmp(name,"wb12.adf") || (uae_disk1_present && !strcmp(name,"df1.adf")));}
zfile *zfile_gunzip(zfile*){return NULL;}
