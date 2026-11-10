"""Specialise the measured normal AGA stretch path; preserve other modes."""


def aga_pixel_loop(source):
    a = source.index('static int NOINLINE linetoscr_16_stretch1_aga')
    z = source.index('\n#endif', a)
    section = source[a:z]
    marker='''    } else {
        while (dpix < dpix_end) {
            uae_u32 spix_val;
            uae_u32 out_val;

            spix_val = (pixdata.apixels[spix++] ^ xor_val) & and_val;'''
    assert section.count(marker)==1
    new='''    } else if (xor_val == 0 && and_val == 255) {
        /* Four independent palette lookups; retain the original two-pixel
         * tail and exact source advance for short or split spans. */
        while (dpix_end - dpix >= 8) {
            uae_u32 a = p_acolors[pixdata.apixels[spix]];
            uae_u32 b = p_acolors[pixdata.apixels[spix + 1]];
            uae_u32 c = p_acolors[pixdata.apixels[spix + 2]];
            uae_u32 d = p_acolors[pixdata.apixels[spix + 3]];
            *((uae_u32 *)&buf[dpix]) = a;
            *((uae_u32 *)&buf[dpix + 2]) = b;
            *((uae_u32 *)&buf[dpix + 4]) = c;
            *((uae_u32 *)&buf[dpix + 6]) = d;
            spix += 4;
            dpix += 8;
        }
        while (dpix < dpix_end) {
            *((uae_u32 *)&buf[dpix]) = p_acolors[pixdata.apixels[spix++]];
            dpix += 2;
        }
'''+marker
    # marker starts with closing brace, closing the inserted branch.
    return source[:a]+section.replace(marker,new)+source[z:]
