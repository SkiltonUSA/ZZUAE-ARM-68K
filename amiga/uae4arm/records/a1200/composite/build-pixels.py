from pathlib import Path
import sys,shutil,json,subprocess,runpy
sys.path.insert(0,'scripts')
import build_uae4arm as b
p=b.OUT/'a1200/gameplay';base=b.OUT/'a1200/performance/build-chipreads';out=p/'build-pixel4'
shutil.copytree(base,out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text())
f=out/'src/linetoscr.cpp';s=f.read_text();a=s.index('static int NOINLINE linetoscr_16_stretch1_aga');z=s.index('\n#endif',a);u=s[a:z]
marker='''    } else {
        while (dpix < dpix_end) {
            uae_u32 spix_val;
            uae_u32 out_val;
        
            spix_val = (pixdata.apixels[spix++] ^ xor_val) & and_val;'''
assert u.count(marker)==1
new='''    } else if (xor_val == 0 && and_val == 255) {
        /* Four independent palette lookups; retain the original two-pixel
         * tail and exact source advance for short or split spans. */
        while (dpix_end - dpix >= 8) {
            uae_u32 a = p_acolors[pixdata.apixels[spix]];
            uae_u32 b = p_acolors[pixdata.apixels[spix + 1]];
            uae_u32 c = p_acolors[pixdata.apixels[spix + 2]];
            uae_u32 d = p_acolors[pixdata.apixels[spix + 3]];
            *((uae_u32 *)&buf[dpix]) = a;
            *((uae_u32 *)&buf[dpix + 2]) = b;
            *((uae_u32 *)&buf[dpix + 4]) = c;
            *((uae_u32 *)&buf[dpix + 6]) = d;
            spix += 4;
            dpix += 8;
        }
        while (dpix < dpix_end) {
            *((uae_u32 *)&buf[dpix]) = p_acolors[pixdata.apixels[spix++]];
            dpix += 2;
        }
'''+marker
# marker starts with closing brace, closing the inserted branch.
u=u.replace(marker,new);s=s[:a]+u+s[z:];f.write_text(s)
subprocess.run([*b.RUN,'arm-none-eabi-g++',*c['flags'],'-c',b.inside(out/'src/drawing.cpp'),'-o',b.inside(out/'drawing.o')],check=True)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
exec((b.ROOT/'.context/amiga/uae4arm/a1200/performance/extend-chipreads.py').read_text().replace("for variant in ('chipreads',):", "for variant in ('pixel4',):").replace("a1200/performance/build-", "a1200/gameplay/build-"))
