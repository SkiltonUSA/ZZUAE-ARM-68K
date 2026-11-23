/* Only idle AGA fetch phases. Stop before any state-changing boundary. */
STATIC_INLINE int zz_idle_span(int pos, int until, int stop, int dma, int fm)
{
    if (fm != 2 || !dma || line_cyclebased || badmode || bpldmasetuphpos > 0 ||
        bpl1dat_written || fetch_state != fetch_started || plf_state != plf_active)
        return 0;
    int phase = fetch_cycle & fetchstart_mask;
    if (phase < fm_maxplane || toscr_nbits < 0 || toscr_nbits >= 16 ||
        (toscr_res2p != 2 && toscr_res2p != 4 && toscr_res2p != 8) ||
        ((16 - toscr_nbits) & (toscr_res2p - 1)))
        return 0;
    int count = fetchstart - phase;
    if (count > until - pos) count = until - pos;
    if (count > stop - pos) count = stop - pos;
    int unit = fetchunit - (fetch_cycle & fetchunit_mask);
    if (count > unit) count = unit;
    int flush = (16 - toscr_nbits) >> __builtin_ctz((unsigned)toscr_res2p);
    if (count > flush) count = flush;
    return count >= 2 ? count : 0;
}
