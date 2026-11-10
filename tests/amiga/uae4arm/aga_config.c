#include "launcher_config.h"
#include <assert.h>
int main(){
 struct zu_config c={.rom="ROMs/A1200.rom",.profile=ZP_A1200,.engine=2,.writes=2,.ntsc=1,.joystick=2,.hdf="SD032G:Disks/My HDF.hdf"},d={0};
 char cmd[4096];assert(zu_command(cmd,sizeof cmd,zu_player(&c),"102938ab",&c));
 assert(strstr(cmd,"VIDEO NTSC")&&strstr(cmd," SAVE ")&&strstr(cmd,"JOY USB")&&strstr(cmd,"HDF \"SD032G:Disks/My HDF.hdf\""));
 FILE*f=tmpfile();assert(f&&zu_save(f,&c));rewind(f);assert(zu_load(f,&d));fclose(f);
 assert(d.ntsc==1&&d.writes==2&&d.joystick==2&&!strcmp(d.hdf,c.hdf));
 c.profile=ZP_A500;assert(!zu_valid(&c));c.profile=ZP_A600;assert(zu_valid(&c));
 c.engine=0;strcpy(c.rom,"ROMs/Kick205.rom");
 assert(zu_command(cmd,sizeof cmd,zu_player(&c),"102938ab",&c));
 assert(strstr(cmd,"MODEL A600")&&strstr(cmd,"RUN \"\" 0")&&strstr(cmd," HDF ")&&strstr(cmd," SAVE "));
 c.ntsc=2;assert(!zu_valid(&c));
 puts("PASS NTSC, USB, HDF-only boot and persistent image-write configuration");
}
