from pathlib import Path
import sys,shutil,json,subprocess,runpy
sys.path.insert(0,'scripts')
import build_uae4arm as b
p=b.OUT/'a1200/gameplay';base=b.OUT/'a1200/performance/build-chipreads';out=p/'build-composite-profile'
shutil.copytree(base,out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text());c['flags']=['-I'+b.inside(b.SRC)]+c['flags']+['-DZZUAE_PROFILE'];(out/'compile.json').write_text(json.dumps(c))
for name in ['profile.h','profile.cpp']:
 s=(p/'build-fetch-profile/test-source'/name).read_text().replace('gp_fetch','gp_composite')
 (b.SRC/name).write_text(s)
f=out/'src/drawing.cpp';s=f.read_text()
for name,stage in [('static void pfield_draw_line (int lineno, int gfx_ypos, int follow_ypos)',0),('static void pfield_doline (int lineno)',1),('static void adjust_drawing_colors (int ctable, int need_full)',2),('STATIC_INLINE void do_color_changes (line_draw_func worker_border, line_draw_func worker_pfield)',4),('static void pfield_do_linetoscr(int start, int stop)',5)]:
 marker=name+'\n{';assert s.count(marker)==1;s=s.replace(marker,marker+f'\n GP_PROFILE({stage});')
marker='  dip_for_drawing = curr_drawinfo + lineno;';assert s.count(marker)==1
s=s.replace(marker,marker+'''
 if(timeframes>=3000){
  ++gp_composite[0];gp_composite[1]+=dp_for_drawing->plfleft<0;
  gp_composite[2]+=dip_for_drawing->nr_sprites!=0;
  gp_composite[3]+=dip_for_drawing->nr_color_changes!=0;
  gp_composite[4]+=dip_for_drawing->nr_color_changes;
 }
''')
marker='static void adjust_drawing_colors (int ctable, int need_full)\n{\n GP_PROFILE(2);'
s=s.replace(marker,marker+'''
 if(timeframes>=3000){
  bool copy=drawing_color_matches!=ctable || need_full<0;
  if((copy&&need_full) || (!copy&&need_full&&color_match_type!=color_match_full))++gp_composite[5];
  else if(copy)++gp_composite[6];else ++gp_composite[7];
 }
''')
marker='static void pfield_do_linetoscr(int start, int stop)\n{\n GP_PROFILE(5);'
s=s.replace(marker,marker+'''
 if(timeframes>=3000){
  ++gp_composite[8];gp_composite[9]+=stop-start;
  unsigned kind=bplham?0:bpldualpf?1:bplehb?2:3;
  ++gp_composite[14+kind];gp_composite[18+kind]+=stop-start;
  if(pfield_do_linetoscr_normal==linetoscr_16_stretch1_aga)++gp_composite[10];
  else if(pfield_do_linetoscr_normal==linetoscr_16_aga)++gp_composite[11];
  else if(pfield_do_linetoscr_normal==linetoscr_16_shrink1_aga || pfield_do_linetoscr_normal==linetoscr_16_shrink2_aga)++gp_composite[12];
  else ++gp_composite[13];
  gp_composite[22]+=bplxor==0&&bpland==255;
 }
''')
# Scope both sprite-composition blocks, including their setup.
a=s.index('static void pfield_draw_line (');z=s.index('\n}',a)
u=s[a:z]
for marker in ['if (dip_for_drawing->nr_sprites) {','if (dosprites) {']:
 assert u.count(marker)==1;u=u.replace(marker,marker+'\n GP_PROFILE(3);')
s=s[:a]+u+s[z:];f.write_text(s)
subprocess.run([*b.RUN,'arm-none-eabi-g++',*c['flags'],'-c',b.inside(f),'-o',b.inside(out/'drawing.o')],check=True)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
f=out/'machine/host.c';s=f.read_text();a=s.index('      for(unsigned i=0;i<ZJ_STAGES;i++)printf(');z=s.index('\n',a)
s=s[:a]+'      for(unsigned i=0;i<28;i++)printf("COMPOSITE_COUNT id=%u value=%u\\n",i,ad_get(shared,ZJ_PROFILE_BASE+16+4*i));'+s[z:];f.write_text(s)
exec((b.ROOT/'.context/amiga/uae4arm/a1200/performance/extend-chipreads.py').read_text().replace("for variant in ('chipreads',):", "for variant in ('composite-profile',):").replace("a1200/performance/build-", "a1200/gameplay/build-"))
