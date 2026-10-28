/* Single-producer frame and input mailboxes. All words are big-endian.
 * Pixels remain little-endian RGB565. ARM owns pixels until publication;
 * it must not replace them until the host acknowledges the sequence.
 * Separate cache lines keep host writes away from ARM-owned counters. */
#pragma once
#define UAE_LIVE 0x482c00u
#define UL_FRAME 0u
#define UL_TAIL 4u
#define UL_DONE 8u
#define UL_ERROR 12u
#define UL_NEON_ROWS 16u
#define UL_SCALAR_ROWS 20u
#define UL_SIMD_CHECKS 24u
#define UL_SIMD_ERRORS 28u
#define UL_DISK_ACTIVE 32u /* ARM-owned DF0 selected/motor/write indicator */
#define UL_DISK_READS 36u /* Two ARM-owned read-burst counters: DF0, DF1 */
#define UL_ACK 64u
#define UL_HEAD 68u
#define UL_GRANT 72u
#define UL_ADDRESS 76u
#define UL_PITCH 80u
#define UL_FORMAT 84u
#define UL_NONCE 88u
#define UL_SCAN_RESERVED 92u /* former software scanlines; ignored */
#define UL_CAPTURE 96u
#define UL_WIDTH 100u
#define UL_HEIGHT 104u
#define UL_EVENTS 256u
#define UL_CAPACITY 64u
#define UL_KEY 1u
#define UL_MOUSE_X 2u
#define UL_MOUSE_Y 3u
#define UL_LEFT 4u
#define UL_RIGHT 5u
#define UL_JOY 6u
#define UL_RESET_INPUT 7u
#define UAE_OPT_LIVE 8u
#define UAE_OPT_DIRECT 16u
#ifndef __ASSEMBLER__
#include <stdint.h>
static inline uint32_t ul_event(unsigned kind, int value) {
    return (kind << 16) | ((uint32_t)value & 65535u);
}
/* Unsigned subtraction intentionally handles counter wrap. */
static inline int ul_room(uint32_t head,uint32_t tail) {
    return (uint32_t)(head-tail)<UL_CAPACITY;
}
static inline int ul_mouse_half(int delta,int *remainder) {
    int total=delta+*remainder,step=total/2;
    *remainder=total-step*2;return step;
}
#endif
