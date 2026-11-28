/* Called only from the modal menu at an ungranted frame. All file reads and
 * journal recovery finish before EJECT; old media stays attached on failure. */
static const char *us_disk_name(unsigned unit){return us_files[unit].path;}
static int us_swap_disk(unsigned unit,const char *path){
    struct us_host_file next;memset(&next,0,sizeof next);
    unsigned char *image=NULL;int same=0,ok=0;
    if(unit>1 || strlen(path)>=sizeof next.path)return 0;
    if(*path){
        same=!strcasecmp(path,us_files[unit].path);
        if(!same && !us_prepare_file(&next,unit,path,persistent_mode!=0))goto done;
        image=AllocVec(UAE_DISK_SIZE,MEMF_PUBLIC);
        if(!image)goto done;
        FILE *f=fopen(path,"rb");
        if(!f)goto done;
        ok=fread(image,1,UAE_DISK_SIZE,f)==UAE_DISK_SIZE && fgetc(f)==EOF && !ferror(f);
        if(fclose(f))ok=0;
        if(!ok)goto done;
    }
    ok=0;
    unsigned reply=live_media_request(UM_EJECT,unit);
    if(reply!=UM_OK){
        if(reply==UM_BUSY)puts("STARTUP Drive DMA active; resume and retry disk change");
        goto done;
    }
    if(!same){
        us_close_file(&us_files[unit]);us_files[unit]=next;memset(&next,0,sizeof next);
    }
    if(!*path){printf("MEDIA DF%u ejected\n",unit);ok=1;goto done;}
    unsigned offset=unit?UAE_DISK1_OFFSET:UAE_DISK;
    CopyMem(image,(APTR)(shared+offset),UAE_DISK_SIZE);
    syncio->push(shared+offset,UAE_DISK_SIZE,NULL);syncio->barrier(NULL);
    reply=live_media_request(UM_INSERT,unit);
    if(reply==UM_OK){printf("MEDIA DF%u inserted: %s\n",unit,path);ok=1;}
    else {puts("ERROR Disk insertion failed after eject; stopping emulator");live_abort();}
 done:
    if(image)FreeVec(image);
    us_close_file(&next);
    if(!ok && !live_quit)puts("STARTUP Disk unchanged or unavailable; see preceding message");
    return ok;
}
