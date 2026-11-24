#!/usr/bin/env python3
"""Build a diagnostic-only host around a recorded FPU payload; never boot a guest."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'docker.io/amigadev/crosstools@sha256:93ca1a47903b61873f6638881b44f9f2d6086a39f1b9b916a26faff3a8ea4d3d'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe_host(text):
    gate = 'if(rate<320000000u || rate>345000000u)goto done;'
    assert text.count(gate) == 1, 'Expected recorded stock-clock host'
    assert 'GUEST_FPU VERIFY PASS' in text, 'FPU self-test host required'
    text = text.replace(gate, '''/* MB_VERIFY executes bounded, unpaced arithmetic only. This does not
     * enable game/audio timing at another clock rate. */
    if(!((rate>=320000000u && rate<=345000000u) ||
         (rate>=396000000u && rate<=404000000u)))goto done;''')
    check = 'syncio->pull(shared+UAE_OPTIONS+72,24,NULL);'
    assert text.count(check) == 1
    text = text.replace(check, check + '\n    if(ad_get(shared,UAE_OPTIONS+80)){puts("FPU host-state restoration failed");goto done;}')
    return '#ifdef UAE_BOOT\n#error This host is for MB_VERIFY only\n#endif\n' + text


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('recorded', type=Path, help='Recorded machine directory with host.c, zz_payload.h and mmu.h')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--connection', default='nuflix-converter-root')
    a = p.parse_args()
    source, out = a.recorded.resolve(), a.output.resolve()
    assert out != source and source not in out.parents, 'Keep recorded build separate'
    out.mkdir(parents=True, exist_ok=True)
    inputs = {n: digest(source/n) for n in ['host.c', 'zz_payload.h', 'mmu.h', 'mmu_plan.h']}
    (out/'host.c').write_text(probe_host((source/'host.c').read_text()))
    for n in ['zz_payload.h', 'mmu.h', 'mmu_plan.h']:
        shutil.copy2(source/n, out/n)
    flags = ['-DZZ_BLOCK_SIZE=75497472', '-DZZ_CONTROL=0x480000',
             '-DMB_ALLOCATION=75497472u', '-DMB_MMU', '-DMB_DCACHE',
             '-DZZ_HEADLESS_BENCH', '-DFF_DIRECT', '-DZZ_RELEASE',
             '-DZZ_HEADLESS_MMU', '-DZZ_HEADLESS_ICACHE',
             '-DZZ_APP_NAME="ZZUAE-FPU-Verify"', '-DZZ_APP_VERSION="diagnostic"',
             '-DZZ_MIN_STACK=131072', '-Dmain=zzuae_main']
    includes = ['-I/out', '-Iamiga/uae4arm', '-Iamiga/uae4arm/support/core1',
                '-Iamiga/arm_debug', '-Iamiga/arm_debug/zz9000']
    cmd = ['podman', '--connection', a.connection, 'run', '--rm', '--platform',
           'linux/amd64', '-v', str(ROOT)+':/work:ro', '-v', str(out)+':/out',
           '-w', '/work', IMAGE, 'm68k-amigaos-gcc', '-std=c99', '-noixemul',
           '-m68020', '-O2', '-Wall', '-Wextra', '-Werror', *flags, *includes,
           'amiga/arm_debug/zz9000/launcher.c', '/out/host.c', '-lamiga',
           '-o', '/out/FPUVerify']
    subprocess.run(cmd, check=True)
    assert digest(out/'zz_payload.h') == inputs['zz_payload.h']
    (out/'build.json').write_text(json.dumps({
        'scope': 'MB_VERIFY only; no guest boot, audio or gameplay clock support',
        'inputs': inputs, 'host': digest(out/'host.c'),
        'executable': digest(out/'FPUVerify'), 'image': IMAGE,
        'launcher': digest(ROOT/'amiga/arm_debug/zz9000/launcher.c')}, indent=2)+'\n')


if __name__ == '__main__':
    main()
