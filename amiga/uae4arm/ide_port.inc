/* Gayle IDE bus glue. ATA commands/data sequencing remain UAE4ARM ide.cpp. */
#include "td-sdl/thread.h"
#include "filesys.h"
#include "ide.h"
#include "storage_wire.h"
static ide_hdf *zu_ide[2];
static unsigned zu_ide_irq;
static ide_hdf *zu_ide_selected(){return zu_ide[zu_ide[0]->ide_drv];}
static int zu_ide_reg(uaecptr a){return ((a&0xffff)&~0x2020u)>>2;}
static bool zu_ide_data(uaecptr a){return (a&0xa0000)==0xa0000 && zu_ide_reg(a)==IDE_DATA;}
static void zu_ide_init(){
 if(zu_ide[0])return;
 alloc_ide_mem(zu_ide,2,NULL);
 for(unsigned i=0;i<2;i++)zu_ide[i]->blocksize=512;
 ide_hdf*d=zu_ide[0];uint64_t size=ad_get(uae_shared,US_HDF_SIZE)|((uint64_t)ad_get(uae_shared,US_HDF_HIGH)<<32);
 d->hdhfd.size=d->hdhfd.hfd.virtsize=d->hdhfd.hfd.physsize=size;
 d->hdhfd.hfd.ci.blocksize=512;d->hdhfd.hfd.ci.readonly=ad_get(uae_shared,US_USB_DISK)||!ad_get(uae_shared,US_WRITABLE);
 d->hdhfd.heads=d->hdhfd.heads_def=16;d->hdhfd.secspertrack=d->hdhfd.secspertrack_def=63;
 d->hdhfd.cyls=d->hdhfd.cyls_def=size/(512*16*63);
 strcpy(d->hdhfd.hfd.product_id,"ZZUAE HDF");
 ide_initialize(zu_ide,0);zu_ide_irq=0;
}
static void zu_ide_rethink(){
 if(!zu_ide[0])return;
 if(ide_irq_check(zu_ide[0],false))zu_ide_irq|=0x80;
 if((zu_ide_irq&profile_irq_enable&0x80) && !(intreq&8))INTREQ_0(0x8008);
}
static void zu_ide_hsync(){
 if(zu_ide[0]){ide_interrupt_hsync(zu_ide[0]);zu_ide_rethink();}
}
