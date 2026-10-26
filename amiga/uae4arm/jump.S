/* Integer-only AAPCS context for the -mfloat-abi=soft diagnostic worker.
 * No VFP/NEON code may be linked while using these helpers. */
.syntax unified
.arm
.text
.global setjmp
.hidden setjmp
.type setjmp,%function
setjmp:
    stmia r0, {r4-r11,sp,lr}
    mov r0, #0
    bx lr
.size setjmp,.-setjmp
.global longjmp
.hidden longjmp
.type longjmp,%function
longjmp:
    ldmia r0, {r4-r11,sp,lr}
    movs r0, r1
    moveq r0, #1
    bx lr
.size longjmp,.-longjmp
.section .note.GNU-stack,"",%progbits
