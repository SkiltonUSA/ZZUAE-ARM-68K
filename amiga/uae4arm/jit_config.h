#pragma once
/* Build-time experiments retain the normal 512 KiB cache / 32 MiB runtime. */
#ifndef ZU_JIT_CACHE_KIB
#define ZU_JIT_CACHE_KIB 512
#endif
#ifndef ZU_ALLOCATION_SIZE
#define ZU_ALLOCATION_SIZE 0x2000000u
#endif
/* Keep the original extra 128 KiB gap ahead of the linker's stack reserve. */
#define ZU_STACK_RESERVE 0x50000u
#ifndef ZU_JIT_TRACE_INSTRUCTIONS
#define ZU_JIT_TRACE_INSTRUCTIONS 32
#endif
#if ZU_JIT_CACHE_KIB != 512 && ZU_JIT_CACHE_KIB != 32768
#error Unsupported experimental JIT cache size
#endif
#if ZU_JIT_CACHE_KIB == 32768 && ZU_ALLOCATION_SIZE != 0x4000000u
#error The 32 MiB cache requires the 64 MiB runtime allocation
#endif
