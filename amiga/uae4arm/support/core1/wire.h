#pragma once
#include "protocol.h"
#include "layout.h"
#define MB_HOST (ZZ_CONTROL+0x800)
#define MB_REPLY (ZZ_CONTROL+0x900)
enum { MB_SEQ=0, MB_OP=4 };
enum { MB_ACK=0, MB_ERROR=4, MB_LO=8, MB_HI=12, MB_RESULT=16 };
enum { MB_CLOCK=1, MB_VERIFY=2, MB_BENCH=3, MB_CANCEL=4 };
