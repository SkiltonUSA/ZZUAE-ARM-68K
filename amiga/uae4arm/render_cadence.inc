/* Drawing cadence only. Chipset/Paula keep the selected PAL/NTSC clock. */
static bool zu_render_due(unsigned rate,unsigned &phase,unsigned hz=50){
    if(!rate || rate>=hz)return true;
    phase+=rate;
    if(phase<hz)return false;
    phase-=hz;
    return true;
}
