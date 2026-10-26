#include "exception.h"
#include <assert.h>
jmp_buf *zzuae_exception;
void zzuae_throw(int n){assert(zzuae_exception);longjmp(*zzuae_exception,n);}
int main(){
 volatile int result=0;
 TRY(outer) {
   TRY(inner) { THROW(7); } CATCH(inner) { result=inner;THROW(2); } ENDTRY
 } CATCH(outer) { result+=outer; } ENDTRY
 assert(result==9 && !zzuae_exception);
}
