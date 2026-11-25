#pragma once
#include "machine.h"
#include "profiles.h"
#define UAE_PICTURE_UP (UAE_OPTIONS+148u)
static inline unsigned zu_picture_offset(unsigned profile,unsigned ntsc,unsigned up){
 return (profile==ZP_A1200&&!ntsc?18u:0u)+up;
}
