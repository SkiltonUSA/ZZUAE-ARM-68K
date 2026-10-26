/* GPL-3.0-or-later. Identity map only this launcher's owned allocation plus
 * one read-only private-peripheral page. All other L1 entries fault. */
#pragma once
#ifndef __ASSEMBLER__
#include <stdint.h>
#endif
#define MB_TABLE_BEGIN 0x40000u
#define MB_TABLE_END 0x50000u
#define MB_WITNESS 0x60000u
#define MB_PUBLIC_BEGIN 0x80000u
#define MB_PUBLIC_END 0x84000u
#define MB_MMU_STATE 0x82000u
#define MB_MMU_REPORT 0x82400u
#ifndef MB_ALLOCATION
#define MB_ALLOCATION 0x100000u
#endif
/* Worst-case section crossing, plus the private timer page. */
#define MB_OWNED_TABLES ((MB_ALLOCATION>>20)+1u)
#define MB_L2_BYTES ((MB_OWNED_TABLES+1u)*1024u)
#define MB_TIMER_PAGE 0xf8f00000u
/* ARMv7 short small-page descriptor: TEX[2:0]=100, C=0, B=1:
 * Normal, inner WB/WA, outer noncacheable; S=0; AP=01 privileged RW. */
#define MB_PAGE_PRIVATE 0x116u
/* TEX=001,C=B=0: Normal inner/outer NC, S=1, AP=01. */
#define MB_PAGE_SHARED 0x452u
/* Strongly ordered, AP=101 privileged RO, XN=1. */
#define MB_PAGE_TIMER 0x213u
#ifndef __ASSEMBLER__
static inline uint32_t mb_align_up(uint32_t p,uint32_t n) { return (p+n-1)&~(n-1); }
static inline int mb_overlap(uint32_t page,uint32_t first,uint32_t end) {
    return page<end && page+4096>first;
}
static inline uint32_t mb_page_attr(uint32_t base,uint32_t page) {
    uint32_t attr;
    if(page==MB_TIMER_PAGE)return MB_PAGE_TIMER;
    if(!mb_overlap(page,base,base+MB_ALLOCATION))return 0;
    attr=MB_PAGE_PRIVATE;
    if(page<base || page+4096>base+MB_ALLOCATION ||
       mb_overlap(page,base+MB_TABLE_BEGIN,base+MB_TABLE_END) ||
       mb_overlap(page,base+MB_PUBLIC_BEGIN,base+MB_PUBLIC_END))attr=MB_PAGE_SHARED;
    if(page>=base+MB_TABLE_BEGIN)attr|=1u; /* non-code regions XN */
    return attr;
}
static inline int mb_make_tables(uint32_t base,uint32_t *l1,uint32_t l1addr,
                                 uint32_t *l2,uint32_t l2addr) {
    uint32_t i,page,first,section,slot=0,last=~0u;
    if(base<0x10000000u || base>0x201f0000u-MB_ALLOCATION || (base&63u) ||
       l1addr!=mb_align_up(base+MB_TABLE_BEGIN,16384u) || l2addr!=l1addr+16384u ||
       l2addr+MB_L2_BYTES>base+MB_TABLE_END)return 0;
    for(i=0;i<4096;i++)l1[i]=0;
    for(i=0;i<MB_L2_BYTES/4;i++)l2[i]=0;
    first=base&~4095u;
    for(page=first;page<base+MB_ALLOCATION;page+=4096u) {
        section=page>>20;
        if(section!=last) {
            if(slot>=MB_OWNED_TABLES)return 0;
            l1[section]=(l2addr+1024u*slot)|1u;last=section;slot++;
        }
        l2[(slot-1)*256+((page>>12)&255)]=page|mb_page_attr(base,page);
    }
    l1[MB_TIMER_PAGE>>20]=(l2addr+MB_OWNED_TABLES*1024u)|1u;
    l2[MB_OWNED_TABLES*256+((MB_TIMER_PAGE>>12)&255)]=MB_TIMER_PAGE|MB_PAGE_TIMER;
    return 1;
}
#endif
