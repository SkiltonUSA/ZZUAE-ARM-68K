"""Select upstream MOVW/MOVT for LOAD_U32 without other ARMV6T2 changes."""

def movw_constants(source, header):
    start = source.index('STATIC_INLINE void LOAD_U32(')
    end = source.index('\n}', start) + 2
    function = source[start:end]
    prefix, choices = function.split('#ifdef ARMV6T2\n', 1)
    wide, _ = choices.split('#else', 1)
    source = source[:start] + prefix + wide + '}' + source[end:]
    names = ('CC_MOVW_ri16', 'MOVW_ri16', 'CC_MOVT_ri16', 'MOVT_ri16')
    macros = [next(line for line in header.splitlines()
                   if line.startswith('#define ' + name + '(')) for name in names]
    header = '#ifndef ARMV6T2\n' + '\n'.join(macros) + '\n#endif\n' + header
    return source, header
