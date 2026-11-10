"""Pinned Cyclone generator adaptation for UAE's big-endian instruction memory.

Data callbacks retain their ordinary numeric 68000 semantics. Only instruction
fetches change; no mirrored RAM or stale self-modifying-code cache is introduced.
"""
import re

def movem_address_error(folder):
    """Restore the saved instruction PC before MOVEM's odd-address exception.

    r4 has already become a context register pointer at this point. Passing it
    to the shared exception handler would put a host-relative value on the
    guest stack. FlushPC(1) immediately above saved the real instruction PC.
    """
    path=folder/'OpMove.cpp';s=path.read_text()
    old='  ot("  bne ExceptionAddressError_%c_data\\n",dir?\'r\':\'w\');'
    assert s.count(old)==1
    s=s.replace(old,'  ot("  ldrne r4,[r7,#0x40] ;@ restore PC before address error\\n");\n'+old)
    path.write_text(s)

def big_endian_fetches(folder):
    counts={}
    for name in ('Main.cpp','Ea.cpp','OpAny.cpp','OpBranch.cpp','OpMove.cpp'):
        path=folder/name;s=path.read_text();result=[];count=0
        for line in s.splitlines(keepends=True):
            result.append(line)
            m=re.search(r'ot\("  ldr(sh|h) (r\d+|r%d),\[r4(?:\]|,)',line)
            if not m:continue
            if name=='Main.cpp' and 'Fetch' not in line:continue
            if name=='OpMove.cpp' and not ('register mask' in line or 'Fetch the immediate' in line):continue
            reg=m[2];extra=',a' if reg=='r%d' else ''
            result.append('    ot("  '+('revsh' if m[1]=='sh' else 'rev16')+' '+reg+','+reg+' ;@ UAE big-endian fetch\\n"'+(',a,a' if extra else '')+');\n')
            count+=1
        s=''.join(result)
        if name=='Ea.cpp':
            old='      ot("  ldr%s r%d,[r4],#2 ;@ Fetch immediate value\\n",suffix,a); pc_dirty=1;'
            assert s.count(old)==1
            s=s.replace(old,'''      if (size == 0) {
        ot("  ldr%s r%d,[r4,#1] ;@ UAE immediate byte\\n",suffix,a);
        ot("  add r4,r4,#2\\n");
      } else {
        ot("  ldrh r%d,[r4],#2\\n",a);
        ot("  %s r%d,r%d ;@ UAE immediate word\\n",type==earwt_zero_extend?"rev16":"revsh",a,a);
      }
      pc_dirty=1;''')
        if name=='OpBranch.cpp':
            old='    ot(UAL(ldr,sh,hs) "r0,[r4]\\n");'
            assert s.count(old)==1
            s=s.replace(old,old+'\n    ot("  revshhs r0,r0 ;@ UAE conditional branch extension\\n");')
        path.write_text(s);counts[name]=count
    assert counts=={'Main.cpp':5,'Ea.cpp':9,'OpAny.cpp':2,'OpBranch.cpp':4,'OpMove.cpp':2},counts
    return counts
