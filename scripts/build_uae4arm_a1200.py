#!/usr/bin/env python3
"""Isolated AGA/68020 build using the measured ZZUAE JIT configuration."""
import runpy,sys,shutil
import build_uae4arm as b
base=b.OUT
optimisations=[flag for flag in ('--neon-bitplanes','--neon-half','--chip-reads','--aga-pixel-loop') if flag in sys.argv]
b.OUT=base/'a1200/build'
b.OUT.mkdir(parents=True,exist_ok=True)
for name in ('libgcc.a','mapping.elf','machine.ld'):shutil.copy2(base/name,b.OUT/name)
sys.argv=['build_uae4arm_jit.py','--event-blocks','--cache-kib','32768',
 '--movw-constants','--armv7-emitter','--flat-cycles','--early-draw',
 '--early-pressure','--register-groups','--batch-context','--player','--hardware']+optimisations
runpy.run_path(str(b.ROOT/'scripts/build_uae4arm_jit.py'),run_name='__main__')
