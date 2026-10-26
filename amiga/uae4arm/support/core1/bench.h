#pragma once
#include <stdint.h>
struct MesenResult {
    uint32_t checked, mismatch, cycles, hash, errors, unsupported, ticks;
    uint32_t actual_pc, expected_pc, actual_regs, expected_regs;
};
#ifdef __cplusplus
extern "C" {
#endif
// stop is sampled between bounded instruction groups, including validation.
int mesen_test(int verify, struct MesenResult *, int (*stop)(void), uint32_t (*clock)(void));
void mesen_progress(uint32_t phase);
#ifdef __cplusplus
}
#endif
