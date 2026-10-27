/* Drawing only: leave framecnt and chipset recording untouched. Lazy choice
 * on the first partial draw avoids consuming cadence during reset/init. */
#ifdef ZZUAE_EARLY_DRAW
extern "C" bool zzuae_live_draw_frame(void);
static bool zu_draw_decided,zu_draw_selected;
static bool zu_draw_frame(){
    if(!zu_draw_decided){
        zu_draw_selected=zzuae_live_draw_frame();
        zu_draw_decided=true;
    }
    return zu_draw_selected;
}
#endif
