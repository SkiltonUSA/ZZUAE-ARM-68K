from pathlib import Path
import sys,shutil,json,subprocess,runpy,difflib
sys.path.insert(0,'scripts')
import build_uae4arm as b

p=b.OUT/'a1200/sprite-neon';g=p.parent/'gameplay';variant='sprite-neon';out=g/('build-'+variant)
shutil.copytree(g/'build-pixel4',out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text())
f=out/'src/custom.cpp';original=f.read_text();s=original
declarations='''
extern "C" unsigned zu_neon_available(void);
extern "C" void zu_sprite_or16(uae_u16*,uae_u32,unsigned,unsigned);
static bool zu_sprite_neon_ready;
unsigned zu_sprite_neon_spans;
'''
a=s.index('static void record_sprite_1 (');s=s[:a]+declarations+s[a:]
a=s.index('static void record_sprite_1 (');a=s.index('{',a)+1
s=s[:a]+'\n'+(p/'entry.inc').read_text()+s[a:]
marker='static void init_hardware_frame (void)\n{';assert s.count(marker)==1
s=s.replace(marker,marker+'\n zu_sprite_neon_ready=zu_neon_available()!=0;')
f.write_text(s)
(p/'candidate.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='reference/custom.cpp',tofile='candidate/custom.cpp')))
f=b.SRC/'convert_neon.S';f.write_text(f.read_text()+'\n'+(p/'kernel.S').read_text())
f=b.SRC/'machine_probe.cpp';s=f.read_text();needle='    zu_profile_finish();return cancelled?2:0;';assert s.count(needle)==1
s=s.replace(needle,'    extern unsigned zu_sprite_neon_spans;\n    if(uae_shared)ad_put(uae_shared,0x482908u,zu_sprite_neon_spans);\n'+needle)
f.write_text(s)
subprocess.run([*b.RUN,'arm-none-eabi-g++',*c['flags'],'-c',b.inside(out/'src/custom.cpp'),'-o',b.inside(out/'custom.o')],check=True)
f=Path('scripts/build_uae4arm_machine.py');s=f.read_text()
needle="'zu_convert_neon320','zu_bitplane_neon'}";assert s.count(needle)==1
s=s.replace(needle,"'zu_convert_neon320','zu_bitplane_neon','zu_sprite_or16'}")
sys.argv=[str(f),'--guest-jit','--hardware'];exec(compile(s,str(f),'exec'),{'__name__':'__main__'})
sys.argv=['lock-input.py',variant];runpy.run_path(str(p.parent/'sprite-decisions/lock-input.py'),run_name='__main__')
