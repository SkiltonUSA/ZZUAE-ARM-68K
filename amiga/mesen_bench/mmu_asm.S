/* GPL-3.0-or-later. Core1-only MMU/L1 experiment. No L2 MMIO writes or
 * broadcast cache maintenance. No stack stores between final L1 clean and
 * restoring uncached identity execution. See mmu.c and mmu_plan.h. */
#include "layout.h"
#include "mmu.h"
.syntax unified
.arm
.section .text.entry,"ax"
.global _start
.hidden _start
_start:
    mrc p15,0,r1,c1,c0,0
    movw r2,#0x1005
    tst r1,r2
    bxne lr
    mrc p15,0,r1,c0,c0,5
    and r1,r1,#255
    cmp r1,#1
    bxne lr
    mrs r3,cpsr
    and r1,r3,#31
    cmp r1,#19
    cmpne r1,#31
    bxne lr
    push {r4-r11,lr}
    mov r4,sp
    ldr r5,[r0,#4]
    mov r6,r3
    cpsid aif
    /* Keep the active stack wholly inside fully owned cacheable pages. */
    add sp,r5,#ZZ_BLOCK_SIZE
    movw r0,#4095
    bic sp,sp,r0
    sub sp,sp,#16
    mov r0,r5
    mov r1,r6
    bl mb_mmu_prepare
    cmp r0,#1
    bne .Lreturn
    ldr r0,=MB_MMU_STATE
    add r0,r5,r0
    bl mb_mmu_enable
    mov r0,r5
    bl zz_worker
    ldr r0,=MB_MMU_STATE
    add r0,r5,r0
    bl mb_mmu_disable
.Lreturn:
    mov r0,r5
    bl mb_mmu_report
    mov sp,r4
    msr cpsr_cx,r6 /* restore A (bit 8) as well as IRQ/FIQ masks and mode */
    mrs r0,cpsr
    movw r2,#511
    and r0,r0,r2
    rev r0,r0
    ldr r1,=MB_MMU_REPORT+136
    str r0,[r5,r1]
    ldr r1,=ZZ_DIAG+24
    movw r0,#0x4552
    movt r0,#0x3154
    str r0,[r5,r1]
    dsb sy
    pop {r4-r11,pc}

.text
.global mb_mmu_enable
.hidden mb_mmu_enable
mb_mmu_enable:
    push {r4,lr}
    mov r4,r0
    bl .Ll1_clean_invalidate
    mov r0,#0
    mcr p15,0,r0,c7,c5,0 /* local ICIALLU */
    mcr p15,0,r0,c7,c5,6 /* local BPIALL */
    dsb sy
    mcr p15,0,r0,c2,c0,2 /* TTBCR N=0, all lookups through TTBR0 */
    ldr r1,[r4,#MS_TABLE]
    mcr p15,0,r1,c2,c0,0 /* NC walks to our aligned table */
    mov r1,#1
    mcr p15,0,r1,c3,c0,0 /* domain 0 client, all other domains fault */
    mcr p15,0,r0,c8,c7,0 /* local TLBIALL, not Inner Shareable variant */
    dsb sy
    isb
    ldr r0,[r4,#MS_RUNNING]
    mcr p15,0,r0,c1,c0,0
    isb
    pop {r4,pc}

.global mb_mmu_disable
.hidden mb_mmu_disable
mb_mmu_disable:
    push {r4,lr}
    mov r4,r0
    /* This includes dirty stack/global/private data. The following sequence
     * does not write memory until MMU/D-cache are disabled again. */
    bl .Ll1_clean_invalidate
    ldr r0,[r4,#MS_SCTLR]
    mcr p15,0,r0,c1,c0,0
    isb
    ldr r0,[r4,#MS_TTBR0]
    mcr p15,0,r0,c2,c0,0
    ldr r0,[r4,#MS_TTBR1]
    mcr p15,0,r0,c2,c0,1
    ldr r0,[r4,#MS_TTBCR]
    mcr p15,0,r0,c2,c0,2
    ldr r0,[r4,#MS_DACR]
    mcr p15,0,r0,c3,c0,0
    mov r0,#0
    mcr p15,0,r0,c8,c7,0
    mcr p15,0,r0,c7,c5,0
    mcr p15,0,r0,c7,c5,6
    dsb sy
    isb
    pop {r4,pc}

/* CCSIDR was checked: 32 KiB, four ways, 256 sets, 32-byte lines.
 * Level field is zero throughout. Only this CPU's L1 is operated on. */
.Ll1_clean_invalidate:
    dsb sy
    mov r0,#0
.Lway:
    mov r1,#0
.Lset:
    orr r2,r0,r1
    mcr p15,0,r2,c7,c14,2
    add r1,r1,#32
    cmp r1,#8192
    bne .Lset
    adds r0,r0,#0x40000000
    bne .Lway
    dsb sy
    bx lr
