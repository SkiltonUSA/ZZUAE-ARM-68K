/* Appended to the pinned upstream disk.cpp: retain its drive/change machinery. */
#include "disk_swap.h"
#include "machine.h"
extern "C" unsigned zzuae_disk_command(unsigned operation,unsigned unit){
    if(!zu_disk_command_valid(operation,unit))return UM_INVALID;
    /* Do not discard partial MFM writes or redirect an in-flight read. The
     * session menu remains paused; Resume lets the guest finish before retry. */
    if(floppy[unit].writtento ||
       (dskdmaen!=DSKDMA_OFF && !((selected|disabled)&(1u<<unit))))return UM_BUSY;
    if(operation==UM_EJECT){
        disk_eject(unit);
        if(unit==1)uae_disk1_present=0;
        return UM_OK;
    }
    if(!disk_empty(unit))return UM_INVALID;
    if(unit==1){
        bool enable=currprefs.nr_floppies<2 || currprefs.floppyslots[1].dfxtype<0;
        uae_disk1_present=1;
        if(currprefs.nr_floppies<2)currprefs.nr_floppies=2;
        changed_prefs.nr_floppies=currprefs.nr_floppies;
        currprefs.floppyslots[1].dfxtype=changed_prefs.floppyslots[1].dfxtype=DRV_35_DD;
        if(enable)reset_drive(1);
    }
    const char *name=unit?"df1.adf":"wb12.adf";
    strcpy(changed_prefs.floppyslots[unit].df,name);
    disk_insert(unit,name,!uae_volatile_write);
    /* Match UAE's existing replacement delay, including same-image reinsertion. */
    floppy[unit].dskchange_time=0;
    setdskchangetime(floppy+unit,2*50*312);
    return UM_OK;
}
