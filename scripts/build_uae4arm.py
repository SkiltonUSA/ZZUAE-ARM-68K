#!/usr/bin/env python3
"""Prepare and compile an isolated UAE4ARM Cortex-A9 port; never deploys."""
import hashlib,json,re,shutil,subprocess,sys
from prepare_uae4arm_disk_activity import disk_activity
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/'.context/uae4arm-review';OUT=ROOT/'.context/amiga/uae4arm';SRC=ROOT/'amiga/uae4arm'
PIN='fc1cb90afd6b5c6d9bb933d111c4c99c90f37688'
EXTRA_FLAGS=[]
BUILD_CONFIG={}
RUN=['podman','--connection','nuflix-converter-root','exec','zzffmpeg-toolchain']
def inside(p):return '/work/'+str(p.relative_to(ROOT))
def prepare():
 if not UP.exists():
  subprocess.run(['git','clone','--no-checkout','https://github.com/Chips-fr/uae4arm-rpi',str(UP)],check=True)
  subprocess.run(['git','checkout','--detach',PIN],cwd=UP,check=True)
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=UP,text=True).strip()==PIN
 OUT.mkdir(parents=True,exist_ok=True)
 if not (OUT/'src').exists():shutil.copytree(UP/'src',OUT/'src')
 (OUT/'include').mkdir(exist_ok=True)
 config=(UP/'src/od-pandora/sysconfig.h').read_text()
 config='#ifndef PATH_MAX\n#define PATH_MAX 1024\n#endif\n#define REGPARAM\n'+config
 disabled=['SUPPORT_THREADS','FILESYS','UAE_FILESYS_THREADS','JIT','USE_JIT_FPU','CD32','CDTV','SCSIEMU','CPUEMU_40','ACTION_REPLAY','BSDSOCKET','CAPS','FDI2RAW','SAVESTATE','A_ZIP','A_7Z','A_LHA','A_LZX','A_DMS','A_WRP','HAVE_GETMNTENT','MOUNTED_GETMNTENT1']
 for name in disabled:config=re.sub(r'^#define '+name+r'\b[^\n]*','/* disabled in initial ZZUAE OCS profile */',config,flags=re.M)
 config=config.replace('#define CPUEMU_0', '#define CPUEMU_68000_ONLY\n#define CPUEMU_0')
 (OUT/'include/sysconfig.h').write_text(config)
 deps=(UP/'src/include/sysdeps.h').read_text().replace('typedef unsigned int uae_u32;','typedef uint32_t uae_u32;').replace('typedef int uae_s32;','typedef int32_t uae_s32;')
 (OUT/'src/include/sysdeps.h').write_text(deps)
 shutil.copyfile(SRC/'td-sdl/thread.h',OUT/'src/td-sdl/thread.h')
 shutil.copyfile(SRC/'md-pandora/rpt.h',OUT/'src/md-pandora/rpt.h')
 shutil.copyfile(SRC/'exception.h',OUT/'src/include/mmu_common.h')
 # Optional upstream backends have a few unguarded references.
 disk=(UP/'src/disk.cpp').read_text()
 start=disk.index('  retrytrack = drv->lastdataacesstrack')
 end=disk.index('\n\n',start)
 disk=disk[:start]+'#ifdef CAPS\n'+disk[start:end]+'\n#endif'+disk[end:]
 (OUT/'src/disk.cpp').write_text(disk_activity(disk))
 cfg=(UP/'src/cfgfile.cpp').read_text()
 # The toolchain's uint32_t is unsigned long; upstream's overload uses unsigned int.
 marker='int cfgfile_intval (const TCHAR *option, const TCHAR *value, const TCHAR *name, int *location, int scale)'
 overload='static int cfgfile_intval(const TCHAR *o,const TCHAR *v,const TCHAR *n,uae_u32 *p,int scale) { unsigned int x=0; int r=cfgfile_intval(o,v,n,&x,scale); if(r)*p=x; return r; }\n'
 cfg=cfg.replace(marker,overload+marker)
 (OUT/'src/cfgfile.cpp').write_text('#define __LIBRETRO__ 1\n'+cfg)
 dev=(UP/'src/devices.cpp').read_text()
 for call in ['CDTV_hsync_handler();','rethink_cdtv();','cdtv_free();','cd32_fmv_set_sync(svpos, syncadjust);']:
  feature='CD32' if call.startswith('cd32') else 'CDTV'
  dev=dev.replace(call,'\n#ifdef '+feature+'\n'+call+'\n#endif\n')
 (OUT/'src/devices.cpp').write_text(dev)
 exp=(UP/'src/expansion.cpp').read_text()
 start=exp.index('\tif (do_mount < 0 && ks11orolder())')
 end=exp.index('\n\t}',start)+3
 exp=exp[:start]+'#ifdef FILESYS\n'+exp[start:end]+'\n#endif'+exp[end:]
 for label,feature in [('cd32fmv','CD32'),('cdtvdmac','CDTV'),('cdtvsram','CDTV')]:
  pos=exp.index('_T("'+label+'")');start=exp.rfind('\n\t{',0,pos);end=exp.index('\n\t},',pos)+4
  exp=exp[:start]+'\n#ifdef '+feature+exp[start:end]+'\n#endif'+exp[end:]
 (OUT/'src/expansion.cpp').write_text(exp)
 cpu=(UP/'src/newcpu.cpp').read_text()
 start=cpu.index('static const struct cputbl *cputbls[5][3]')
 end=cpu.index('\n};',start)+3
 cpu=cpu[:start]+'''static const struct cputbl *cputbls[5][3] = {
 {NULL,NULL,op_smalltbl_12_ff}, {NULL,NULL,NULL}, {NULL,NULL,NULL},
 {NULL,NULL,NULL}, {NULL,NULL,NULL}
};'''+cpu[end:]
 start=cpu.index('  /* hack fpu to 68000/68010 mode */')
 end=cpu.index('  for (opcode = 0; opcode < 65536; opcode++)',start)
 cpu=cpu[:start]+'  /* 68000 prototype: no FPU opcode injection. */\n'+cpu[end:]
 cpu=cpu.replace('  fpu_reset ();','  /* No guest FPU in the 68000 profile. */').replace('\tfpu_reset ();','\t/* No guest FPU in the 68000 profile. */')
 cpu += """
extern "C" void zzuae_cpu_reset(void) { m68k_reset(false); }

"""
 cpu += (SRC/'cpu_batch.inc').read_text()
 (OUT/'src/newcpu.cpp').write_text(cpu)
 inp=(UP/'src/inputdevice.cpp').read_text()+'''
// Bounded diagnostic input, using the core's normal guest event handling.
extern "C" void zzuae_test_button(unsigned kind,int down) {
 if(kind==1)handle_input_event(INPUTEVENT_JOY1_FIRE_BUTTON,down,1,0);
 if(kind==2)handle_input_event(INPUTEVENT_JOY2_FIRE_BUTTON,down,1,0);
 if(kind==3)inputdevice_do_keyboard(0x40,down); // Amiga Space key
}
'''
 inp += r'''
#include "live.h"
// Guest timing from inputdevice_vsync, without desktop input reconfiguration.
// Host events already arrive through zzuae_live_event; hsync polls the core.
extern "C" void zzuae_input_vsync(void) {
 input_frame++;
 mouseupdate(0,true);
}
extern "C" void zzuae_live_event(unsigned kind,int value) {
 static unsigned char keys[128];
 static const int joy[]={INPUTEVENT_JOY2_RIGHT,INPUTEVENT_JOY2_LEFT,
  INPUTEVENT_JOY2_UP,INPUTEVENT_JOY2_DOWN,INPUTEVENT_JOY2_FIRE_BUTTON,
  INPUTEVENT_JOY2_2ND_BUTTON,INPUTEVENT_JOY2_3RD_BUTTON};
 if(kind==UL_KEY) {
  unsigned key=value&127;int down=!(value&128);
  if(keys[key]!=down){keys[key]=down;inputdevice_do_keyboard(key,down);}
 } else if(kind==UL_MOUSE_X || kind==UL_MOUSE_Y) {
  mouse_port[0]=1;
  handle_input_event(kind==UL_MOUSE_X?INPUTEVENT_MOUSE1_HORIZ:INPUTEVENT_MOUSE1_VERT,value,0,0);
 } else if(kind==UL_LEFT || kind==UL_RIGHT) {
  handle_input_event(kind==UL_LEFT?INPUTEVENT_JOY1_FIRE_BUTTON:INPUTEVENT_JOY1_2ND_BUTTON,value,1,0);
 } else if(kind==UL_JOY && (value&127)<7) {
  handle_input_event(joy[value&127],!(value&128),1,0);
 } else if(kind==UL_RESET_INPUT) {
  for(unsigned i=0;i<128;i++)if(keys[i]){inputdevice_do_keyboard(i,0);keys[i]=0;}
  for(unsigned i=0;i<7;i++)handle_input_event(joy[i],0,1,0);
  handle_input_event(INPUTEVENT_JOY1_FIRE_BUTTON,0,1,0);
  handle_input_event(INPUTEVENT_JOY1_2ND_BUTTON,0,1,0);
 }
}
'''
 (OUT/'src/inputdevice.cpp').write_text(inp)
 draw=(UP/'src/drawing.cpp').read_text()
 start=draw.index('  if(render_pipe == 0) {', draw.index('void drawing_init'))
 end=draw.index('\n#ifdef PICASSO96',start)
 draw=draw[:start]+'  /* XACP Core1 renders synchronously; no Linux render thread. */\n'+draw[end:]
 draw=draw.replace('''    if(render_tid) {
      write_comm_pipe_u32 (render_pipe, RENDER_SIGNAL_FRAME_DONE, 1);
      uae_sem_wait (&render_sem);
    }''','    finish_drawing_frame();')
 draw=draw.replace('if(render_tid && linestate_first_undecided > 3 )','if(linestate_first_undecided > 3 )')
 draw=draw.replace('write_comm_pipe_u32(render_pipe, RENDER_SIGNAL_PARTIAL, 1);','partial_draw_frame();').replace('write_comm_pipe_u32 (render_pipe, RENDER_SIGNAL_PARTIAL, 1);','partial_draw_frame();')
 # Diagnostic stage scopes do not change the core when profiling is disabled.
 for signature,stage in [('static void partial_draw_frame(void)',0),('static void finish_drawing_frame (void)',0),('static void pfield_doline (int lineno)',1)]:
  pos=draw.index(signature);brace=draw.index('{',pos)
  draw=draw[:brace+1]+f'\n ZU_PROFILE({stage});'+draw[brace+1:]
 draw=draw.replace('static void init_drawing_frame (void)\n{','static void init_drawing_frame (void)\n{\n#ifdef ZZUAE_NEON_BITPLANES\n zu_bitplanes_ready=zu_neon_available();\n#endif')
 needle='  uae_u32 *data = pixdata.apixels_l + MAX_PIXELS_PER_LINE / sizeof(uae_u32);'
 draw=draw.replace(needle,needle+'\n#ifdef ZZUAE_NEON_BITPLANES\n  if(zu_bitplanes_ready && bplplanecnt>=2 && bplplanecnt<=6 && wordcount>0 && wordcount<=50){\n    zu_bitplane_neon(data,wordcount,DATA_POINTER(0),bplplanecnt);\n    ++zu_bitplanes_neon_rows;return;\n  }\n  ++zu_bitplanes_scalar_rows;\n#endif\n')
 draw=(SRC/'bitplanes.inc').read_text()+draw
 draw=draw.replace('static void init_drawing_frame (void)\n{','static void init_drawing_frame (void)\n{\n#ifdef ZZUAE_EARLY_DRAW\n zu_draw_decided=false;\n#endif')
 for signature in ['static void partial_draw_frame(void)','static void finish_drawing_frame (void)']:
  pos=draw.index(signature);brace=draw.index('{',pos)
  draw=draw[:brace+1]+'\n#ifdef ZZUAE_EARLY_DRAW\n if(!zu_draw_frame())return;\n#endif'+draw[brace+1:]
 draw=(SRC/'early_draw.inc').read_text()+draw

 (OUT/'src/drawing.cpp').write_text('#include "profile.h"\n'+draw)
 custom=(UP/'src/custom.cpp').read_text()
 pos=custom.index('static bool framewait (void)')
 end=custom.index('\n#define FPSCOUNTER',pos+20)
 # Diagnostic runs are unpaced; emulated chipset cycle scheduling is unchanged.
 custom=custom[:pos]+'''static bool framewait(void) {
 is_syncline=0;frame_rendered=render_screen(false);show_screen(0);
 frame_shown=true;return true;
}
'''+custom[end:]
 (OUT/'src/custom.cpp').write_text(custom)
 audio=(UP/'src/audio.cpp').read_text().replace('void update_audio (void)\n{','void update_audio (void)\n{\n ZU_PROFILE(2);')
 (OUT/'src/audio.cpp').write_text('#include "profile.h"\n'+audio+'\n#include "audio_mixer.inc"\n')
 return OUT/'src'
