#pragma once
#include "audio_wire.h"
#include "protocol.h"
int ua_audio_host_rate(unsigned rate);
int ua_audio_host_open(volatile uint8_t*,const struct ad_io*,unsigned);
int ua_audio_host_service(void);
int ua_audio_host_pending(void);
int ua_audio_host_close(void);
/* Main task, only while the ARM producer is held at a frame checkpoint. */
int ua_audio_host_pause_drain(void);

#ifdef ZZUAE_AUDIO_DIAGNOSTIC
void ua_audio_host_report(void);
#endif
