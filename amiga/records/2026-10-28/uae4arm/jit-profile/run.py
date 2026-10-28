from pathlib import Path
import subprocess,sys,re
root=Path.cwd();lab=Path(__file__).resolve().parent
mode=sys.argv[1];player={'baseline':'event32armv7','profile':'jitprofile','candidate':'jitlists','flat':'jitflat'}[mode]
workloads=[('frontier','FrontierEliteII-1','Kick13','A500','EXPANDED',3000,''),('alien','AlienSyndrome','Kick12','A1000','EXPANDED',1800,' LMB'),('wb20','Workbench20','Kick205','A600','BASE',1800,'')]
repeat=int(sys.argv[2]) if len(sys.argv)>2 else 0
skip=int(sys.argv[3]) if len(sys.argv)>3 else 0
nonce={'baseline':1,'profile':17,'candidate':33,'flat':193}[mode]+repeat*64+skip
for name,disk,rom,model,ram,frames,extra in workloads[skip:]:
 label='profile-'+name+'-'+mode+('-r'+str(repeat) if repeat else '')
 command=f'RAM:ZZUAE054/{player}/ZZUAEBoot c4de{nonce:04x} RUN ZZUAE:Disks/{disk}.adf {frames} WRITE{extra} ROM ZZUAE:ROMs/{rom}.rom MODEL {model} RAM {ram} FPS MAX ENGINE JIT'
 print('RUN',label,flush=True)
 with (lab/(label+'-runner.log')).open('w')as log:
  subprocess.run([str(root/'.tools/amiga-venv/bin/python'),str(lab.parent/'next-pass/hardware.py'),label,command],check=True,stdout=log,stderr=subprocess.STDOUT)
 text=(lab.parent/'next-pass'/(label+'.log')).read_text();ref=(lab.parent/'next-pass'/f'events-{name}-a1.log').read_text()
 pattern=r'cycles=(\d+) hash=(\w+) pc=(\w+) frames=(\d+)'
 assert re.search(pattern,text).groups()==re.search(pattern,ref).groups()
 assert re.search(r'UAE_MACHINE dispatches=(\d+)',text)[1]==re.search(r'UAE_MACHINE dispatches=(\d+)',(lab.parent/'next-pass'/('profile-'+name+'-baseline.log')).read_text())[1]
 print('PASS',label,re.search(r'BOOT elapsed_us=(\d+)',text)[1],'state matches',flush=True)
 if mode=='profile':assert 'JIT_PROFILE dispatches=' in text
 nonce+=1
