from pathlib import Path
import sys,shutil,json,subprocess,runpy
sys.path.insert(0,'scripts')
import build_uae4arm as b
p=b.OUT/'a1200/gameplay';base=p/'build-pixel4';variant=sys.argv[1] if len(sys.argv)>1 else 'idle-batch';out=p/('build-'+variant)
shutil.copytree(base,out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text())
f=out/'src/custom.cpp';s=f.read_text()
helper=Path('.context/amiga/uae4arm/a1200/idle-fetch/idle_span.inc').read_text()
marker='STATIC_INLINE void update_fetch (int until, int fm)'
assert s.count(marker)==1
if variant=='idle-count':
 helper='static unsigned zz_idle_counts[28];\n'+helper
 helper+='\nextern "C" void zz_idle_report(volatile unsigned char *p) {\n ad_put(p,0x482980u,ZJ_PROFILE_MAGIC);\n for(unsigned i=0;i<28;i++)ad_put(p,0x482990u+4*i,zz_idle_counts[i]);\n}\n'
 helper='#include "jit_profile.h"\n'+helper
s=s.replace(marker,helper+'\n'+marker)
a=s.index(marker);z=s.index('static void update_fetch_0',a);u=s[a:z]
needle='\tfor (; pos < until; pos++) {'
assert u.count(needle)==1
if variant=='idle-count':
 code='\n        if(timeframes>=3000){\n            int n=zz_idle_span(pos,until,ddfstop_to_test,dma,fm);\n            ++zz_idle_counts[0];\n            if(n){++zz_idle_counts[1];zz_idle_counts[2]+=n;++zz_idle_counts[3+n];}\n        }\n'
else:
 code='\n        int idle = zz_idle_span(pos, until, ddfstop_to_test, dma, fm);\n        if (idle) {\n            fetch_cycle += idle;\n            toscr_nbits += idle * toscr_res2p;\n            if (toscr_nbits == 16) flush_display(fm);\n            pos += idle - 1;\n            continue;\n        }\n'
u=u.replace(needle,needle+code);s=s[:a]+u+s[z:];f.write_text(s)
if variant=='idle-count':
 q=b.SRC/'machine_probe.cpp';v=q.read_text();v='extern "C" void zz_idle_report(volatile unsigned char*);\n'+v
 v=v.replace('zu_profile_finish();','zz_idle_report(uae_shared);zu_profile_finish();');assert 'zz_idle_report(uae_shared)' in v;q.write_text(v)
subprocess.run([*b.RUN,'arm-none-eabi-g++',*c['flags'],'-c',b.inside(f),'-o',b.inside(out/'custom.o')],check=True)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
if variant=='idle-count':
 q=out/'machine/host.c';v=q.read_text();a=v.index('      for(unsigned i=0;i<ZJ_STAGES;i++)printf(');z=v.index('\n',a);v=v[:a]+'      for(unsigned i=0;i<28;i++)printf("IDLE_COUNT id=%u value=%u\\n",i,ad_get(shared,ZJ_PROFILE_BASE+16+4*i));'+v[z:];q.write_text(v)
exec((b.ROOT/'.context/amiga/uae4arm/a1200/performance/extend-chipreads.py').read_text().replace("for variant in ('chipreads',):", "for variant in ('REPLACE_VARIANT',):").replace("REPLACE_VARIANT",variant).replace("a1200/performance/build-", "a1200/gameplay/build-"))
