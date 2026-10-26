#!/usr/bin/env python3
"""Export the ZZUAE source backup. No ROMs, disks, credentials or preferences."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.context/ZZUAE-ARM-68K'
SUFFIXES = {'.c', '.cpp', '.h', '.S', '.ld', '.py', '.json', '.md', '.inc'}

def copy(rel):
    src = ROOT / rel
    dst = OUT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for folder in ['amiga/uae4arm', 'tests/amiga/uae4arm']:
        for p in (ROOT / folder).rglob('*'):
            if p.is_file() and p.suffix in SUFFIXES:
                copy(p.relative_to(ROOT))
    for p in (ROOT / 'scripts').glob('*uae4arm*.py'):
        copy(p.relative_to(ROOT))
    for rel in ['scripts/build_zz9000_debug.py', 'scripts/build_pocketsnes_libc.py',
                'amiga/upstream.json', 'amiga/common/rtg_mapping.h',
                'amiga/ffmpeg_bench/heap.c', 'amiga/mesen_snes/system/memory.c',
                'amiga/pocketsnes/payload.ld', 'amiga/pocketsnes/libc_config.h',
                'amiga/pocketsnes/libc-sources.json', 'amiga/arm_debug/relay.h',
                'amiga/arm_debug/protocol.h', 'amiga/arm_debug/zz9000/launcher.c',
                'amiga/arm_debug/zz9000/layout.h', 'amiga/arm_debug/zz9000/mapping_probe.S']:
        copy(rel)
    for name in ['worker.cpp', 'host.c', 'mmu.c', 'mmu.h', 'mmu_asm.S',
                 'mmu_plan.h', 'wire.h', 'bench.h', 'runtime.c', 'mmu_payload.ld']:
        copy('amiga/mesen_bench/' + name)
    for p in (ROOT / 'docs').glob('amiga-uae4arm-*.md'):
        copy(p.relative_to(ROOT))
    # Build scripts need only the pinned compiler image from the larger workspace helper.
    (OUT / 'scripts/amiga.py').write_text(
        '"""Compiler pin adapter for the standalone ZZUAE source backup."""\n'
        'import json\nfrom pathlib import Path\n'
        'PIN = json.loads((Path(__file__).resolve().parents[1] / "amiga/upstream.json").read_text())\n')
    (OUT / '.gitignore').write_text('.context/\n.tools/\n__pycache__/\n*.pyc\n*.su\n*.rom\n*.adf\n*.cfg\n.DS_Store\n')
    (OUT / 'docs').mkdir(exist_ok=True)
    hashes = {str(p.relative_to(OUT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for base in ['amiga', 'scripts', 'tests'] for p in (OUT / base).rglob('*')
              if p.is_file() and '__pycache__' not in p.parts}
    (OUT / 'docs/source-sha256.json').write_text(json.dumps(hashes, indent=2) + '\n')
    print(f'Exported {len(hashes)} source/build files to {OUT}')

if __name__ == '__main__':
    main()
