from pathlib import Path
import sys,shutil,json,subprocess,runpy
sys.path.insert(0,'scripts')
import build_uae4arm as b
p=b.OUT/'a1200/gameplay';base=p/'build-pixel4';variant='sprite-plain';out=p/('build-'+variant)
shutil.copytree(base,out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text())
f=out/'src/custom.cpp';s=f.read_text()
helper=Path('.context/amiga/uae4arm/a1200/remaining/sprite_plain.inc').read_text()
entry=Path('.context/amiga/uae4arm/a1200/remaining/sprite-entry.inc').read_text()
a=s.index('static void record_sprite_1 (');s=s[:a]+helper+'\n'+s[a:]
a=s.index('static void record_sprite_1 (');a=s.index('{',a)+1;s=s[:a]+'\n'+entry+s[a:];f.write_text(s)
subprocess.run([*b.RUN,'arm-none-eabi-g++',*c['flags'],'-c',b.inside(f),'-o',b.inside(out/'custom.o')],check=True)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
exec((b.ROOT/'.context/amiga/uae4arm/a1200/performance/extend-chipreads.py').read_text().replace("for variant in ('chipreads',):", "for variant in ('REPLACE_VARIANT',):").replace("REPLACE_VARIANT",variant).replace("a1200/performance/build-", "a1200/gameplay/build-"))
