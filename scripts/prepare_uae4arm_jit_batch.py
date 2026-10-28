"""Reuse one guest exception context per bounded dispatcher call.

The in-flight cycle origin must survive longjmp. Dispatch counters live outside
that stack frame; the fault path accounts exactly once before resuming.
"""
def batch_context(source):
    loop=' while((*dispatches-start)<limit && (!uae_frame_limit || timeframes<uae_frame_limit) && !regs.halted) {'
    source=source.replace(' const unsigned start=*dispatches;',
                          ' const unsigned start=*dispatches;\n volatile unsigned before=0;')
    source=source.replace(loop,loop+'\n  TRY(fault) {\n'+loop)
    source=source.replace('  const unsigned before=get_cycles();\n  TRY(fault) {',
                          '  before=get_cycles();')
    source=source.replace('  } CATCH(fault) {bus_error();} ENDTRY\n','')
    tail='\n }\n}\n'
    assert source.endswith(tail)
    return source[:-len(tail)]+'''
 }
  } CATCH(fault) {
#ifdef ZZUAE_JIT_PROFILE
   zz_jit_service_active=false;
#endif
   bus_error();
   *cycles+=(get_cycles()-before)/(CYCLE_UNIT/2);++*dispatches;
  } ENDTRY
 }
}
'''
