#!/usr/bin/env python3
"""Build the optional Cyclone 68000 player; never replace the default player.

Uses the normal ZZUAE toolchain/runtime prerequisites. --conservative and
--direct retain evaluation variants; the launcher uses event synchronization.
"""
import argparse
import hashlib
import json
import re
import runpy
import shutil
import subprocess
import sys
import build_uae4arm as b
from prepare_uae4arm_cyclone import big_endian_fetches, movem_address_error
from build_uae4arm_cyclone_probe import REV


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group()
    modes.add_argument('--conservative',action='store_true')
    modes.add_argument('--direct',action='store_true')
    modes.add_argument('--event-sync',action='store_true',help='default')
    args=parser.parse_args()
    normal=b.OUT
    event_sync=not args.conservative
    out=normal/('cyclone-direct' if args.direct else 'cyclone-player' if args.conservative else 'cyclone-events')
    b.OUT=out
    upstream=b.ROOT/'.context/cyclone-review'
    if not upstream.exists():
        subprocess.run(['git','clone','--no-checkout','https://github.com/notaz/cyclone68000',str(upstream)],check=True)
        subprocess.run(['git','-C',str(upstream),'checkout','--detach',REV],check=True)
    if subprocess.check_output(['git','-C',str(upstream),'rev-parse','HEAD'],text=True).strip()!=REV:
        raise RuntimeError('Cyclone checkout differs from the recorded revision')
    gen=out/'generator';gen.mkdir(parents=True,exist_ok=True)
    for p in upstream.iterdir():
        if p.suffix in ('.cpp','.h') or p.name in ('Makefile','Disa'):
            if p.is_dir():shutil.copytree(p,gen/p.name,dirs_exist_ok=True)
            else:shutil.copy2(p,gen/p.name)
    big_endian_fetches(gen)
    movem_address_error(gen)
    config=(gen/'config.h').read_text()
    for name in ('USE_RESET_CALLBACK','EMULATE_ADDRESS_ERRORS_IO','EMULATE_HALT','MEMHANDLERS_NEED_PC'):
        config=re.sub(r'(#define '+name+r'\s+)0',r'\g<1>1',config)
    if args.direct:config+='\n#define MEMHANDLERS_DIRECT_PREFIX "cyclone_"\n'
    (gen/'config.h').write_text(config)
    subprocess.run(['make','-C',str(gen),'HAVE_ARMv6T2=1','CXXFLAGS=-O2 -DHAVE_ARMv6T2=1 -DHAVE_UNALIGNED_ACCESSES=0'],check=True)
    b.EXTRA_FLAGS=['-I'+b.inside(gen)]+(['-DZZ_CYCLONE_EVENT_SYNC'] if event_sync else [])
    b.BUILD_CONFIG={'cyclone_revision':REV,'experimental_core':'Cyclone68000','event_sync':event_sync,
                    'direct_handlers':args.direct,'movem_address_error_fix':True,'allocation_bytes':0x2000000}
    original=b.prepare
    def prepare():
        tree=original();cpu=tree/'newcpu.cpp'
        source=cpu.read_text().replace('zzuae_cpu_reset','zzuae_original_cpu_reset').replace('zzuae_run_batch','zzuae_original_run_batch')
        cpu.write_text(source+'\n'+(b.SRC/'cyclone/dispatch.inc').read_text())
        return tree
    b.prepare=prepare
    sys.argv=['build_uae4arm.py','--profile-stages','--neon-bitplanes','--copper-predict']
    # Compile every required object from this configuration. No borrowing from
    # an older experiment: incremental reuse is governed by source/flag hashes.
    if b.build():raise RuntimeError('UAE core failed')
    subprocess.run([*b.RUN,'arm-none-eabi-gcc','-mcpu=cortex-a9','-marm','-c',b.inside(gen/'Cyclone.s'),'-o',b.inside(out/'Cyclone.o')],check=True)
    subprocess.run(['/opt/homebrew/opt/lld/bin/ld.lld','-r',str(out/'newcpu.o'),str(out/'Cyclone.o'),'-o',str(out/'combined.o')],check=True)
    shutil.copyfile(out/'combined.o',out/'newcpu.o')
    (out/'newcpu.sha256').unlink(missing_ok=True)  # next build must not fold twice
    for name in ('mapping.elf','libgcc.a'):shutil.copyfile(normal/name,out/name)
    b.prepare=lambda:out/'src'
    sys.argv=['build_uae4arm_machine.py','--hardware']
    runpy.run_path(str(b.ROOT/'scripts/build_uae4arm_machine.py'),run_name='__main__')
    player=out/'machine/ZZUAE-Cyclone'
    shutil.copyfile(out/'machine/ZZUAEBoot',player)
    record=json.loads((out/'build-manifest.json').read_text())
    record['artifacts'][player.name]=hashlib.sha256(player.read_bytes()).hexdigest()
    (out/'build-manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    print('Optional player:',player)


if __name__=='__main__':main()
