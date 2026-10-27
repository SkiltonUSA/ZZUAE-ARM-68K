#!/usr/bin/env python3
"""Build bounded A500/OCS diagnostics; --hardware also packages 68K launchers."""
import json,subprocess,re,sys
from uae4arm_version import VERSION
from build_uae4arm import ROOT,OUT,SRC,RUN,inside,prepare
prepare()
flags=json.loads((OUT/'compile.json').read_text())['flags']
neon_experiment='--scalar-renderer' not in sys.argv
if neon_experiment:flags+=['-DZZUAE_NEON_EXPERIMENT']
flags+=['-I'+inside(OUT),'-I/work/amiga/uae4arm/support/core1','-I/work/amiga/arm_debug','-I/work/amiga/arm_debug/zz9000']
obj=OUT/'machine_probe.o'
subprocess.run([*RUN,'arm-none-eabi-g++',*flags,'-c',inside(SRC/'machine_probe.cpp'),'-o',inside(obj)],check=True)
objects=[obj]
for source in [SRC/'machine_platform.cpp',SRC/'live_arm.cpp',SRC/'profile.cpp',SRC/'media.cpp',ROOT/'amiga/uae4arm/support/allocator/heap.c',ROOT/'amiga/uae4arm/support/memory/memory.c',SRC/'runtime.c',SRC/'jump.S']+([SRC/'convert_neon.S'] if neon_experiment else []):
 target=OUT/('machine-'+source.stem+'.o')
 cpp=source.suffix=='.cpp'
 opts=flags if cpp else [f for f in flags if f not in ['-std=gnu++11','-fno-exceptions','-fno-rtti','-fpermissive']]
 subprocess.run([*RUN,'arm-none-eabi-g++' if cpp else 'arm-none-eabi-gcc',*opts,'-c',inside(source),'-o',inside(target)],check=True)
 objects.append(target)
objects+=[OUT/(n+'.o') for n in ['cpuemu_11','cpustbl','cpudefs','readcpu','newcpu','newcpu_common','custom','cia','events','memory','blitter','blitfunc','blittable','drawing','audio','gfxutil','keybuf','disk','diskutil','rommgr','cfgfile','crc32','inputdevice','rtc']]
link=(ROOT/'amiga/uae4arm/support/libc/payload.ld').read_text().replace('0x100000','0x400000').replace('0x220000','0x640000').replace('0x17d0000','0x1fd0000').replace('ENTRY(_start)','ENTRY(mesen_test)')
(OUT/'machine.ld').write_text(link)
subprocess.run(['/opt/homebrew/opt/lld/bin/ld.lld','-shared','-Bsymbolic','--no-undefined','--gc-sections','--error-limit=0','-T',str(OUT/'machine.ld'),*map(str,objects),'--exclude-libs=ALL',str(ROOT/'.context/amiga/uae4arm/libc/libc.a'),str(OUT/'libgcc.a'),'-o',str(OUT/'uae-machine.elf')],check=True)

def audit_integer_context(elf):
 # jump.S deliberately saves integer context only. Optional NEON is confined
 # to audited assembly leaves. Reject floating-point archive helpers, other
 # SIMD instructions and A7 hardware division before packaging for the A9.
 code=subprocess.check_output(['/opt/homebrew/opt/llvm/bin/llvm-objdump','-d',str(elf)],text=True)
 bad=[];function=''
 for line in code.splitlines():
  label=re.match(r'^[0-9a-f]+ <([^>]+)>:',line)
  if label:function=label[1]
  if re.search(r'\t[us]div\s',line):bad.append(line)
  if re.search(r'\tv[a-z][a-z0-9.]*\s',line) and not(neon_experiment and function in {'zu_neon_available','zu_neon_snapshot','zu_convert_neon'}):bad.append(line)
 if bad:raise ValueError('Unsupported instruction in integer-only worker:\n'+'\n'.join(bad[:10]))

audit_integer_context(OUT/'uae-machine.elf')

