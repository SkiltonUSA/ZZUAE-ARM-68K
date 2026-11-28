/* PCMCIA ATA bus decoding, based on UAE4ARM gayle.cpp (GPL-2.0-or-later).
 * The existing ATA core owns commands and sector transfers. This adapter owns
 * only CIS/configuration space and Gayle's byte/word data aliases. */
#pragma once
#include <stdint.h>
#include <string.h>

struct zu_pcmcia {
    unsigned present, disabled, configured;
    uint8_t config[20];
    uint16_t latch;
};
struct zu_pcmcia_io {
    void *context;
    unsigned (*read)(void *, unsigned);
    void (*write)(void *, unsigned, unsigned);
};
/* ATA register numbers match UAE's ide.h, including alternate status. */
#define ZU_PC_DATA 0
#define ZU_PC_CONTROL 0x406
#define ZU_PC_ADDRESS 0x407
static const uint8_t zu_pcmcia_cis[] = {
    0x01,4,0xdf,0x4a,1,0xff,
    0x1c,4,2,0xd9,1,0xff,
    0x18,2,0xdf,1,
    0x15,16,4,1,'Z','Z','U','A','E',0,'A','T','A',' ','C','F',0,0xff,
    0x21,2,4,1, 0x22,2,1,1, 0x22,3,2,0x0c,0x0f,
    0x1a,5,1,2,0,2,0x0f,
    0x1b,6,0xc1,1,0x21,0xb5,0x1e,0x4d,
    0x14,0,0xff
};
static void zu_pcmcia_reset(struct zu_pcmcia *c) {
    c->configured=0;c->latch=0;memset(c->config,0,sizeof c->config);
}
static int zu_pcmcia_register(const struct zu_pcmcia *c,unsigned a) {
    a&=0x7ffff;
    if(!c->present || c->disabled || !c->configured || a<0x20000 || a>=0x40000)return -1;
    a-=0x20000;
    if(a>=0x10000)a=(a&0xffff)|1;
    if(c->configured==1){
        unsigned r=a&15;
        if(r<8)return r;
        if(r==8 || r==9)return ZU_PC_DATA;
        if(r==13)return 1;
        if(r==14)return ZU_PC_CONTROL;
        if(r==15)return ZU_PC_ADDRESS;
    }else if(c->configured==2){
        if(a>=0x1f0 && a<=0x1f7)return a-0x1f0;
        if(a==0x3f6)return ZU_PC_CONTROL;
        if(a==0x3f7)return ZU_PC_ADDRESS;
    }
    return -1;
}
static unsigned zu_pcmcia_read8(struct zu_pcmcia *c,const struct zu_pcmcia_io *io,unsigned a) {
    a&=0x7ffff;
    if(!c->present || c->disabled)return 0;
    if(a>=0x200 && a<0x200+sizeof c->config*2)return c->config[(a-0x200)/2];
    int r=zu_pcmcia_register(c,a);
    if(r==ZU_PC_DATA){
        if(a>=0x30000)return c->latch&255;
        c->latch=io->read(io->context,r);return c->latch>>8;
    }
    if(r>=0)return io->read(io->context,r)&255;
    return a<sizeof zu_pcmcia_cis*2?zu_pcmcia_cis[a/2]:0;
}
static void zu_pcmcia_write8(struct zu_pcmcia *c,const struct zu_pcmcia_io *io,unsigned a,unsigned v) {
    a&=0x7ffff;v&=255;
    if(!c->present || c->disabled)return;
    if(a>=0x40000){zu_pcmcia_reset(c);return;}
    if(a>=0x200 && a<0x200+sizeof c->config*2){
        unsigned n=(a-0x200)/2;c->config[n]=v;
        if(!n){
            if(v&128)zu_pcmcia_reset(c);
            else c->configured=(v&63)==1?1:(v&63)==2?2:0;
        }
        return;
    }
    int r=zu_pcmcia_register(c,a);
    if(r==ZU_PC_DATA){
        if(a>=0x30000)c->latch=v<<8;
        else {c->latch=(c->latch&0xff00)|v;io->write(io->context,r,c->latch);}
    }else if(r>=0)io->write(io->context,r,v);
}
static unsigned zu_pcmcia_read16(struct zu_pcmcia *c,const struct zu_pcmcia_io *io,unsigned a) {
    if(zu_pcmcia_register(c,a)==ZU_PC_DATA){c->latch=io->read(io->context,ZU_PC_DATA);return c->latch;}
    unsigned hi=zu_pcmcia_read8(c,io,a);return (hi<<8)|zu_pcmcia_read8(c,io,a+1);
}
static void zu_pcmcia_write16(struct zu_pcmcia *c,const struct zu_pcmcia_io *io,unsigned a,unsigned v) {
    if(zu_pcmcia_register(c,a)==ZU_PC_DATA)io->write(io->context,ZU_PC_DATA,v&65535);
    else {zu_pcmcia_write8(c,io,a,v>>8);zu_pcmcia_write8(c,io,a+1,v);}
}
