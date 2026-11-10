#include "hdf_check.h"
#include <assert.h>
#include <unistd.h>
static void word(unsigned char*b,unsigned n,unsigned v){b[n*4]=v>>24;b[n*4+1]=v>>16;b[n*4+2]=v>>8;b[n*4+3]=v;}
static void rdb(unsigned char*b){memset(b,0,512);memcpy(b,"RDSK",4);word(b,1,64);word(b,4,512);word(b,7,2);word(b,16,8);word(b,17,32);word(b,18,4);unsigned sum=0;for(unsigned i=0;i<64;i++)sum+=zu_hdf_word(b+i*4);word(b,2,0-sum);}
int main(void){
 char path[]="/tmp/zzuae-hdf-XXXXXX";int fd=mkstemp(path);assert(fd>=0);close(fd);
 unsigned char b[512];struct zu_hdf_info info;FILE*f=fopen(path,"wb");assert(f);rdb(b);assert(fwrite(b,1,512,f)==512);assert(!fseek(f,512*1024-1,SEEK_SET));fputc(0,f);fclose(f);
 assert(zu_hdf_check(path,&info)==ZU_HDF_OK&&info.bytes==512*1024);
 f=fopen(path,"r+b");fputc('X',f);fclose(f);assert(zu_hdf_check(path,&info)==ZU_HDF_NO_RDB);
 f=fopen(path,"r+b");rdb(b);b[8]^=1;fwrite(b,1,512,f);fclose(f);assert(zu_hdf_check(path,&info)==ZU_HDF_BAD_RDB);
 f=fopen(path,"wb");memset(b,0,512);fwrite(b,1,512,f);fwrite(b,1,512,f);rdb(b);fwrite(b,1,512,f);fseek(f,512*1024-1,SEEK_SET);fputc(0,f);fclose(f);assert(zu_hdf_check(path,&info)==ZU_HDF_OK);
 f=fopen(path,"ab");fputc(0,f);fclose(f);assert(zu_hdf_check(path,&info)==ZU_HDF_SIZE);
 /* Sparse >2 GiB file: detect size without reading/copying the image. */
 assert(!truncate(path,0x80000000LL));assert(zu_hdf_check(path,&info)==ZU_HDF_SIZE);
 unlink(path);assert(zu_hdf_check(path,&info)==ZU_HDF_OPEN);
 puts("PASS HDF headers, checksum, relocated RDB, size/alignment and missing files");
}
