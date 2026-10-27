#!/usr/bin/env python3
"""Generate, assemble and execute the adapted upstream bitplane routines."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from build_uae4arm import RUN,UP,inside
source=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'scripts/prepare_uae4arm_bitplanes.py'
spec=importlib.util.spec_from_file_location('bitplane_generator',source)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
out=Path(tempfile.mkdtemp(prefix='bitplane-test-',dir=ROOT/'.context/amiga/uae4arm'))
try:
    module.generate(UP,out/'leaf.S')
    subprocess.run([*RUN,'arm-none-eabi-gcc','-mcpu=cortex-a9','-c',inside(out/'leaf.S'),'-o',inside(out/'leaf.o')],check=True)
    subprocess.run(['/opt/homebrew/opt/lld/bin/ld.lld','-Ttext=0x10000','-e','zu_bitplane_neon',out/'leaf.o','-o',out/'leaf.elf'],check=True)
    subprocess.run(['/opt/homebrew/opt/llvm/bin/llvm-objcopy','-O','binary',out/'leaf.elf',out/'leaf.bin'],check=True)
    subprocess.run([ROOT/'.tools/dosbox-model-venv/bin/python',ROOT/'tests/amiga/uae4arm/bitplanes.py',out/'leaf.bin'],check=True)
finally:
    shutil.rmtree(out)
