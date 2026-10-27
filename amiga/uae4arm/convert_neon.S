/* GPL-3.0-or-later. Optional, bounded RGB565 -> P96 row conversion.
 * Integer NEON only. Preserve every touched D register, never call out or
 * change CPACR/FPEXC/FPSCR. Inputs are private cached RAM, not the RTG mapping.
 * A completed leaf cannot leave SIMD state across the integer setjmp boundary.
 */
.syntax unified
.arm
.fpu neon
.text
.global zu_neon_available
.hidden zu_neon_available
.type zu_neon_available,%function
zu_neon_available:
    mrc p15,0,r1,c1,c0,2
    tst r1,#0xc0000000
    bne 1f
    and r1,r1,#0x00f00000
    cmp r1,#0x00f00000
    bne 1f
    isb
    vmrs r1,fpexc
    tst r1,#0x40000000
    beq 1f
    vmrs r1,mvfr0
    and r1,r1,#15
    cmp r1,#2
    bne 1f
    vmrs r1,mvfr1
    ubfx r1,r1,#8,#12
    movw r2,#0x111
    cmp r1,r2
    moveq r0,#1
    bxeq lr
1:  mov r0,#0
    bx lr
.size zu_neon_available,.-zu_neon_available

.global zu_neon_snapshot
.hidden zu_neon_snapshot
.type zu_neon_snapshot,%function
zu_neon_snapshot:
    vstmia r0!,{d0-d15}
    vstmia r0!,{d16-d31}
    vmrs r1,fpscr
    str r1,[r0]
    bx lr
.size zu_neon_snapshot,.-zu_neon_snapshot

/* void zu_convert_neon(uint32_t *out, const uint16_t *src,
 *                      unsigned format, unsigned level);
 * Exactly 640 pixels, format 3/4, level 0..8, disjoint buffers.
 */
.global zu_convert_neon
.hidden zu_convert_neon
.type zu_convert_neon,%function
zu_convert_neon:
    vpush {d0-d7}
    vpush {d16-d23}
    vdup.16 q9,r3
    mov r12,#80
2:  vld1.16 {d0,d1},[r1]!
    vshr.u16 q1,q0,#11
    vmov.i16 q8,#31
    vand q3,q0,q8
    vshr.u16 q2,q0,#5
    vmov.i16 q8,#63
    vand q2,q2,q8
    vshl.i16 q8,q1,#3
    vshr.u16 q1,q1,#2
    vorr q1,q1,q8
    vshl.i16 q8,q2,#2
    vshr.u16 q2,q2,#4
    vorr q2,q2,q8
    vshl.i16 q8,q3,#3
    vshr.u16 q3,q3,#2
    vorr q3,q3,q8
    vmul.i16 q1,q1,q9
    vmul.i16 q2,q2,q9
    vmul.i16 q3,q3,q9
    vshr.u16 q1,q1,#3
    vshr.u16 q2,q2,#3
    vshr.u16 q3,q3,#3
    vmov.i16 q8,#255
    vmul.i16 q8,q8,q9
    vshr.u16 q8,q8,#3
    vmovn.i16 d20,q3
    vmovn.i16 d21,q2
    vmovn.i16 d22,q1
    vmovn.i16 d23,q8
    cmp r2,#3
    beq 3f
    vswp d20,d23
    vswp d21,d22
3:  vst4.8 {d20,d21,d22,d23},[r0]!
    subs r12,r12,#1
    bne 2b
    vpop {d16-d23}
    vpop {d0-d7}
    bx lr
.size zu_convert_neon,.-zu_convert_neon
.section .note.GNU-stack,"",%progbits