def build(render_optimisations=True):
 tree=prepare()
 names=['cpuemu_11','cpustbl','cpudefs','readcpu','newcpu','newcpu_common','custom','cia','events','memory','blitter','blitfunc','blittable','drawing','audio','gfxutil','keybuf','disk','diskutil','rommgr','cfgfile','crc32','inputdevice','rtc']
 flags=['-std=gnu++11','-O2','-mcpu=cortex-a9','-marm','-mfloat-abi=soft','-mno-unaligned-access','-fno-builtin','-fPIC','-fvisibility=hidden','-ffunction-sections','-fdata-sections','-fno-exceptions','-fno-rtti','-fno-stack-protector','-fpermissive','-fmax-errors=4','-DINLINE=inline','-DARMV6_ASSEMBLY','-DZZ_UAE','-DPANDORA','-DREGPARAM3=','-DREGPARAM2=']
 includes=[SRC,OUT/'include',tree,tree/'include',tree/'od-pandora',UP/'libretro/include',UP/'libretro',UP/'libretro/core']
 flags+=['-I'+inside(p) for p in includes]
 flags+=EXTRA_FLAGS
 if '--profile-stages' in sys.argv:flags+=['-DZZUAE_PROFILE']
 if '--neon-bitplanes' in sys.argv:flags+=['-DZZUAE_NEON_BITPLANES']
 if '--early-draw' in sys.argv or (render_optimisations and '--late-draw' not in sys.argv):flags+=['-DZZUAE_EARLY_DRAW']
 selected=[x for x in sys.argv[1:] if x not in {'--profile-stages','--neon-bitplanes','--early-draw','--late-draw'}] or names
 failed=[]
 for name in selected:
  source=tree/(name+'.cpp');obj=OUT/(name+'.o');log=OUT/(name+'.log')
  key=hashlib.sha256(source.read_bytes()+(OUT/'include/sysconfig.h').read_bytes()+str(flags).encode()+b''.join(p.read_bytes() for folder in [SRC,tree/'include',tree/'md-pandora',tree/'td-sdl'] for p in sorted(folder.rglob('*.h')))).hexdigest()
  stamp=obj.with_suffix('.sha256')
  if stamp.exists() and stamp.read_text()==key:continue
  command=[*RUN,'arm-none-eabi-g++',*flags,'-c',inside(source),'-o',inside(obj)]
  r=subprocess.run(command,capture_output=True,text=True);log.write_text(r.stdout+r.stderr)
  print(name,'PASS' if r.returncode==0 else 'FAIL',flush=True)
  if r.returncode:failed.append(name);print('\n'.join(r.stderr.splitlines()[:16]),flush=True)
  else:stamp.write_text(key)
 (OUT/'compile.json').write_text(json.dumps({'upstream':PIN,'flags':flags,'failed':failed,**BUILD_CONFIG},indent=2)+'\n')
 return bool(failed)
if __name__=='__main__':sys.exit(build())
