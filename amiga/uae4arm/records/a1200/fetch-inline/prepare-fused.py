from pathlib import Path
import shutil, difflib

p = Path('.context/amiga/uae4arm/a1200/gameplay')
out = p / 'build-fetch-fused'
shutil.copytree(p / 'build-pixel4', out, dirs_exist_ok=True)
f = out / 'src/custom.cpp'
original = f.read_text()
a = original.index('STATIC_INLINE void update_fetch (int until, int fm)')
z = original.index('static void update_fetch_0', a)
part = original[a:z]
head = part[:part.index('\t/* First, a loop')]
bulk = part[part.index('\t// vdiw getting cleared'):part.index('\tfor (; pos < until; pos++)')]
replacement = head + '''
    bool preparing = true;
    for (;;) {
        if (pos == until) {
            if (until >= maxhpos) {
                maybe_finish_last_fetch(pos, fm);
                return;
            }
            flush_display(fm);
            return;
        }
        if (preparing && fetch_state == fetch_was_plane0) {
''' + bulk + '''
            preparing = false;
            continue;
        }
        if (!preparing && fetch_state == fetch_was_plane0) {
            beginning_of_plane_block(pos, fm);
            estimate_last_fetch_cycle(pos);
        }
        fetch_start();
        if (one_fetch_cycle_0(pos, ddfstop_to_test, dma, fm))
            return;
        ++pos;
    }
}

'''
s = original[:a] + replacement + original[z:]
f.write_text(s)
(p.parent / 'fetch-inline/fused.patch').write_text(''.join(difflib.unified_diff(
    original.splitlines(True), s.splitlines(True), fromfile='reference/custom.cpp', tofile='candidate/custom.cpp')))
