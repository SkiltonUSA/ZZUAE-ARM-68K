from pathlib import Path
import sys,shutil,json,runpy
sys.path.insert(0,'scripts');import build_uae4arm as b
p=b.OUT/'a1200';variant=sys.argv[1] if len(sys.argv)>1 else 'audio-trace'
out=p/('gameplay/build-'+variant)
shutil.copytree(p/'gameplay/build-pixel4',out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text());c['flags']=['-I'+b.inside(b.SRC)]+c['flags'];
if variant=='audio-2048':c['flags']+=['-DUA_FRAMES=2048u']
(out/'compile.json').write_text(json.dumps(c))
f=b.SRC/'audio_arm.inc';s=f.read_text();a=s.index('static void pcm_publish')
s=s[:a]+'''/* Private diagnostics. Two 32-byte banks in unused audio control space. */
struct AudioTrace { uint32_t blocks,intervals,last,maximum,waits; uint64_t span,blocked; };
static AudioTrace audio_trace[2];
static uint32_t audio_clock(){return *(volatile uint32_t*)0xf8f00200u;}
static void audio_record(unsigned k,uint32_t now,uint32_t blocked,bool waited){
 AudioTrace &t=audio_trace[k];
 if(t.blocks){uint32_t delta=now-t.last;t.span+=delta;++t.intervals;if(delta>t.maximum)t.maximum=delta;}
 t.last=now;++t.blocks;t.blocked+=blocked;t.waits+=waited;
 unsigned off=0x483080u+k*32u;
 ad_put(uae_shared,off,t.blocks);ad_put(uae_shared,off+4,t.intervals);
 ad_put(uae_shared,off+8,t.span>>32);ad_put(uae_shared,off+12,t.span);
 ad_put(uae_shared,off+16,t.maximum);ad_put(uae_shared,off+20,t.waits);
 ad_put(uae_shared,off+24,t.blocked>>32);ad_put(uae_shared,off+28,t.blocked);
}
'''+s[a:]
s=s.replace('    while(!ua_room(pcm_write,ad_get(p,UA_READ)))', '    uint32_t trace_start=audio_clock();\n    bool trace_wait=!ua_room(pcm_write,ad_get(p,UA_READ));\n    while(!ua_room(pcm_write,ad_get(p,UA_READ)))',1)
s=s.replace('    __asm__ volatile("dsb sy" ::: "memory");', '''    uint32_t trace_end=audio_clock();
    audio_record(0,trace_start,trace_wait?trace_end-trace_start:0,trace_wait);
    if(timeframes>=3000)audio_record(1,trace_start,trace_wait?trace_end-trace_start:0,trace_wait);
    __asm__ volatile("dsb sy" ::: "memory");''',1);f.write_text(s)
if variant=='audio-only':
 f=b.SRC/'live_arm.cpp';v=f.read_text()
 needle='    if(draw)++zu_drawn_frames;else ++zu_skipped_frames;'
 assert v.count(needle)==1
 v=v.replace(needle,'''    // Private upper-bound test: keep the final frame and all guest hardware work.
    if(timeframes+1<uae_frame_limit){draw=false;input();}
'''+needle)
 f.write_text(v)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
# Add host-only diagnostics, retaining the existing queue/device implementation.
s=(b.ROOT/'amiga/uae4arm/audio_host.c').read_text()
s=s.replace('static int audio_opened;', '''static int audio_opened;
static ULONG trace_calls,trace_last,trace_max,trace_hist[5],trace_empty,trace_backlog;
static uint64_t trace_empty_us,trace_backlog_us;
''')
needle=' r=ad_get(b,UA_READ);';assert s.count(needle)==1
s=s.replace(needle,''' ULONG trace_now=us(),trace_delta=trace_calls?trace_now-trace_last:0;
 trace_last=trace_now;++trace_calls;if(trace_delta>trace_max)trace_max=trace_delta;
 trace_hist[trace_delta<5000?0:trace_delta<20000?1:trace_delta<40000?2:trace_delta<80000?3:4]++;
'''+needle)
needle=' ad_put(b,UA_RESERVE,n*UA_FRAMES+i);'
s=s.replace(needle,''' if(!n&&!i){if(w==r){trace_empty++;trace_empty_us+=trace_delta;}else{trace_backlog++;trace_backlog_us+=trace_delta;}}
'''+needle)
needle='  player_audio_close();\n }\n return !audio_error;'
assert s.count(needle)==1
s=s.replace(needle,'''  printf("AUDIO_SERVICE calls=%u max_us=%u lt5ms=%u lt20ms=%u lt40ms=%u lt80ms=%u ge80ms=%u empty=%u backlog=%u empty_us=%u backlog_us=%u\\n",trace_calls,trace_max,trace_hist[0],trace_hist[1],trace_hist[2],trace_hist[3],trace_hist[4],trace_empty,trace_backlog,(ULONG)trace_empty_us,(ULONG)trace_backlog_us);
  syncio->pull(shared+0x483080,64,NULL);
  for(unsigned k=0;k<2;k++){
   unsigned off=0x483080+k*32;
   printf("AUDIO_PRODUCER bank=%u blocks=%u intervals=%u span_hi=%u span_lo=%u max_ticks=%u waits=%u wait_hi=%u wait_lo=%u\\n",k,ad_get(shared,off),ad_get(shared,off+4),ad_get(shared,off+8),ad_get(shared,off+12),ad_get(shared,off+16),ad_get(shared,off+20),ad_get(shared,off+24),ad_get(shared,off+28));
  }
'''+needle)
(out/'audio_trace_host.c').write_text(s)
# Existing bounded host compile, with the private diagnostic audio source.
extend=(b.ROOT/'.context/amiga/uae4arm/a1200/performance/extend-chipreads.py').read_text().replace("for variant in ('chipreads',):", f"for variant in ({variant!r},):").replace('a1200/performance/build-','a1200/gameplay/build-').replace("'amiga/uae4arm/audio_host.c'",repr(str((out/'audio_trace_host.c').relative_to(b.ROOT))))
if variant=='audio-2048':extend=extend.replace("'-DUAE_BOOT'","'-DUAE_BOOT','-DUA_FRAMES=2048u'")
exec(extend)
