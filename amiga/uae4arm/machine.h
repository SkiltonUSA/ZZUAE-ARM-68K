#pragma once
#define UAE_BOOT_FRAMES 1800u
#define UAE_OPTIONS 0x482800u
#define UAE_FRAME 0x490000u
#define UAE_ROM 0x4e0000u
#define UAE_DISK 0x560000u
#define UAE_ROM_SIZE 262144u
#define UAE_ROM_CAPACITY 524288u
#if UAE_FRAME + 640*256*2 > UAE_ROM || UAE_ROM + UAE_ROM_CAPACITY > UAE_DISK || UAE_DISK + 901120 > 0x640000
#error Media layout overlaps
#endif
#define UAE_DISK_SIZE 901120u
#ifndef __ASSEMBLER__
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
extern volatile uint8_t *uae_shared;
extern int (*uae_stop)(void);
extern unsigned uae_frame_limit;
extern unsigned uae_input_mode;
extern int uae_volatile_write;
void zzuae_test_button(unsigned,int);
void zzuae_shared(volatile uint8_t *);
void zzuae_cpu_reset(void);
unsigned zzuae_step(void);
#ifdef __cplusplus
}
#endif
#endif
