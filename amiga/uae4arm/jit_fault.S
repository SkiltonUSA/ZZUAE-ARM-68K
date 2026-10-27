/* Diagnostic-only Core1 exception landing pad. Entry requires SVC mode with
 * IRQ/FIQ masked. No abort-mode stack is used; longjmp restores the saved SVC
 * integer context. Never enabled by the normal player. */
.syntax unified
.arm
.text
.p2align 5
.global zz_jit_vectors
.hidden zz_jit_vectors
zz_jit_vectors:
 b .Lreset
 b .Lundef
 b .Lsvc
 b .Lprefetch
 b .Ldata
 b .Lreserved
 b .Lirq
 b .Lfiq
.macro FAULT name,reason
\name:
 mov r0,#\reason
 mov r1,lr
 mrs r2,spsr
 cps #0x13
 bic sp,sp,#7
 bl zz_jit_fault
 b .
.endm
FAULT .Lreset,0
FAULT .Lundef,1
FAULT .Lsvc,2
FAULT .Lprefetch,3
FAULT .Ldata,4
FAULT .Lreserved,5
FAULT .Lirq,6
FAULT .Lfiq,7
.section .note.GNU-stack,"",%progbits
