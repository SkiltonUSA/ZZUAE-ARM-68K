"""Add the runtime PCM-rate argument to recorded hosts without changing ARM code."""
def host_audio_rate(text):
    if 'ua_audio_host_rate(' in text:
        return text
    anchor='else if(!strcmp(argv[i],"AUDIO")'
    if text.count(anchor)!=1:
        raise ValueError('Expected one AUDIO argument in the recorded host')
    return text.replace(anchor,'''else if(!strcmp(argv[i],"RATE") && i+1<argc){
                const char *rate=argv[++i];
                if(strcmp(rate,"0") && strcmp(rate,"22050") && strcmp(rate,"27000"))return 20;
                if(!ua_audio_host_rate(!strcmp(rate,"0")?0:!strcmp(rate,"27000")?27000:22050))return 20;
            }
            '''+anchor,1)
