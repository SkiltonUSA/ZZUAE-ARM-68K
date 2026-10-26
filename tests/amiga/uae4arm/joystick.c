#include "joystick.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 assert(uj_merge(4,16)==20);
 assert(uj_merge(16,16)==16);
 assert(uj_merge(0,16)==16); /* keyboard release cannot release held stick fire */
 assert(uj_merge(4,0)==4);   /* stick release cannot release held keyboard Up */
 assert(uj_merge(0,0)==0);
 assert(uj_merge(0xff,0)==127);
 assert(uj_merge(16,32|64)==112);
 assert(uj_merge(0,64)==64);
 puts("PASS: independent keyboard/stick input merge and release semantics");
}
