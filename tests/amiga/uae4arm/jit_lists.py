#!/usr/bin/env python3
"""Check actual upstream cache-list promotion against an independent list model."""
import argparse,subprocess,tempfile,sys
from pathlib import Path
root=Path(__file__).absolute().parents[3];sys.path.insert(0,str(root/'scripts'))
from prepare_uae4arm_jit_lists import fast_promotion
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);args=p.parse_args()
source=args.source.read_text()
for name,text in [('upstream',source),('fast',fast_promotion(source))]:
 start=text.index('STATIC_INLINE void remove_from_cl_list(');end=text.index('STATIC_INLINE void remove_dep(',start)
 with tempfile.TemporaryDirectory()as folder:
  folder=Path(folder);(folder/'jit_lists_generated.inc').write_text(text[start:end]);binary=folder/'test'
  subprocess.run(['clang++','-std=c++11','-fsanitize=undefined','-I'+str(folder),str(root/'tests/amiga/uae4arm/jit_lists.cpp'),'-o',str(binary)],check=True)
  subprocess.run([str(binary)],check=True)
 print('PASS',name,'10000 promotions: collisions, links and handler updates')
