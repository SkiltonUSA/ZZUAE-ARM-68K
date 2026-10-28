"""Preserve Copper cycle phase and CPU-write ordering with optional prediction."""


def copper_prediction(source):
    # The pinned WAIT shortcut can return before committing Copper state, or
    # assign an odd CPU position to a Copper engine advancing two cycles at once.
    start = source.index("\t\t\t\t\t\t/* This will leave c_hpos untouched")
    end = source.index("\n    \t\t\t\t\t}", start)
    aligned_wait = """
#ifdef ZZUAE_COPPER_PREDICT
                        // Keep the two-cycle phase and commit state normally.
                        if (!(c_hpos & 1) && wait_finish > c_hpos)
                            c_hpos = wait_finish <= until_hpos
                                ? wait_finish : ((until_hpos + 1) & ~1);
#else
"""
    source = (source[:start] + aligned_wait + source[start:end] +
              "\n#endif\n" + source[end:])

    # The first-sync/register-type early returns change pixels when CPU colour
    # writes overlap Copper-list modifications and COPJMP restarts. Retain event
    # prediction, but synchronize pending Copper work for every CPU custom access.
    start = source.index("\t\tif (hpos != maxhpos) {", source.index(
        "STATIC_INLINE void sync_copper_with_cpu"))
    end = source.index("\n\t\teventtab[ev_copper].active = 0;", start)
    return (source[:start] + "\n#ifndef ZZUAE_COPPER_PREDICT\n" +
            source[start:end] + "\n#endif\n" + source[end:])
