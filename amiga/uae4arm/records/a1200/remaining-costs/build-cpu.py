from pathlib import Path
import sys,shutil,json,subprocess,runpy
sys.path.insert(0,'scripts')
import build_uae4arm as b
from prepare_uae4arm_jit_service import service_profile
p=b.OUT/'a1200/gameplay';base=p/'build-pixel4';out=p/'build-cpu-audio-profile'
shutil.copytree(base,out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text());c['flags']=['-I'+b.inside(b.SRC)]+c['flags']+['-DZZUAE_JIT_PROFILE','-DZZUAE_PROFILE'];(out/'compile.json').write_text(json.dumps(c))
f=b.SRC/'jit_profile.h';s=f.read_text().replace('struct ZuJitProfile {','extern unsigned long timeframes;\nstruct ZuJitProfile {').replace('  ++dispatches;rng', '  if(timeframes<3000)return false;\n  ++dispatches;rng');f.write_text(s)
f=b.SRC/'profile.h';s=f.read_text().replace('struct ZuProfileScope {','extern unsigned long timeframes;\nstruct ZuProfileScope {').replace('unsigned stage; uint32_t start;', 'unsigned stage; uint32_t start; bool active;').replace('stage(s),start(zu_profile_now()){}','stage(s),start(timeframes>=3000?zu_profile_now():0),active(timeframes>=3000){}').replace('~ZuProfileScope(){zu_profile_ticks','~ZuProfileScope(){if(!active)return;zu_profile_ticks');f.write_text(s)
f=out/'src/newcpu.cpp';s=f.read_text();s=service_profile(s,(b.SRC/'jit_service.inc').read_text())
needle='    cpu_cycles=adjust_cycles(cpufunctbl[regs.opcode](regs.opcode));\n    do_cycles(cpu_cycles);\n    ZJ_MARK(ZJ_INTERPRETER);'
assert s.count(needle)==1
s=s.replace(needle,'''    cpu_cycles=adjust_cycles(cpufunctbl[regs.opcode](regs.opcode));
    ZJ_MARK(ZJ_INTERPRETER);
    do_cycles(cpu_cycles);
    ZJ_MARK(ZJ_HANDLER);''')
f.write_text(s)
for unit in ['newcpu','drawing','audio']:
 subprocess.run([*b.RUN,'arm-none-eabi-g++',*c['flags'],'-c',b.inside(out/'src'/(unit+'.cpp')),'-o',b.inside(out/(unit+'.o'))],check=True)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
# Keep the matched test player's extended deadline, without changing production.
hw=out/'machine';f=hw/'host.c';s=f.read_text().replace('zu_run_timeout(frame_limit,audio_mode?20000:frame_period)','(frame_limit?300000000u:0u)');f.write_text(s)
exec((b.ROOT/'.context/amiga/uae4arm/a1200/performance/extend-chipreads.py').read_text().replace("for variant in ('chipreads',):", "for variant in ('cpu-audio-profile',):").replace("a1200/performance/build-", "a1200/gameplay/build-"))
