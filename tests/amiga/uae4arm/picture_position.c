#include <assert.h>
#include "launcher_config.h"
#include "picture_position.h"
int main(void){
 struct zu_config c={.rom="Kick.rom",.profile=3,.picture=3},d=c;char cmd[4096];
 assert(zu_picture_offset(3,0,18)==18);assert(zu_picture_offset(4,0,0)==18);assert(zu_picture_offset(4,1,0)==0);
 assert(zu_command(cmd,sizeof cmd,"player","1234abcd",&c));assert(strstr(cmd," PICTUREUP 18"));
 FILE*f=tmpfile();assert(f);assert(zu_save(f,&c));rewind(f);d.picture=0;assert(zu_load(f,&d)&&d.picture==3);fclose(f);
 c.picture=5;assert(!zu_valid(&c));c.picture=3;c.engine=3;assert(!zu_valid(&c));
 return 0;
}
