from pathlib import Path
import sys,shutil,runpy
sys.path.insert(0,'scripts')
import build_uae4arm as b
p=b.OUT/'a1200/gameplay';kind=sys.argv[1];assert kind in ('reference','candidate')
variant='sprite-table-'+kind;out=p/('build-'+variant);base=p/('build-pixel4' if kind=='reference' else 'build-sprite-plain')
shutil.copytree(base,out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
f=b.SRC/'machine_probe.cpp';s=f.read_text();assert 'if(uae_frame_limit>6000)' in s;s=s.replace('if(uae_frame_limit>6000)','if(uae_frame_limit>9000)').replace('?200000000u:20000000u','?400000000u:20000000u');f.write_text(s)
f=b.SRC/'machine_platform.cpp';s=f.read_text();assert 'clicks[]={1800,2800}' in s;s=s.replace('clicks[]={1800,2800}','clicks[]={1800,2800,3800,6200}')
s=s.replace('if(timeframes==3600 || timeframes==3610)','if(timeframes==3600 || timeframes==3610 || timeframes==5200 || timeframes==5210 || timeframes==6600 || timeframes==6610)').replace('(timeframes==3600?0:128)','((timeframes==3600 || timeframes==5200 || timeframes==6600)?0:128)')
s=s.replace('if(timeframes==4400 || timeframes==4410)','if(timeframes==4400 || timeframes==4410 || timeframes==7000 || timeframes==7010)').replace('(timeframes==4400?0:128)','((timeframes==4400 || timeframes==7000)?0:128)');f.write_text(s)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
f=out/'machine/host.c';s=f.read_text().replace('frame_limit>6000','frame_limit>9000');f.write_text(s)
s=(b.ROOT/'.context/amiga/uae4arm/a1200/performance/extend-chipreads.py').read_text().replace("for variant in ('chipreads',):",f"for variant in ('{variant}',):").replace('a1200/performance/build-','a1200/gameplay/build-').replace('300000000u','450000000u')
exec(s)
