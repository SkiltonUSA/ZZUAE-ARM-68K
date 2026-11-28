#pragma once
/* Host commands and ARM replies use separate cache lines in uncached control RAM.
 * Commands are serviced only while a published frame awaits grant/ack. */
#define UM_CONTROL 0x483200u
#define UM_REQUEST (UM_CONTROL+0u)
#define UM_OPERATION (UM_CONTROL+4u)
#define UM_UNIT (UM_CONTROL+8u)
#define UM_REPLY (UM_CONTROL+64u)
#define UM_RESULT (UM_CONTROL+68u)
#define UM_CAPS (UM_CONTROL+72u)
#define UM_MAGIC 0x5a554d31u
#define UM_EJECT 1u
#define UM_INSERT 2u
#define UM_OK 1u
#define UM_BUSY 2u
#define UM_INVALID 3u
static inline int zu_disk_command_valid(unsigned op,unsigned unit){
    return unit<2 && (op==UM_EJECT || op==UM_INSERT);
}
