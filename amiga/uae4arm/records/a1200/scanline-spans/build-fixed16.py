from pathlib import Path
import sys,shutil,json,subprocess,runpy
sys.path.insert(0,'scripts')
import build_uae4arm as b
p=b.OUT/'a1200/gameplay';base=p/'build-pixel4';out=p/'build-fixed16'
shutil.copytree(base,out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text())
f=out/'src/custom.cpp';s=f.read_text()
old='static void toscr_2_2 (int nbits) { toscr_3_aga (nbits, 2); }'
new='static void toscr_2_2 (int nbits) {\n    // Specialise the common full span; keep every partial span unchanged.\n    if (nbits == 16) toscr_3_aga (16, 2);\n    else toscr_3_aga (nbits, 2);\n}'
assert s.count(old)==1
f.write_text(s.replace(old,new))
subprocess.run([*b.RUN,'arm-none-eabi-g++',*c['flags'],'-c',b.inside(f),'-o',b.inside(out/'custom.o')],check=True)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
exec((b.ROOT/'.context/amiga/uae4arm/a1200/performance/extend-chipreads.py').read_text().replace("for variant in ('chipreads',):", "for variant in ('fixed16',):").replace("a1200/performance/build-", "a1200/gameplay/build-"))
