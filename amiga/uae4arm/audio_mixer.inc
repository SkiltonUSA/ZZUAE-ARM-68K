/* Included in pinned upstream audio.cpp. Initial port deliberately selects the
 * integer stereo mixer, without floating-point filters or interpolation. */
extern "C" void zzuae_audio_init(void) {
    sample_handler=sample16s_handler;
    sample_prehandler=NULL;
    put_sound_word_stereo_func=put_sound_word_stereo_func_nofilter_notmixed;
    for(int i=0;i<AUDIO_CHANNELS_PAULA;i++)audio_data[i]=&audio_channel[i].data;
    audio_activate();
}
