#!/usr/bin/env python3
"""Adapt pinned UAE4ARM GPL NEON bitplane leaves to ZZUAE's context contract.

The upstream transpose algorithm is unchanged. Pass the first plane address,
not a global line index, and preserve all D registers/FPSCR across the leaf.
"""
import re
from pathlib import Path

def generate(upstream: Path, target: Path):
    source=(upstream/'src/od-pandora/neon_helper.s').read_text()
    body=[]
    for planes in range(2,7):
        start=source.index(f'NEON_doline_n{planes}:')
        end=source.index('\n.align',start)
        part=source[start:end]
        part,count=re.subn(r'  mov\s+r3, #1600\n  mul\s+r2, r2, r3\n  ldr\s+r3, =line_data\n  add\s+r2, r3, r2[^\n]*\n','',part)
        assert count==1
        body.append(part.replace('NEON_doline_', '.Lbitplane_'))
    wrapper='''/* Derived from pinned UAE4ARM neon_helper.s (GPL-2.0-or-later).
 * Private helpers are leaf-only: no callbacks, allocation or longjmp here. */
.syntax unified
.cpu cortex-a9
.fpu neon
.arm
.text
.align 2
.global zu_bitplane_neon
.hidden zu_bitplane_neon
.type zu_bitplane_neon,%function
zu_bitplane_neon:
 cmp r1,#0
 bxeq lr
 push {r4,lr}
 vmrs r4,fpscr
 vpush {d0-d15}
 vpush {d16-d31}
'''
    for planes in range(2,7):wrapper+=f' cmp r3,#{planes}\n beq .Lcall{planes}\n'
    wrapper+=' b .Lrestore\n'
    for planes in range(2,7):wrapper+=f'.Lcall{planes}:\n bl .Lbitplane_n{planes}\n b .Lrestore\n'
    wrapper+='''.Lrestore:
 vpop {d16-d31}
 vpop {d0-d15}
 vmsr fpscr,r4
 pop {r4,pc}
'''
    target.write_text(wrapper+'\n'.join(body)+'\n.size zu_bitplane_neon,.-zu_bitplane_neon\n.section .note.GNU-stack,"",%progbits\n')

if __name__=='__main__':
    from build_uae4arm import UP,OUT
    generate(UP,OUT/'bitplanes_neon.S')
