#include "frame_pacing.h"
#include <assert.h>
#include <stdio.h>
int main(void) {
    assert(!zu_frame_due(39999,0,40000));
    assert(zu_frame_due(40000,0,40000));
    assert(!zu_frame_due(33333,0,33334));
    assert(zu_frame_due(33334,0,33334));
    assert(zu_frame_due(10,10,0));
    assert(!zu_frame_due(10000,UINT32_MAX-19999,40000));
    assert(zu_frame_due(20000,UINT32_MAX-19999,40000));
    assert(zu_run_timeout(3000,40000)==150000000);
    assert(zu_run_timeout(6000,40000)==270000000);
    assert(zu_run_timeout(3000,0)==120000000);
    assert(zu_run_timeout(0,20000)==0);
    assert(zu_request_wait(300000000,0,0,0,0));
    assert(!zu_request_wait(150000001,0,150000000,0,0));
    assert(zu_request_wait(400000001,0,0,1,400000000));
    assert(!zu_request_wait(405000000,0,0,1,400000000));
    assert(zu_request_wait(99,0,0,1,UINT32_MAX-100));
    assert(!zu_request_wait(5000000,0,0,1,UINT32_MAX-100));
    puts("PASS: 25/30/MAX pacing, clock wrap and bounded-run timeout");
}
