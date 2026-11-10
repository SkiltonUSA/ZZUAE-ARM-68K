.syntax unified
.cpu cortex-a9
.fpu neon
.arm
.text
.global zu_sprite_or16
.hidden zu_sprite_or16
.type zu_sprite_or16,%function
/* Private cached sprite buffer; caller checks clipping, scale and collisions.
 * r0=destination, r1=16 packed two-bit pixels, r2=sprite shift, r3=scale log2.
 * Preserve all touched SIMD state; no callbacks, FP arithmetic or saturation. */
.macro store_or reg
    vld1.16 {q4},[r0]
    vorr q4,q4,\reg
    vst1.16 {q4},[r0]!
.endm
.macro store_quad reg
    vmov q2,\reg
    vzip.16 \reg,q2
    vmov q3,\reg
    vzip.16 \reg,q3
    store_or \reg
    store_or q3
    vmov q3,q2
    vzip.16 q2,q3
    store_or q2
    store_or q3
.endm
zu_sprite_or16:
    vpush {d0-d9}
    vdup.16 q0,r1
    lsr r1,r1,#16
    vdup.16 q1,r1
    adr r12,.Lshifts
    vld1.16 {q2},[r12]
    vshl.u16 q0,q0,q2
    vshl.u16 q1,q1,q2
    vmov.i16 q3,#3
    vand q0,q0,q3
    vand q1,q1,q3
    vdup.16 q2,r2
    vshl.u16 q0,q0,q2
    vshl.u16 q1,q1,q2
    cmp r3,#1
    beq .Ldouble
    bhi .Lquad
    store_or q0
    store_or q1
    b .Ldone
.Ldouble:
    vmov q2,q0
    vzip.16 q0,q2
    vmov q3,q1
    vzip.16 q1,q3
    store_or q0
    store_or q2
    store_or q1
    store_or q3
    b .Ldone
.Lquad:
    store_quad q0
    store_quad q1
.Ldone:
    vpop {d0-d9}
    bx lr
.size zu_sprite_or16,.-zu_sprite_or16
.balign 16
.Lshifts:
    .hword 0,-2,-4,-6,-8,-10,-12,-14
