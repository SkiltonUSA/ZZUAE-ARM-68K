#pragma once
/* Single-worker port: blocking/thread requests are unsupported, never faked. */
typedef int uae_sem_t;
typedef void *uae_thread_id;
#define BAD_THREAD 0
static inline int uae_sem_init(uae_sem_t *s,int,int value){*s=value;return 0;}
static inline void uae_sem_destroy(uae_sem_t *s){*s=0;}
static inline void uae_sem_post(uae_sem_t *s){++*s;}
static inline void uae_sem_wait(uae_sem_t *s){if(*s<=0)abort();--*s;}
static inline int uae_sem_trywait(uae_sem_t *s){if(*s<=0)return -1;--*s;return 0;}
static inline int uae_sem_getvalue(uae_sem_t *s){return *s;}
static inline void uae_set_thread_priority(uae_thread_id*,int){}
static inline long uae_start_thread(const TCHAR*,int(*)(void*),void*,uae_thread_id*){abort();return 0;}
static inline long uae_start_thread_fast(void*(*)(void*),void*,uae_thread_id*){abort();return 0;}
static inline void uae_wait_thread(uae_thread_id){abort();}
#define UAE_THREAD_EXIT do {} while(0)
#include "commpipe.h"
