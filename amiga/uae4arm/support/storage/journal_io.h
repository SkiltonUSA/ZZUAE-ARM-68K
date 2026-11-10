#pragma once
/* Durability barriers for the containing filesystem, after stdio closes.
 * A device/handler must honour flushes; this cannot fix failing storage. */
#include <stdint.h>
#include <stdio.h>
#if defined(__amigaos__) || defined(__AMIGA__) || defined(__mc68000__)
#include <dos/dosextens.h>
#include <proto/dos.h>
static inline uint32_t zn_journal_milliseconds(void){struct DateStamp d;DateStamp(&d);return ((uint32_t)d.ds_Days*4320000u+(uint32_t)d.ds_Minute*3000u+(uint32_t)d.ds_Tick)*20u;}
static int zn_journal_sync(const char *path){
 struct DevProc *d=GetDeviceProc((CONST_STRPTR)path,NULL);if(!d)return 0;
 LONG ok=DoPkt(d->dvp_Port,ACTION_FLUSH,0,0,0,0,0);FreeDeviceProc(d);return ok!=0;
}
#else
#include <sys/stat.h>
#include <sys/time.h>
static inline uint32_t zn_journal_milliseconds(void){struct timeval t;gettimeofday(&t,NULL);return (uint32_t)t.tv_sec*1000u+(uint32_t)t.tv_usec/1000u;}
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
static int zn_journal_sync(const char *path){
 int fd=open(path,O_RDONLY);if(fd<0)return 0;int ok=!fsync(fd);if(close(fd))ok=0;
 char parent[1024];size_t n=strlen(path);if(n>=sizeof parent)return 0;memcpy(parent,path,n+1);
 char *slash=strrchr(parent,'/');if(slash){if(slash==parent)slash[1]=0;else *slash=0;}else strcpy(parent,".");
 fd=open(parent,O_RDONLY);if(fd<0)return 0;if(fsync(fd))ok=0;if(close(fd))ok=0;return ok;
}
#endif
