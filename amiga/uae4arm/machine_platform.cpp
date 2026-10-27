/* Platform integration in progress: a bounded A500/OCS diagnostic profile. */
#include "sysconfig.h"
#include "sysdeps.h"
#include "options.h"
#include "memory.h"
#include "custom.h"
#include "newcpu.h"
#include "cia.h"
#include "disk.h"
#include "audio.h"
#include "events.h"
#include "gui.h"
#include "xwin.h"
#include "drawing.h"
#include "uae.h"
#include "mmu_common.h"
#include "machine.h"
#include <stdarg.h>
struct uae_prefs currprefs,changed_prefs;
int quit_program,config_changed,savestate_state;
int64_t g_uae_epoch;
uint64_t zzuae_clock_us(void) {
 volatile uint32_t *t=(volatile uint32_t*)0xf8f00200u;uint32_t hi,lo;
 do{hi=t[1];lo=t[0];}while(hi!=t[1]);
 return (((uint64_t)hi<<32)|lo)/333u;
}
jmp_buf *zzuae_exception;
void zzuae_throw(int value) { if(zzuae_exception)longjmp(*zzuae_exception,value);abort(); }
struct gui_info gui_data;
void gui_flicker_led(int,int,int) {}
void gui_led(int,int,int) {}
void gui_message(const char*,...) {}
void gui_filename(int,const char*) {}
void gui_display(int) {}
void notify_user(int) {}
void fixup_cpu(uae_prefs *p) {
#ifndef ZZUAE_GUEST_JIT
 p->cpu_model=68000;p->cpu_compatible=true;p->cachesize=0;
#endif
#ifndef ZZUAE_GUEST_FPU
 p->fpu_model=0;
#endif
}
void uae_quit() { quit_program=UAE_QUIT;set_special(SPCFLAG_BRK); }
void uae_reset(int,int) { uae_quit(); }
void uae_restart(int,const char*) { uae_quit(); }
void target_reset() {}
void virtualdevice_init() {}
void protect_roms(bool) {}
bool mapped_malloc(addrbank *b) { b->baseaddr=(uae_u8*)calloc(1,b->reserved_size);b->allocated_size=b->baseaddr?b->reserved_size:0;return b->baseaddr!=NULL; }
void mapped_free(addrbank *b) { free(b->baseaddr);b->baseaddr=NULL;b->allocated_size=0; }
#include "profile_io.h"
void reset_all_systems() {
 init_eventtab();init_mem_banks();
 if(!chipmem_bank.baseaddr){chipmem_bank.reserved_size=currprefs.chipmem_size;chipmem_bank.mask=currprefs.chipmem_size-1;if(!mapped_malloc(&chipmem_bank))abort();}
 chipmem_full_mask=chipmem_bank.mask;
 kickmem_bank.mask=0x7ffff;
 map_banks(&chipmem_bank,0,currprefs.chipmem_size>>16,0);map_banks(&custom_bank,0xc0,0x20,0);
 if(currprefs.bogomem_size){
  if(!bogomem_bank.baseaddr){
   bogomem_bank.reserved_size=currprefs.bogomem_size;
   bogomem_bank.mask=currprefs.bogomem_size-1;bogomem_bank.start=0xc00000;
   if(!mapped_malloc(&bogomem_bank))abort();
  }
  map_banks(&bogomem_bank,0xc0,currprefs.bogomem_size>>16,0);
 }
 map_banks(&dummy_bank,0xd8,6,0);
 map_banks(&cia_bank,0xa0,0x20,0);map_banks(&kickmem_bank,0xf8,8,0);
 if(currprefs.cs_ksmirror_e0)map_banks(&kickmem_bank,0xe0,8,0);
 if(currprefs.cs_ksmirror_a8)map_banks(&kickmem_bank,0xa8,8,0);
 if(currprefs.cs_compatible==CP_A600)profile_map_gayle();
}
void devices_reset(int) { DISK_reset();CIA_reset(); }
void devices_hsync() { if((uae_stop && uae_stop()) || (uae_frame_limit && timeframes>=uae_frame_limit))set_special(SPCFLAG_BRK|SPCFLAG_MODE_CHANGE);DISK_hsync();if(currprefs.produce_sound)audio_hsync(); }
void devices_vsync_pre() {
 CIA_vsync_prehandler();
 if(currprefs.produce_sound>1)audio_activate();
 // Optional reproducible guest input, not injection into the host Workbench.
 if(uae_input_mode && (timeframes==900 || timeframes==910))
  zzuae_test_button(uae_input_mode,timeframes==900);
}
void devices_rethink() { rethink_cias(); }
void device_check_config() {}
void devices_update_sync(float,float) {}
// No CD32, host-native UAE traps, network, or expansion ROM in this profile.
#include "autoconf.h"
#include "traps.h"
#include "zfile.h"
#include "sd-pandora/sound.h"
#include <sys/time.h>
uaecptr rtarea_base;
addrbank rtarea_bank;
bool cloanto_rom;
int uae_boot_rom_type,gary_toenb;
volatile uae_atomic uae_int_requested;
volatile int bsd_int_requested;
void akiko_mute(int) {}
bool akiko_ntscmode() { return false; }
void bsdsock_fake_int_handler() {}
void m68k_handle_trap(unsigned int) { abort(); }
uaecptr here() { abort(); }
void org(uaecptr) { abort(); }
void calltrap(uae_u32) { abort(); }
void dw(uae_u16) { abort(); }
unsigned int define_trap(TrapHandler,int,const char*) { abort(); }
char *ua(const char *p){return strdup(p);}
char *au(const char *p){return strdup(p);}
void timeval_to_amiga(mytimeval*,int *d,int *m,int *t,int){*d=*m=*t=0;}
extern "C" int gettimeofday(timeval *t,void*){t->tv_sec=0;t->tv_usec=0;return 0;}
void fetch_saveimagepath(char *p,int n,int){if(n)p[0]=0;}
void target_addtorecent(const char*,int){}
void target_startup_msg(char*,char*){}
int handle_msgpump(){return 0;}
void gui_handle_events(){}
void savestate_check(){}
uae_u32 target_lastsynctime(){return 0;}
int max_uae_height=256;
unsigned long time_per_frame=20000;
int lockscr(){return 1;}
extern "C" void zzuae_live_present(void);
void unlockscr(){zzuae_live_present();}
void draw_status_line_single(unsigned char*,int,int){}
int cd32_fmv_active;
void cd32_fmv_genlock(vidbuffer*,vidbuffer*){abort();}
int check_prefs_changed_gfx(){return 0;}
bool target_graphics_buffer_update(){return false;}
bool vsync_switchmode(int){return false;}
bool render_screen(bool){return true;}
void show_screen(int){}
bool show_screen_maybe(bool){return true;}
uae_u16 sndbuffer[SOUND_BUFFERS_COUNT][(SNDBUFFER_LEN+32)*DEFAULT_SOUND_CHANNELS];
uae_u16 *sndbufpt=sndbuffer[0],*finish_sndbuff=sndbuffer[0]+SNDBUFFER_LEN*2;
void restart_sound_buffer(){sndbufpt=sndbuffer[0];}
void pause_sound_buffer(){}

