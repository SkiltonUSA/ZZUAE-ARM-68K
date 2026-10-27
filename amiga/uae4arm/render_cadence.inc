/* PAL chipset/Paula still execute at 50 Hz. This chooses drawing only. */
static bool zu_render_due(unsigned rate,unsigned &phase){
    if(!rate || rate>=50)return true;
    phase+=rate;
    if(phase<50)return false;
    phase-=50;
    return true;
}
