/* Private experiment: only unclipped, unmasked, non-collision spans. */
template<int Dup> static inline void zz_sprite_plain(uae_u16 *buf, uae_u32 datab, int num)
{
    while (datab) {
        unsigned col = (datab & 3) << (2 * num);
        for (int i = 0; i < (1 << Dup); ++i) buf[i] |= col;
        buf += 1 << Dup;
        datab >>= 2;
    }
}