void reset_sound(){restart_sound_buffer();}
#include "audio_arm.inc"
#undef stderr
extern "C" { FILE *const stderr=NULL; }
#include "inputdevice.h"
static int input_init(){return 1;}
static void input_close(){}
static int input_acquire(int,int){return 0;}
static void input_unacquire(int){}
static void input_read(){}
static int input_count(){return 0;}
static char *input_name(int){return NULL;}
static int input_widgets(int){return 0;}
static int input_widget(int,int,char*,uae_u32*){return 0;}
static int input_first(int,int){return 0;}
struct inputdevice_functions inputdevicefunc_joystick={input_init,input_close,input_acquire,input_unacquire,input_read,input_count,input_name,input_name,input_widgets,input_widget,input_first,input_widgets};
struct inputdevice_functions inputdevicefunc_mouse={input_init,input_close,input_acquire,input_unacquire,input_read,input_count,input_name,input_name,input_widgets,input_widget,input_first,input_widgets};
struct inputdevice_functions inputdevicefunc_keyboard={input_init,input_close,input_acquire,input_unacquire,input_read,input_count,input_name,input_name,input_widgets,input_widget,input_first,input_widgets};

volatile uint8_t *uae_shared;
int (*uae_stop)(void);
unsigned uae_frame_limit;
unsigned uae_input_mode;
int uae_volatile_write;
extern "C" void zzuae_shared(volatile uint8_t *p){uae_shared=p;}
int sleep_millis_main(int){return 0;} // Diagnostic is unpaced, including guest HALT.
