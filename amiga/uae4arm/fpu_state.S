/* GPL-3.0-or-later. Full VFP state boundary for the optional guest FPU.
 * Called only after zu_neon_available. Never changes CPACR or FPEXC. */
.syntax unified
.arm
.fpu vfpv3
.text
.global zu_fpu_restore
.hidden zu_fpu_restore
.type zu_fpu_restore,%function
zu_fpu_restore:
    vldmia r0!,{d0-d15}
    vldmia r0!,{d16-d31}
    ldr r1,[r0]
    vmsr fpscr,r1
    bx lr
.size zu_fpu_restore,.-zu_fpu_restore
.global zu_fpu_clear
.hidden zu_fpu_clear
.type zu_fpu_clear,%function
zu_fpu_clear:
    mov r0,#0
    vmsr fpscr,r0
    bx lr
.size zu_fpu_clear,.-zu_fpu_clear
/* softfp ABI, round using the guest FPCR mapped into FPSCR by UAE. */
.global zu_fpu_to_int
.hidden zu_fpu_to_int
.type zu_fpu_to_int,%function
zu_fpu_to_int:
    vmov d0,r0,r1
    vcvtr.s32.f64 s0,d0
    vmov r0,s0
    bx lr
.size zu_fpu_to_int,.-zu_fpu_to_int
.global zu_fpu_sqrt
.hidden zu_fpu_sqrt
.type zu_fpu_sqrt,%function
zu_fpu_sqrt:
    vmov d0,r0,r1
    vsqrt.f64 d0,d0
    vmov r0,r1,d0
    bx lr
.size zu_fpu_sqrt,.-zu_fpu_sqrt
.section .note.GNU-stack,"",%progbits
