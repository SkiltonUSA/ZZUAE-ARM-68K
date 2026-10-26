#pragma once
#include <stdint.h>
enum { ZP_A1000, ZP_A500, ZP_A500PLUS, ZP_A600, ZP_LEGACY };
static inline uint32_t zp_crc_byte(uint32_t c,uint8_t b) {
    static const uint32_t t[16]={0,0x1db71064,0x3b6e20c8,0x26d930ac,0x76dc4190,0x6b6b51f4,0x4db26158,0x5005713c,0xedb88320,0xf00f9344,0xd6d6a3e8,0xcb61b38c,0x9b64c2b0,0x86d3d2d4,0xa00ae278,0xbdbdf21c};
    c^=b;c=(c>>4)^t[c&15];return (c>>4)^t[c&15];
}
/* Recognized A3000 ROMs can share the version of the requested small Amiga.
 * Other checksum-valid custom images still require actual compatibility tests. */
static inline int zp_rom_target_ok(uint32_t crc) {
    return crc!=0xe0f37258u && crc!=0xb333d3c6u && crc!=0x234a7233u;
}
static inline uint32_t zp_chip(unsigned profile,unsigned expanded) {
    if(profile==ZP_A1000)return expanded?0x80000u:0x40000u;
    if(profile==ZP_A500 || profile==ZP_LEGACY)return 0x80000u;
    return expanded?0x200000u:0x100000u;
}
static inline uint32_t zp_slow(unsigned profile,unsigned expanded) {
    return (profile==ZP_A500 || profile==ZP_LEGACY) && expanded?0x80000u:0;
}
static inline uint32_t zp_rom_size(unsigned profile) {return profile==ZP_A500PLUS || profile==ZP_A600?0x80000u:0x40000u;}
static inline int zp_rom_matches(unsigned profile,unsigned major,unsigned revision) {
    switch(profile){
        case ZP_A1000:return major==33;
        case ZP_A500:return major==34;
        case ZP_A500PLUS:return major==37 && revision==175;
        case ZP_A600:return major==37 && (revision==299 || revision==300 || revision==350);
        case ZP_LEGACY:return major==33 || major==34;
    }
    return 0;
}
