.text
.globl _sample_entry
_sample_entry:
 movem.l %d0-%d7/%a0-%a6,-(%sp)
 jsr _sample_body
 movem.l (%sp)+,%d0-%d7/%a0-%a6
 moveq #0,%d0
 rts
