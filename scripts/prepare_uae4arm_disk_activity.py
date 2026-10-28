"""Report actual DF0/DF1 read bursts without changing guest disk timing."""
def disk_activity(source):
    replacements={
        'static void DISK_start (void)\n{':
            'static void DISK_start (void)\n{\n zz_read_words=0;',
        '\t\t\tv = fifo[i];':
            '\t\t\tv = fifo[i];\n'
            '            if(dskdmaen==DSKDMA_READ && ((selected|disabled)&3)!=3 && !(zz_read_words++&255u))\n'
            '                gui_flicker_led(LED_DF0,(selected&1)?1:0,1);',
        '\t        while (dsklength-- > 0) {':
            '\t        if(dr<2 && dsklength>0)gui_flicker_led(LED_DF0,dr,1);\n'
            '\t        while (dsklength-- > 0) {'}
    for old,new in replacements.items():
        assert source.count(old)==1,old
        source=source.replace(old,new)
    return 'static unsigned zz_read_words;\n'+source
