#include "launcher_config.h"
#include <assert.h>
int main(void){
 struct zu_config c={.rom="ROMs/Kick13.rom",.disk="Disks/Boot.adf"},d=c;
 char cmd[4096];FILE *f;
 assert(zu_command(cmd,sizeof(cmd),"ZZUAE-Player","1234abcd",&c));assert(!strstr(cmd," DF1 "));
 c.rtc=1;
 strcpy(c.disk1,"Disks/Second *$`\" disk.adf");
 assert(zu_command(cmd,sizeof(cmd),"ZZUAE-Player","1234abcd",&c));assert(strstr(cmd," DF1 \"Disks/Second ***$*`*\" disk.adf\""));
 f=tmpfile();assert(f&&zu_save(f,&c));rewind(f);assert(zu_load(f,&d));fclose(f);assert(!strcmp(c.disk1,d.disk1)&&d.rtc==1);assert(strstr(cmd," RTC ON"));
 f=tmpfile();fputs("disk1=\n",f);rewind(f);assert(zu_load(f,&d)&&!d.disk1[0]);fclose(f);
 f=tmpfile();fputs("disk=Disks/Legacy.adf\n",f);rewind(f);assert(zu_load(f,&d)&&!d.disk1[0]);fclose(f);
 strcpy(c.disk1,"bad\ncommand");assert(!zu_valid(&c));
 puts("PASS DF1 optional selection, quoting, save/load, eject and old settings");
}
