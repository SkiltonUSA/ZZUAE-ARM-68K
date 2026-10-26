/* Physical Amiga port 2 -> guest joystick 2; keyboard and stick are ORed. */
#pragma once
#include <stdint.h>
static inline unsigned uj_merge(unsigned keys,unsigned stick){return (keys|stick)&127u;}
#if defined(__amigaos__) || defined(__AMIGA__) || defined(__mc68000__)
#include <libraries/lowlevel.h>
#include <proto/lowlevel.h>
static inline unsigned uj_sample(ULONG state){
 ULONG type=state&JP_TYPE_MASK;
 if(type!=JP_TYPE_JOYSTK && type!=JP_TYPE_GAMECTLR)return 0;
 return ((state&JPF_JOY_RIGHT)?1:0)|((state&JPF_JOY_LEFT)?2:0)|
        ((state&JPF_JOY_UP)?4:0)|((state&JPF_JOY_DOWN)?8:0)|((state&JPF_BUTTON_RED)?16:0)|
        ((state&JPF_BUTTON_BLUE)?32:0)|
        ((type==JP_TYPE_GAMECTLR && (state&JPF_BUTTON_GREEN))?64:0);
}
#endif
