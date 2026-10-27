/* Adapt the upstream ARM double backend to our softfp ABI and VFP rounding.
 * The core still has the upstream double/extended-precision limitation. */
extern "C" int zu_fpu_to_int(double);
extern "C" double zu_fpu_sqrt(double);
static double zu_fpu_round(double value){
    union {double d; uint64_t u;} bits={value};
    unsigned exponent=(unsigned)((bits.u>>52)&2047);
    if(exponent>=1075 || !(bits.u&0x7fffffffffffffffull))return value;
    double magic=(bits.u>>63)?-4503599627370496.0:4503599627370496.0;
    volatile double sum=value+magic;
    double result=sum-magic;
    if(result==0.0){bits.u&=0x8000000000000000ull;return bits.d;}
    return result;
}
#define lrintl(x) zu_fpu_to_int(x)
#define rintl(x) zu_fpu_round(x)
#define sqrtl(x) zu_fpu_sqrt(x)