# Optional isolated Amiga diagnostic package. All media stays external/private.
import sys,re,importlib.util,hashlib
if '--hardware' in sys.argv:
 hw=OUT/'machine';hw.mkdir(exist_ok=True)
 common=['-DZZ_BLOCK_SIZE=0x2000000','-DZZ_CONTROL=0x480000','-DMB_ALLOCATION=0x2000000u','-DMB_MMU','-DMB_DCACHE']
 for name in ['worker.cpp','mmu.c','mmu.h','mmu_asm.S','mmu_plan.h']:
  data=(ROOT/'amiga/uae4arm/support/core1'/name).read_text()
  if name=='mmu_plan.h':
   moves={'0x40000u':'0x400000u','0x50000u':'0x420000u','0x60000u':'0x430000u','0x80000u':'0x480000u','0x84000u':'0x640000u','0x82000u':'0x482000u','0x82400u':'0x482400u'}
   data=re.sub('|'.join(moves),lambda m:moves[m[0]],data)
  if name=='worker.cpp':
   data='#include "machine.h"\n'+data
   data=data.replace('    shared=base;','    shared=base;zzuae_shared(base);')
  (hw/name).write_text(data)
 hwobjects=objects.copy()
 for name in ['worker.cpp','mmu.c','mmu_asm.S']:
  source=hw/name;target=hw/(name+'.o');cpp=source.suffix=='.cpp'
  opts=flags if cpp else [f for f in flags if f not in ['-std=gnu++11','-fno-exceptions','-fno-rtti','-fpermissive']]
  subprocess.run([*RUN,'arm-none-eabi-g++' if cpp else 'arm-none-eabi-gcc','-I'+inside(hw),*opts,*common,'-c',inside(source),'-o',inside(target)],check=True)
  hwobjects.append(target)
 (hw/'payload.ld').write_text(link.replace('ENTRY(mesen_test)','ENTRY(_start)'))
 elf=hw/'uae.elf'
 subprocess.run(['/opt/homebrew/opt/lld/bin/ld.lld','-shared','-Bsymbolic','--no-undefined','--gc-sections','-T',str(hw/'payload.ld'),*map(str,hwobjects),'--exclude-libs=ALL',str(ROOT/'.context/amiga/uae4arm/libc/libc.a'),str(OUT/'libgcc.a'),'-o',str(elf)],check=True)
 audit_integer_context(elf)
 spec=importlib.util.spec_from_file_location('uaeelf',SRC/'elf.py');packer=importlib.util.module_from_spec(spec);spec.loader.exec_module(packer)
 payload,relocations,entry=packer.unpack(elf.read_bytes())
 from build_zz9000_debug import unpack_elf
 mapping,rel,point=unpack_elf((OUT/'mapping.elf').read_bytes());assert not rel and not point
 array=lambda name,data:'static const unsigned char '+name+'[]={'+','.join(map(str,data))+'};\n'
 (hw/'zz_payload.h').write_text(f'#define ZZ_ENTRY {entry}u\n'+array('zz_image',payload)+array('zz_mapping_probe',mapping)+'static const unsigned long zz_relocations[]={'+','.join(map(str,relocations))+'};\n')
 host=(ROOT/'amiga/uae4arm/support/core1/host.c').read_text().replace('#include "expected.h"','#include "machine.h"\n#include "profiles.h"\n#include <stdlib.h>\n#include <errno.h>\n#include <string.h>\n#ifdef UAE_BOOT\nstatic const char *disk_path="RAM:WB12.adf",*rom_path="RAM:Kick12.rom";\nstatic ULONG frame_limit=UAE_BOOT_FRAMES,boot_options,frame_period=20000,profile=ZP_LEGACY,audio_mode,joystick_mode=1,display_rate=50,scanline_mode;\n#endif').replace('10000000u','120000000u')
 start=host.index('    if(!request(MB_VERIFY))goto done;');end=host.index('\ndone:',start)
 host=host[:start]+'''    #ifdef UAE_BOOT
    puts("STARTUP Loading Kickstart and DF0...");
    if(!load_media(rom_path,UAE_ROM,zp_rom_size(profile)) || !load_media(disk_path,UAE_DISK,UAE_DISK_SIZE))goto done;
    {const volatile UBYTE *rom=shared+UAE_ROM;ULONG major=((ULONG)rom[12]<<8)|rom[13],rev=((ULONG)rom[14]<<8)|rom[15],sum=0,crc=0xffffffffu;
     for(ULONG at=0;at<zp_rom_size(profile);at+=4){ULONG old=sum;sum+=ad_get(rom,at);if(sum<old)sum++;}
     for(ULONG at=0;at<zp_rom_size(profile);at++)crc=zp_crc_byte(crc,rom[at]);
     if(!zp_rom_target_ok(crc^0xffffffffu) || sum!=0xffffffffu || !zp_rom_matches(profile,major,rev)){puts("ERROR Kickstart does not match selected machine or checksum failed");goto done;}
     printf("STARTUP Kickstart %u.%u verified\\n",major,rev);}
    printf("MEDIA df0=%s target_frames=%u input=%u volatile_write=%u\\n",disk_path,frame_limit,boot_options&3u,(boot_options&4u)!=0);
    ad_put(shared,UAE_OPTIONS,frame_limit);ad_put(shared,UAE_OPTIONS+4,boot_options);ad_put(shared,UAE_OPTIONS+20,profile==ZP_LEGACY?0:profile+1);ad_put(shared,UAE_OPTIONS+40,display_rate);syncio->push(shared+UAE_OPTIONS,44,NULL);syncio->barrier(NULL);
    if((boot_options&8u) && !live_open(timer))goto done;
    if(!ua_audio_host_open(shared,syncio,audio_mode))goto done;
    printf("STARTUP Booting %s...\\n",profile==0?"A1000":profile==2?"A500 Plus":profile==3?"A600":"A500");
    t0=us();
    if(!request(MB_BENCH))goto done;
    syncio->pull(shared+UAE_LIVE,32,NULL);
    printf("PIXELS neon_rows=%u scalar_rows=%u simd_checks=%u simd_errors=%u\\n",ad_get(shared+UAE_LIVE,UL_NEON_ROWS),ad_get(shared+UAE_LIVE,UL_SCALAR_ROWS),ad_get(shared+UAE_LIVE,UL_SIMD_CHECKS),ad_get(shared+UAE_LIVE,UL_SIMD_ERRORS));
    syncio->pull(shared+0x482900u,96,NULL);
    for(unsigned stage=0;stage<6;stage++)if(ad_get(shared,0x482908u+stage*16))
      printf("STAGE id=%u ticks_hi=%u ticks_lo=%u calls=%u\\n",stage,ad_get(shared,0x482900u+stage*16),ad_get(shared,0x482904u+stage*16),ad_get(shared,0x482908u+stage*16));
    printf("BOOT elapsed_us=%u rendered_frames=%u\\n",(ULONG)(us()-t0),value(9));
    #else
    if(!request(MB_VERIFY))goto done;
    if(value(0)!=100000 || value(2)!=1000010 || value(3)!=0x60000000u || value(7)!=0x108)goto done;
    #endif
    printf("UAE_MACHINE instructions=%u cycles=%u hash=%08x pc=%08x frames=%u ticks=%u\\n",value(0),value(2),value(3),value(7),value(9),value(6));
    {
      ULONG bytes;
      BPTR output;
      #ifdef UAE_BOOT
      bytes=640*256*2;output=Open("RAM:ZZUAE-Boot.rgb565",MODE_NEWFILE);
      #else
      bytes=320*256*2;output=Open("RAM:ZZUAE-OCS.rgb565",MODE_NEWFILE);
      #endif
      if(!output)goto done;
      syncio->pull(shared+UAE_FRAME,bytes,NULL);
      if(Write(output,(APTR)(shared+UAE_FRAME),bytes)!=(LONG)bytes){Close(output);goto done;}
      Close(output);
    }
    #ifdef UAE_BOOT
    if(!live_quit && value(9)!=frame_limit)puts("UAE_MACHINE instruction bound reached before frame target; capture retained");
    #endif
    syncio->pull(shared+UAE_OPTIONS+8,12,NULL);
    printf("MEMORY chip=%u slow=%u verified=%u\\n",ad_get(shared,UAE_OPTIONS+8),ad_get(shared,UAE_OPTIONS+12),ad_get(shared,UAE_OPTIONS+16));
    puts("UAE_MACHINE PASS; bounded diagnostic, bounded boot and transport check; audible quality requires listening");fflush(stdout);rc=0;
''' +host[end:]
 host=host.replace('MESEN CPU-ONLY','UAE MACHINE DIAGNOSTIC').replace('ULONG t0,t1,rate,i;','ULONG t0,t1,rate;')
 # Wrapper supplies optional diagnostic media/frame arguments; the shared
 # launcher and its mapping/teardown implementation remain byte-for-byte source.
 host+='''
#undef main
extern int zzuae_main(int,char **);
/* The polling loops handle Ctrl-C cooperatively. libc must never abort
 * during ARM restoration, port removal or allocation release. */
void __chkabort(void){}
#ifdef UAE_BOOT
static int registered_run(char **argv) {
    struct MsgPort *port;char name[48];int rc;
    snprintf(name,sizeof(name),"ZZUAE.Run.%.8s",argv[1]);
    port=CreateMsgPort();if(!port)return 20;
    port->mp_Node.ln_Name=name;
    Forbid();if(FindPort(name)){Permit();DeleteMsgPort(port);return 20;}
    AddPort(port);Permit();
    puts("STARTUP Preparing ZZ9000...");
    rc=zzuae_main(3,argv);
    RemPort(port);DeleteMsgPort(port);return rc;
}
#endif
int main(int argc,char **argv) {
    setvbuf(stdout,NULL,_IONBF,0);
    #ifdef UAE_BOOT
    if(argc>=4 && argc<=23) {
        disk_path=argv[3];
        if(argc>=5){char *end;errno=0;frame_limit=strtoul(argv[4],&end,10);
            if(errno || *end || !frame_limit || frame_limit>6000)return 20;}
        {int i;for(i=5;i<argc;i++) {
            if(!strcmp(argv[i],"ROM") && i+1<argc)rom_path=argv[++i];
            else if(!strcmp(argv[i],"FPS") && i+1<argc){
                const char *rate=argv[++i];
                if(!strcmp(rate,"25"))frame_period=40000;
                else if(!strcmp(rate,"30"))frame_period=33334;
                else if(!strcmp(rate,"50"))frame_period=20000;
                else if(!strcmp(rate,"MAX"))frame_period=0;
                else return 20;
            }
            else if(!strcmp(argv[i],"RAM") && i+1<argc){
                const char *ram=argv[++i];
                if(!strcmp(ram,"1M") || !strcmp(ram,"EXPANDED"))boot_options|=32u;
                else if(!strcmp(ram,"512K") || !strcmp(ram,"BASE"))boot_options&=~32u;
                else return 20;
            }
            else if(!strcmp(argv[i],"MODEL") && i+1<argc){
                const char *model=argv[++i];
                if(!strcmp(model,"A1000"))profile=ZP_A1000;
                else if(!strcmp(model,"A500"))profile=ZP_A500;
                else if(!strcmp(model,"A500PLUS"))profile=ZP_A500PLUS;
                else if(!strcmp(model,"A600"))profile=ZP_A600;
                else return 20;
            }
            else if(!strcmp(argv[i],"SCANLINES") && i+1<argc){
                const char *value=argv[++i];
                if(value[0]<'0' || value[0]>'3' || value[1])return 20;
                scanline_mode=value[0]-'0';
            }
            else if(!strcmp(argv[i],"JOY") && i+1<argc){
                const char *joy=argv[++i];
                if(!strcmp(joy,"OFF"))joystick_mode=0;
                else if(!strcmp(joy,"PORT2"))joystick_mode=1;
                else return 20;
            }
            else if(!strcmp(argv[i],"AUDIO") && i+1<argc){
                const char *sound=argv[++i];
                if(!strcmp(sound,"OFF"))audio_mode=0;
                else if(!strcmp(sound,"PAULA"))audio_mode=1;
                else if(!strcmp(sound,"AHI"))audio_mode=2;
                else return 20;
            }
            else if(!strcmp(argv[i],"WRITE"))boot_options|=4u;
            else if(!strcmp(argv[i],"LIVE"))boot_options|=24u;
            else if(!strcmp(argv[i],"COPY"))boot_options|=8u;
            else if(!strcmp(argv[i],"LMB"))boot_options=(boot_options&~3u)|1u;
            else if(!strcmp(argv[i],"FIRE"))boot_options=(boot_options&~3u)|2u;
            else if(!strcmp(argv[i],"SPACE"))boot_options=(boot_options&~3u)|3u;
            else return 20;
        }}
        if(audio_mode){
            if(!(boot_options&UAE_OPT_LIVE))return 20;
            display_rate=frame_period==40000?25:frame_period==33334?30:50;
            boot_options|=UAE_OPT_AUDIO;frame_period=0; /* PCM consumption paces PAL guest time. */
        }
        return registered_run(argv);
    }
    if(argc==3)return registered_run(argv);
    #endif
    return zzuae_main(argc,argv);
}
'''
 pos=host.index('int ff_window(')
 host=host[:pos]+'''#ifdef UAE_BOOT
static int load_media(const char *name,ULONG offset,ULONG size) {
    BPTR f=Open((STRPTR)name,MODE_OLDFILE);ULONG n=0;UBYTE b[8192];LONG got;
    if(!f){printf("Missing media %s\\n",name);return 0;}
    while(n<size){ULONG want=size-n;if(want>sizeof b)want=sizeof b;
        got=Read(f,b,want);if(got!=(LONG)want){Close(f);return 0;}
        CopyMem(b,(APTR)(shared+offset+n),want);n+=want;
    }
    got=Read(f,b,1);Close(f);if(got!=0)return 0;
    syncio->push(shared+offset,size,NULL);syncio->barrier(NULL);return 1;
}
#endif
''' +host[pos:]
 # Optional live mode shares the same allocation and mandatory teardown.
 marker='static int request(ULONG op) {'
 host=host.replace(marker,'#ifdef UAE_BOOT\n#include "audio_host.h"\n#include "live_host.h"\n#endif\n'+marker)
 host=host.replace('        syncio->pull(reply,96,NULL);', '#ifdef UAE_BOOT\n        if(live_window)live_poll();\n        if(!ua_audio_host_service()){live_abort();}\n#endif\n        syncio->pull(reply,96,NULL);')
 host=host.replace('            if(ad_get(reply,MB_ERROR))printf', '#ifdef UAE_BOOT\n            if(live_quit && ad_get(reply,MB_ERROR)==2)return !live_failed;\n#endif\n            if(ad_get(reply,MB_ERROR))printf')
 host=host.replace('        if(SetSignal(0,SIGBREAKF_CTRL_C)&SIGBREAKF_CTRL_C)return 0;', '#ifdef UAE_BOOT\n        if(!live_window)\n#endif\n        if(SetSignal(0,SIGBREAKF_CTRL_C)&SIGBREAKF_CTRL_C)return 0;')
 host=host.replace('    ULONG token=(sequence+1)', '#ifdef UAE_BOOT\n    ULONG timeout=live_window?zu_run_timeout(frame_limit,audio_mode?20000:frame_period):120000000u;\n#else\n    ULONG timeout=120000000u;\n#endif\n    ULONG token=(sequence+1)')
 host=host.replace('(us()-start)<120000000u', '(us()-start)<timeout')
 host=host.replace('        Delay(1);', '#ifdef UAE_BOOT\n        if(live_window)live_idle();else\n#endif\n        Delay(1);')
 host=host.replace('done:\n    if(opened)', 'done:\n#ifdef UAE_BOOT\n    if(live_window)live_elapsed=us()-live_started;\n    {ULONG drain_start=us();while(ua_audio_host_pending() && (ULONG)(us()-drain_start)<2000000u){if(!ua_audio_host_service())break;Delay(1);}}\n    if(!ua_audio_host_close())rc=20;\n#endif\n    if(opened)')
 host += '\nvoid ff_cleanup(void) {\n#ifdef UAE_BOOT\n live_close();\n#endif\n}\n'
 (hw/'host.c').write_text(host)
 from amiga import PIN
 includes=['-I'+str(hw.relative_to(ROOT)),'-Iamiga/uae4arm','-Iamiga/uae4arm/support/core1','-Iamiga/arm_debug','-Iamiga/arm_debug/zz9000']
 for boot in [False,True]:
  name='ZZUAEBoot' if boot else 'ZZUAEOCS'
  command=['podman','--connection','nuflix-converter-root','run','--rm','--platform','linux/amd64','-v',str(ROOT)+':/work','-w','/work',PIN['image'],'m68k-amigaos-gcc','-std=c99','-noixemul','-m68020','-O2','-Wall','-Wextra','-Werror',*common,*includes,'-DZZ_HEADLESS_BENCH','-DFF_DIRECT','-DZZ_RELEASE','-DZZ_HEADLESS_MMU','-DZZ_HEADLESS_ICACHE','-DZZ_APP_NAME="'+name+'"','-DZZ_APP_VERSION="'+VERSION+'"','-DZZ_MIN_STACK=131072']
  if boot:command+=['-DUAE_BOOT','amiga/uae4arm/audio_host.c']
  command+=['-Dmain=zzuae_main','amiga/arm_debug/zz9000/launcher.c',str((hw/'host.c').relative_to(ROOT)),'-lamiga','-o',str((hw/name).relative_to(ROOT))]
  subprocess.run(command,check=True)
 print('Built hardware diagnostics',len(payload),'ARM bytes')

