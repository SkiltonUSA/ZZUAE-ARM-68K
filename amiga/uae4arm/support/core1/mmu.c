#include "mmu.h"
#include "wire.h"
#define GET(reg,op) __asm__ volatile("mrc p15," op : "=r"(reg))
int mb_mmu_prepare(volatile uint8_t *base,uint32_t original_cpsr) {
    uint32_t *s=(uint32_t *)(base+MB_MMU_STATE),addr=(uint32_t)base;
    uint32_t midr,mpidr,zero=0,ccsidr,ttbr=mb_align_up(addr+MB_TABLE_BEGIN,16384u);
    GET(s[0],"0,%0,c1,c0,0");GET(s[1],"0,%0,c2,c0,0");GET(s[2],"0,%0,c2,c0,1");
    GET(s[3],"0,%0,c2,c0,2");GET(s[4],"0,%0,c3,c0,0");GET(s[5],"2,%0,c0,c0,0");
    s[6]=original_cpsr;
    GET(s[7],"0,%0,c1,c0,1");GET(s[8],"0,%0,c13,c0,1");
    GET(s[9],"0,%0,c10,c2,0");GET(s[10],"0,%0,c10,c2,1");GET(s[11],"0,%0,c12,c0,0");
    s[12]=*(volatile uint32_t *)0xf8f02100u;s[13]=*(volatile uint32_t *)0xf8f02104u;
    GET(midr,"0,%0,c0,c0,0");GET(mpidr,"0,%0,c0,c0,5");
    ad_put(base,ZZ_DIAG+28,s[0]);ad_put(base,MB_MMU_REPORT,1);
    /* The L1-only set/way loop is explicitly sized for this verified A9. */
    __asm__ volatile("mcr p15,2,%0,c0,c0,0\n isb"::"r"(zero):"memory");
    GET(ccsidr,"1,%0,c0,c0,0");s[14]=ccsidr;
    __asm__ volatile("mcr p15,2,%0,c0,c0,0\n isb"::"r"(s[5]):"memory");
    if((s[0]&0x1005u) || midr!=0x413fc090u || (mpidr&255)!=1 ||
       ((original_cpsr&31)!=19 && (original_cpsr&31)!=31) || (ccsidr&7)!=1 || ((ccsidr>>3)&1023)!=3 ||
       ((ccsidr>>13)&32767)!=255)return 0;
    if(!mb_make_tables(addr,(uint32_t *)ttbr,ttbr,(uint32_t *)(ttbr+16384),ttbr+16384))return 0;
    s[15]=ttbr;
    /* Disable TEX remapping and access-flag reinterpretation locally. */
    s[16]=(s[0]&~0x30000000u)|0x1001u;
#ifdef MB_DCACHE
    s[16]|=4u;
#endif
    s[18]=2;
    ad_put(base,MB_MMU_REPORT,2);
    __asm__ volatile("dsb sy":::"memory");return 1;
}
void mb_mmu_report(volatile uint8_t *base) {
    uint32_t *s=(uint32_t *)(base+MB_MMU_STATE),now[14],i,bad=0;
    GET(now[0],"0,%0,c1,c0,0");GET(now[1],"0,%0,c2,c0,0");GET(now[2],"0,%0,c2,c0,1");
    GET(now[3],"0,%0,c2,c0,2");GET(now[4],"0,%0,c3,c0,0");GET(now[5],"2,%0,c0,c0,0");
    __asm__ volatile("mrs %0,cpsr":"=r"(now[6]));
    GET(now[7],"0,%0,c1,c0,1");GET(now[8],"0,%0,c13,c0,1");
    GET(now[9],"0,%0,c10,c2,0");GET(now[10],"0,%0,c10,c2,1");GET(now[11],"0,%0,c12,c0,0");
    now[12]=*(volatile uint32_t *)0xf8f02100u;now[13]=*(volatile uint32_t *)0xf8f02104u;
    for(i=0;i<14;i++) {
        /* Interrupt masks are restored by entry after this C function.
         * Record every other control register as an exact equality. */
        if(i!=6 && now[i]!=s[i])bad|=1u<<i;
        ad_put(base,MB_MMU_REPORT+16+i*4,s[i]);
        ad_put(base,MB_MMU_REPORT+80+i*4,now[i]);
    }
    ad_put(base,ZZ_DIAG+32,now[0]);ad_put(base,MB_MMU_REPORT+4,bad);
    ad_put(base,MB_MMU_REPORT+8,s[15]);ad_put(base,MB_MMU_REPORT+12,s[14]);
    ad_put(base,MB_MMU_REPORT,3);__asm__ volatile("dsb sy":::"memory");
}
