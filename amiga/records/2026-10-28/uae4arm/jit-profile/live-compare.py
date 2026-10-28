from pathlib import Path
import subprocess,re
root=Path.cwd();lab=root/'.context/amiga/uae4arm/jit-profile'
python=str(root/'.tools/amiga-venv/bin/python');runner=str(root/'.context/amiga/uae4arm/next-pass/hardware.py')
for n,(label,player)in enumerate([('reference','event32armv7'),('flat','jitflat')]):
 name='profile-alien-audio3000-'+label
 cmd=f'RAM:ZZUAE054/{player}/ZZUAEBoot c4de030{n} RUN ZZUAE:Disks/AlienSyndrome.adf 3000 LIVE WRITE LMB ROM ZZUAE:ROMs/Kick12.rom MODEL A1000 RAM EXPANDED FPS 30 ENGINE JIT AUDIO AHI'
 print('RUN',name,flush=True)
 with (lab/(name+'-runner.log')).open('w')as output:subprocess.run([python,runner,name,cmd],stdout=output,stderr=subprocess.STDOUT,check=True)
 log=(root/'.context/amiga/uae4arm/next-pass'/(name+'.log')).read_text()
 assert 'rendered_frames=3000' in log
 assert int(re.search(r'AUDIO_PCM nonzero_frames=(\d+)',log)[1])>0,'audio fixture was silent'
 state=re.search(r'cycles=(\d+) hash=(\w+) pc=(\w+) frames=(\d+)',log).groups()
 if n==0:reference=state
 else:assert state==reference,(state,reference)
 print(name,'PASS active PCM and complete run',state,flush=True)