if '--hardware' in sys.argv:
 subprocess.run(['podman','--connection','nuflix-converter-root','run','--rm','--platform','linux/amd64','-v',str(ROOT)+':/work','-w','/work',PIN['image'],'m68k-amigaos-gcc','-std=c99','-noixemul','-m68020','-O2','-Wall','-Wextra','-Werror','amiga/uae4arm/preview.c','-lamiga','-o',str((hw/'ZZUAEPreview').relative_to(ROOT))],check=True)

if '--hardware' in sys.argv:
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 sources=[*SRC.rglob('*'),*ROOT.glob('scripts/*uae4arm*.py'),*ROOT.glob('tests/amiga/uae4arm/*')]
 sources.append(ROOT/'amiga/common/rtg_mapping.h')
 sources += [ROOT/p for p in ['amiga/uae4arm/support/core1/worker.cpp','amiga/uae4arm/support/core1/mmu.c','amiga/uae4arm/support/core1/mmu_asm.S','amiga/uae4arm/support/core1/mmu_plan.h','amiga/uae4arm/support/core1/host.c','amiga/arm_debug/zz9000/launcher.c']]
 record={'version':VERSION,'neon_renderer':neon_experiment,'profile_stages':'-DZZUAE_PROFILE' in flags,'upstream':json.loads((OUT/'compile.json').read_text()),
  'compiler':subprocess.check_output([*RUN,'arm-none-eabi-g++','--version'],text=True).splitlines()[0],
  'sources':{str(p.relative_to(ROOT)):sha(p) for p in sources if p.is_file() and '__pycache__' not in str(p)},
  'archives':{str(p.relative_to(ROOT)):sha(p) for p in [OUT/'libgcc.a',ROOT/'.context/amiga/uae4arm/libc/libc.a']},
  'artifacts':{p.name:sha(p) for p in [OUT/'uae-machine.elf',hw/'uae.elf',hw/'ZZUAEOCS',hw/'ZZUAEBoot',hw/'ZZUAEPreview']},
  'scope':'Bounded PAL A500/OCS 68000 prototype, 512 KiB chip RAM; capture or live P96 bitmap; keyboard/mouse transport; optional volatile DF0 writes; Paula/AHI stereo PCM transport'}
 (OUT/'build-manifest.json').write_text(json.dumps(record,indent=2)+'\n')
