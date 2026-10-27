.text
.globl _start
_start:
 move.b #2,0xbfe001
 move.w #0xf00,0xdff180
 moveq #23,%d7
2:
 fmove.l #3,%fp0
 fadd.l #5,%fp0
 fmul.l #4,%fp0
 fdiv.l #2,%fp0
 fmove.l %fp0,%d0
 move.l %d0,0x10000
 fsqrt.x %fp0,%fp1
 fmove.l %fp1,%d0
 move.l %d0,0x10004
 fmove.x %fp0,0x10008
 fmove.l #0x20,%fpcr
 fmove.d #0r2.75,%fp0
 fint.x %fp0,%fp1
 fmove.l %fp1,%d0
 move.l %d0,0x10014
 fmove.l #0x30,%fpcr
 fint.x %fp0,%fp1
 fmove.l %fp1,%d0
 move.l %d0,0x10018
 fmove.l #0,%fpcr
 fmove.d #0r2.5,%fp0
 fint.x %fp0,%fp1
 fmove.l %fp1,%d0
 move.l %d0,0x1001c
 fmove.d #0r3.5,%fp0
 fint.x %fp0,%fp1
 fmove.l %fp1,%d0
 move.l %d0,0x10020
 fsave 0x10200
 frestore 0x10200
 dbra %d7,2b
 move.l #0x46505531,0x10024
1: bra.s 1b
