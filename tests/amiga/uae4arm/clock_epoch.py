#!/usr/bin/env python3
"""A fresh guest must stop at the same point regardless of board uptime."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[3]
elf=Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory(prefix='uae-clock-') as temporary:
    reports=[]
    for uptime in ['0','0x80000100']:
        report=Path(temporary)/(uptime+'.json')
        subprocess.run([sys.executable,ROOT/'tests/amiga/uae4arm/check_machine.py','3',
                        '--profile','1','--synthetic-rom','--timer-us',uptime,
                        '--state-report',report,'--elf',elf],check=True,stdout=subprocess.DEVNULL)
        reports.append(json.loads(report.read_text()))
    assert reports[0]==reports[1],'Board uptime changed guest execution'
print('PASS initial clock epoch: identical CPU, RAM and pixels across uptime high-bit boundary')
