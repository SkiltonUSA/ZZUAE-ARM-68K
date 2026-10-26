#!/usr/bin/env python3
"""Validate supplied Kickstart/Workbench media into a private diagnostic drawer."""
import argparse,hashlib,json,struct,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def checksum(data):
 total=0
 for word in struct.unpack('>'+str(len(data)//4)+'I',data):
  total+=word;total=(total&0xffffffff)+(total>>32)
 return total

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--kick-disk',type=Path,required=True)
 p.add_argument('--workbench',type=Path,required=True)
 p.add_argument('--desktop-startup',action='store_true',help='Create a separate private copy with LoadWB/EndCLI startup (requires amitools)')
 a=p.parse_args();kick=a.kick_disk.read_bytes();disk=a.workbench.read_bytes()
 if len(kick)!=901120 or kick[:4]!=b'KICK':raise ValueError('Expected a raw A1000 KICK disk')
 rom=kick[512:512+262144]
 if checksum(rom)!=0xffffffff:raise ValueError('Kickstart ROM checksum failed')
 if len(disk)!=901120 or disk[:3]!=b'DOS':raise ValueError('Expected a raw 880 KiB Workbench disk')
 if checksum(disk[:1024])!=0xffffffff:raise ValueError('Workbench boot-block checksum failed')
 out=ROOT/'.context/amiga/uae4arm/media';out.mkdir(parents=True,exist_ok=True)
 (out/'kick12.rom').write_bytes(rom);(out/'wb12.adf').write_bytes(disk)
 record={'kickstart':{'source':str(a.kick_disk),'rom_sha256':hashlib.sha256(rom).hexdigest(),'version':list(struct.unpack_from('>HH',rom,12))},'workbench':{'source':str(a.workbench),'sha256':hashlib.sha256(disk).hexdigest()},'scope':'Private supplied media, not distribution assets'}
 if a.desktop_startup:
  copy=out/'wb12-desktop.adf';copy.write_bytes(disk)
  env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'.tools/amifuse/amitools')+os.pathsep+env.get('PYTHONPATH','')
  subprocess.run([sys.executable,'-m','amitools.tools.xdftool',str(copy),
    'delete','s/startup-sequence','+','write',str(ROOT/'amiga/uae4arm/Startup-Sequence'),'s/startup-sequence'],env=env,check=True)
  assert checksum(copy.read_bytes()[:1024])==0xffffffff
  record['desktop_copy']={'sha256':hashlib.sha256(copy.read_bytes()).hexdigest(),'change':'Only s/startup-sequence replaced by LoadWB and EndCLI; original attachment unchanged'}
 (out/'selected.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
if __name__=='__main__':main()
