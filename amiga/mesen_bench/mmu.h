#pragma once
#include "mmu_plan.h"
/* Native-endian internal snapshot in the UNCACHED control area. Offsets are
 * also used by mmu_asm.S. Shared readback is separately serialized BE. */
#define MS_SCTLR 0
#define MS_TTBR0 4
#define MS_TTBR1 8
#define MS_TTBCR 12
#define MS_DACR 16
#define MS_CSSELR 20
#define MS_CPSR 24
#define MS_ACTLR 28
#define MS_CONTEXT 32
#define MS_PRRR 36
#define MS_NMRR 40
#define MS_VBAR 44
#define MS_L2CTRL 48
#define MS_L2AUX 52
#define MS_CCSIDR 56
#define MS_TABLE 60
#define MS_RUNNING 64
#define MS_RESTORED 68
#define MS_PHASE 72
#ifndef __ASSEMBLER__
#ifdef __cplusplus
extern "C" {
#endif
int mb_mmu_prepare(volatile uint8_t *,uint32_t);
void mb_mmu_enable(volatile uint8_t *);
void mb_mmu_disable(volatile uint8_t *);
void mb_mmu_report(volatile uint8_t *);
#ifdef __cplusplus
}
#endif
#endif
