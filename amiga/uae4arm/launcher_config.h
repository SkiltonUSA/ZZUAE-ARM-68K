#pragma once
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "profiles.h"
#include "version.h"
#define ZU_PATH 512
struct zu_config {char rom[ZU_PATH],disk[ZU_PATH];unsigned output,renderer,writes,limit,fps,ram,profile,audio,joystick,scanlines;char roms[4][ZU_PATH];};
static const unsigned zu_frames[]={500,1000,1800,3000};
/* Amiga Shell quoting, including expansion characters inside quoted paths. */
static int zu_quote(char *out,size_t cap,const char *in) {
    size_t n=0;if(cap<3)return 0;out[n++]='"';
    for(;*in;in++) {
        unsigned char c=*in;
        if(c<32 || c==127)return 0;
        if(c=='*'||c=='"'||c=='$'||c=='`'){if(n+1>=cap)return 0;out[n++]='*';}
        if(n+2>=cap)return 0;
        out[n++]=c;
    }
    out[n++]='"';out[n]=0;return 1;
}
static int zu_valid(const struct zu_config *c) {
    char q[ZU_PATH*2+3];
    return c->output<2 && c->renderer<2 && c->writes<2 && c->limit<4 && c->fps<4 && c->audio<3 && c->joystick<2 && c->scanlines<4 && c->ram<2 && c->profile<4 &&
        c->rom[0] && c->disk[0] && zu_quote(q,sizeof(q),c->rom) && zu_quote(q,sizeof(q),c->disk);
}
static int zu_command(char *out,size_t size,const char *player,const char *session,const struct zu_config *c) {
    char a[ZU_PATH*2+3],b[ZU_PATH*2+3],d[ZU_PATH*2+3];int n;size_t i;
    if(strlen(session)!=8)return 0;
    for(i=0;i<8;i++)if(!strchr("0123456789abcdefABCDEF",session[i]))return 0;
    if(!zu_valid(c)||!zu_quote(a,sizeof(a),player)||!zu_quote(b,sizeof(b),c->disk)||!zu_quote(d,sizeof(d),c->rom))return 0;
    n=snprintf(out,size,"%s %s RUN %s %u%s%s ROM %s FPS %s RAM %s MODEL %s AUDIO %s JOY %s SCANLINES %u",a,session,b,zu_frames[c->limit],
        c->output?"":c->renderer?" COPY":" LIVE",c->writes?" WRITE":"",d,c->fps==3?"50":c->fps==0?"25":c->fps==1?"30":"MAX",c->ram?"EXPANDED":"BASE",c->profile==0?"A1000":c->profile==1?"A500":c->profile==2?"A500PLUS":"A600",(c->output||!c->audio)?"OFF":c->audio==1?"PAULA":"AHI",c->joystick?"PORT2":"OFF",c->scanlines);
    return n>=0 && (size_t)n<size;
}
static int zu_save(FILE *f,const struct zu_config *c) {
    unsigned i;char q[ZU_PATH*2+3];
    if(!zu_valid(c))return 0;
    for(i=0;i<4;i++)if(!zu_quote(q,sizeof(q),c->roms[i]))return 0;
    if(fprintf(f,"rom=%s\ndisk=%s\noutput=%u\nrenderer=%u\nwrites=%u\nlimit=%u\nfps=%u\nram=%u\nprofile=%u\naudio=%u\njoystick=%u\nscanlines=%u\n",
        c->rom,c->disk,c->output,c->renderer,c->writes,c->limit,c->fps,c->ram,c->profile,c->audio,c->joystick,c->scanlines)<0)return 0;
    for(i=0;i<4;i++)if(fprintf(f,"rom%u=%s\n",i,c->roms[i])<0)return 0;
    return !ferror(f);
}
static int zu_load(FILE *f,struct zu_config *c) {
    struct zu_config next=*c;char line[ZU_PATH+32];
    while(fgets(line,sizeof(line),f)) {
        char *eq,*end;unsigned long v;size_t len=strlen(line);
        if(len && line[len-1]!='\n' && !feof(f))return 0;
        line[strcspn(line,"\r\n")]=0;if(!line[0]||line[0]=='#')continue;
        eq=strchr(line,'=');if(!eq)return 0;*eq++=0;
        if(strlen(line)==4 && !strncmp(line,"rom",3) && line[3]>='0' && line[3]<='3'){
            if(strlen(eq)>=ZU_PATH)return 0;strcpy(next.roms[line[3]-'0'],eq);continue;
        }
        if(!strcmp(line,"rom")||!strcmp(line,"disk")) {
            if(strlen(eq)>=ZU_PATH)return 0;
            strcpy(!strcmp(line,"rom")?next.rom:next.disk,eq);continue;
        }
        v=strtoul(eq,&end,10);if(!*eq||*end||v>3)return 0;
        if(!strcmp(line,"output"))next.output=v;
        else if(!strcmp(line,"renderer"))next.renderer=v;
        else if(!strcmp(line,"writes"))next.writes=v;
        else if(!strcmp(line,"limit"))next.limit=v;
        else if(!strcmp(line,"fps"))next.fps=v;
        else if(!strcmp(line,"ram"))next.ram=v;
        else if(!strcmp(line,"profile"))next.profile=v;
        else if(!strcmp(line,"audio"))next.audio=v;
        else if(!strcmp(line,"joystick"))next.joystick=v;
        else if(!strcmp(line,"scanlines"))next.scanlines=v;
        else return 0;
    }
    if(ferror(f)||!zu_valid(&next))return 0;
    *c=next;return 1;
}
