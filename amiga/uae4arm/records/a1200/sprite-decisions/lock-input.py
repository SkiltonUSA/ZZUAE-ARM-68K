from pathlib import Path
import sys
p=Path('.context/amiga/uae4arm/a1200/gameplay');variant=sys.argv[1];hw=p/('build-'+variant)/'machine'
s=Path('amiga/uae4arm/live_host.h').read_text();a=s.index('static void live_input(unsigned kind,int value) {');z=s.index('\nstatic void live_joystick',a)
s=s[:a]+'''/* Bounded benchmark only: scripted guest inputs remain active; UI exit works. */
static void live_input(unsigned kind,int value) {(void)kind;(void)value;}
'''+s[z:]
(hw/'live_host.h').write_text(s)
exec(Path('.context/amiga/uae4arm/a1200/performance/extend-chipreads.py').read_text().replace("for variant in ('chipreads',):",f"for variant in ('{variant}',):").replace('a1200/performance/build-','a1200/gameplay/build-'))
