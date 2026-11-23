from pathlib import Path
import sys,shutil,json,subprocess,runpy
sys.path.insert(0,'scripts')
import build_uae4arm as b
p=b.OUT/'a1200/gameplay';base=p/'build-pixel4';variant='collision-enabled';out=p/('build-'+variant)
shutil.copytree(base,out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text())
f=out/'src/custom.cpp';s=f.read_text()
a=s.index('static void do_sprite_collisions (void)\n{');z=s.index('\nstatic void record_sprite_1',a);part=s[a:z]
needle='        for (l = k; match && l < planes; l += 2) {\n          int t = 0;'
assert part.count(needle)==1
part=part.replace(needle,'        for (l = k; match && l < planes; l += 2) {\n          if (!(clxcon_bpl_enable & (1 << l))) continue;\n          int t = 0;')
s=s[:a]+part+s[z:];f.write_text(s)
subprocess.run([*b.RUN,'arm-none-eabi-g++',*c['flags'],'-c',b.inside(f),'-o',b.inside(out/'custom.o')],check=True)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
exec((b.ROOT/'.context/amiga/uae4arm/a1200/performance/extend-chipreads.py').read_text().replace("for variant in ('chipreads',):", "for variant in ('REPLACE_VARIANT',):").replace("REPLACE_VARIANT",variant).replace("a1200/performance/build-", "a1200/gameplay/build-"))
