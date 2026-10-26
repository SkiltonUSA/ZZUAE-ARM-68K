#pragma once
#include "audio_wire.h"
#include "protocol.h"
int ua_audio_host_open(volatile uint8_t*,const struct ad_io*,unsigned);
int ua_audio_host_service(void);
int ua_audio_host_pending(void);
int ua_audio_host_close(void);
