#include <cassert>
#define ZU_JIT_TRACE_INSTRUCTIONS 32
#define ZU_JIT_EVENT_BLOCKS 1
#define BI_ACTIVE 1
#define BI_NEED_CHECK 2
struct blockinfo {void *csi;int status;unsigned zz_group_cycles;};
struct {void *pc_p;} regs;
static unsigned zz_jit_metadata_live,zz_jit_metadata_flushes,lookups,checks;
static bool changed;
static blockinfo block,*entry;
static char arena[131072],*max_compile_start=arena+sizeof(arena),*current_compile_p;
static void flush_icache_hard(int){entry=nullptr;zz_jit_metadata_live=0;}
static blockinfo *get_blockinfo_addr(void*){++lookups;return entry;}
static void block_check_checksum(blockinfo *b){++checks;b->status=changed?0:BI_ACTIVE;}
#include "jit_validate.inc"
static unsigned prepare(){lookups=0;unsigned cycles=zzuae_jit_validate_current();assert(lookups==1);return cycles;}
int main(){
 assert(prepare()==0);
 block={nullptr,BI_ACTIVE,2048};entry=&block;
 assert(prepare()==2048 && checks==0);
 block.csi=&block;assert(prepare()==2048 && checks==1);
 changed=true;assert(prepare()==0 && checks==2);
 block.status=BI_ACTIVE;changed=false;zz_jit_metadata_live=2*1024*1024+1;
 assert(prepare()==0 && zz_jit_metadata_flushes==1);
 block={nullptr,BI_ACTIVE,0};entry=&block;assert(prepare()==0);
}
