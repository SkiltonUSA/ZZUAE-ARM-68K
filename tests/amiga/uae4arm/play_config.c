#include "launcher_config.h"
#include <assert.h>
int main(void) {
    struct zu_config c={0};char cmd[4096];
    strcpy(c.rom,"ROMs/Kick13.rom");strcpy(c.disk,"Disks/Demo.adf");
    c.limit=2;c.audio=2;c.showfps=1;
    assert(zu_command(cmd,sizeof(cmd),"ZZUAE-Player","1234abcd",&c));
    assert(strstr(cmd," SHOWFPS"));
    assert(strstr(cmd," 0 LIVE ROM ")); /* normal play has no test limit */
    c.fullscreen=1;c.renderer=1;c.output=1;
    assert(zu_command(cmd,sizeof(cmd),"player","1234abcd",&c));
    assert(strstr(cmd," 0 LIVE ROM ") && strstr(cmd," FULLSCREEN"));
    assert(strstr(cmd," AUDIO AHI") && !strstr(cmd," COPY"));
    FILE *f=tmpfile();assert(f);assert(zu_save(f,&c));rewind(f);
    struct zu_config loaded={0};assert(zu_load(f,&loaded));fclose(f);
    assert(loaded.fullscreen==1 && loaded.testing==0 && loaded.showfps==1);
    c.testing=1;
    assert(zu_command(cmd,sizeof(cmd),"player","1234abcd",&c));
    assert(strstr(cmd," 1800 ROM ") && !strstr(cmd," FULLSCREEN"));
    assert(strstr(cmd," AUDIO OFF") && !strstr(cmd," SHOWFPS"));
    c.output=0;
    assert(zu_command(cmd,sizeof(cmd),"player","1234abcd",&c));
    assert(strstr(cmd," 1800 COPY ROM ") && strstr(cmd," FULLSCREEN"));
    c.renderer=0;c.fullscreen=0;
    assert(zu_command(cmd,sizeof(cmd),"player","1234abcd",&c));
    assert(strstr(cmd," 1800 LIVE ROM ") && !strstr(cmd," FULLSCREEN"));
    c.fullscreen=2;assert(!zu_valid(&c));
    puts("PASS: unlimited normal play, isolated test options, display modes and saved mode");
}
