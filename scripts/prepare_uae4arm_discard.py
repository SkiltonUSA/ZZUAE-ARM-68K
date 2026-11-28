"""Opt-in OCS/ECS display-record pruning. Guest DMA/timing remain active.

Apply to the pinned, prepared core only. --discard-records requires early drawing
selection. AGA and collision-enabled rendering keep the complete recording path.
"""


def discard_recording(custom, draw):
    s=draw.replace('static bool zu_draw_decided,zu_draw_selected;','bool zu_discard_pixels;\nstatic bool zu_draw_decided,zu_draw_selected;').replace('zu_draw_decided=true;','zu_draw_decided=true;zu_discard_pixels=!zu_draw_selected;').replace('zu_draw_decided=false;','zu_draw_decided=false;zu_discard_pixels=false;')
    draw=s
    s=custom
    s=s.replace('STATIC_INLINE void toscr_3_ecs (int nbits)\n{','extern bool zu_discard_pixels;\nstatic inline bool discard_ecs_pixels(){return zu_discard_pixels && !currprefs.collision_level && !aga_mode;}\nSTATIC_INLINE void toscr_3_ecs (int nbits)\n{\n if(discard_ecs_pixels())return;')
    needle='''    for (i = 0; i < thisline_decision.nr_planes; i++) {'''
    assert s.count(needle)==1;s=s.replace(needle,'    if(fm!=0 || !discard_ecs_pixels())\n'+needle)
    a=s.index('STATIC_INLINE void long_fetch_16 (');z=s.index('STATIC_INLINE void long_fetch_32 (',a)
    t=s[a:z];needle='  shiftbuffer = todisplay[plane][0];';assert needle in t
    t=t.replace(needle,'''  /* Pixels are dead for this entire skipped frame. Keep the final DMA
   * word and pointers; cycle scheduling and fetch metadata stay unchanged.
   * pfield_xlateptr supplies ordinary Chip RAM, never an I/O callback. */
  if(nwords>0 && discard_ecs_pixels()){
    if(dma)fetched[plane]=do_get_mem_word(real_pt+nwords-1);
    return;
  }
'''+needle)
    s=s[:a]+t+s[z:]
    a=s.index('static void decide_sprites(int spnr, int hpos, bool quick)');z=s.index('STATIC_INLINE void decide_sprites(int spnr, int hpos)',a)
    t=s[a:z].replace('    calcsprite ();','    if(discard_ecs_pixels()){last_sprite_point=point;return;}\n    calcsprite ();').replace('\tcount = 0;','\tif(discard_ecs_pixels()){last_sprite_point=point;return;}\n\tcount = 0;')
    s=s[:a]+t+s[z:]
    a=s.index('static void record_color_change (');z=s.index('static bool isbrdblank',a)
    t=s[a:z].replace('\tif (thisline_decision.ctable < 0)', '\tif(discard_ecs_pixels())return;\n\tif (thisline_decision.ctable < 0)')
    s=s[:a]+t+s[z:]
    a=s.index('STATIC_INLINE void finish_decisions (void)');z=s.index('static void reset_decisions (void)',a)
    t=s[a:z];start=t.index('\tdip = curr_drawinfo + next_lineno;');end=t.index('\tdiw_hcounter +=',start)
    t=t[:start]+'\tif(!discard_ecs_pixels()){\n'+t[start:end]+'\t}\n'+t[end:]
    s=s[:a]+t+s[z:]
    s=s.replace('    hsync_record_line_state (next_lineno);','    if(!discard_ecs_pixels())hsync_record_line_state (next_lineno);')
    needle='static void hsync_handler_pre (bool onvsync)\n{'
    assert needle in s
    s=s.replace(needle,'extern void zu_prepare_drawing();\n'+needle+'\n if(vpos==1)zu_prepare_drawing();')
    draw=draw.replace('    return zu_draw_selected;\n}', '    return zu_draw_selected;\n}\nvoid zu_prepare_drawing(){zu_draw_frame();}')
    return s,draw
