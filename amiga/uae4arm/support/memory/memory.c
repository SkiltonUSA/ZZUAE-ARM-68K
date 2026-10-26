/* GPL-3.0-or-later. Aligned scalar ARM words; no VFP/NEON or MMIO access.
 * memcpy retains its standard non-overlap contract; mismatched alignment
 * uses bytes. No read or write occurs outside the requested extent. */
#include <stddef.h>
#include <stdint.h>
typedef uint32_t alias_word __attribute__((__may_alias__));
void *memcpy(void *dest,const void *src,size_t n){
    unsigned char *d=dest;const unsigned char *s=src;
    if((((uintptr_t)d^(uintptr_t)s)&3u)==0){
        while(n&&((uintptr_t)d&3u)){*d++=*s++;n--;}
        while(n>=16){
            alias_word *w=(alias_word*)d;const alias_word *r=(const alias_word*)s;
            uint32_t a=r[0],b=r[1],c=r[2],e=r[3];
            w[0]=a;w[1]=b;w[2]=c;w[3]=e;d+=16;s+=16;n-=16;
        }
        while(n>=4){*(alias_word*)d=*(const alias_word*)s;d+=4;s+=4;n-=4;}
    }
    while(n--)*d++=*s++;
    return dest;
}
void *memset(void *dest,int value,size_t n){
    unsigned char *d=dest;unsigned char byte=(unsigned char)value;
    while(n&&((uintptr_t)d&3u)){*d++=byte;n--;}
    uint32_t word=(uint32_t)byte*0x01010101u;
    while(n>=16){alias_word *w=(alias_word*)d;w[0]=word;w[1]=word;w[2]=word;w[3]=word;d+=16;n-=16;}
    while(n>=4){*(alias_word*)d=word;d+=4;n-=4;}
    while(n--)*d++=byte;
    return dest;
}
void __aeabi_memcpy(void*d,const void*s,size_t n){memcpy(d,s,n);}
void __aeabi_memcpy4(void*d,const void*s,size_t n){memcpy(d,s,n);}
void __aeabi_memcpy8(void*d,const void*s,size_t n){memcpy(d,s,n);}
void __aeabi_memclr(void*d,size_t n){memset(d,0,n);}
void __aeabi_memclr4(void*d,size_t n){memset(d,0,n);}
void __aeabi_memclr8(void*d,size_t n){memset(d,0,n);}
