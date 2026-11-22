/* GPL-3.0-or-later. PCM rate is separate from guest chip timing. */
#ifndef UA_AUDIO_RATE_H
#define UA_AUDIO_RATE_H
#define UA_PCM_DEFAULT 22050u
static inline int ua_pcm_valid(unsigned rate){return rate==0 || rate==27000 || rate==UA_PCM_DEFAULT;}
/* 0 selects the previous backend rate. Quantize Paula first, then use that
 * same period for both the producer rate and the audio.device request. */
static inline unsigned ua_pcm_period(unsigned clock,unsigned rate,unsigned original){
 return rate?(clock+rate/2)/rate:original;
}
#endif
