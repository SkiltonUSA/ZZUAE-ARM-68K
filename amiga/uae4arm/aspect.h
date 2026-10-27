/* 4:3 presentation of the fixed 640x256 PAL source; no guest timing changes. */
#pragma once
static inline int ul_view_valid(unsigned width,unsigned height){
    return width>=320 && width<=640 && height>=240 && height<=480 && width*3==height*4;
}
static inline int ul_view_size(unsigned available_width,unsigned available_height,unsigned *width,unsigned *height){
    unsigned unit=available_width/4;
    if(unit>available_height/3)unit=available_height/3;
    if(unit>160)unit=160;
    if(unit<80)return 0;
    *width=unit*4;*height=unit*3;return 1;
}
/* Exact nearest-neighbour indices without division in the pixel loop. */
static inline void ul_scale_map(unsigned short *map,unsigned count,unsigned source){
    unsigned i,position=0,phase=0;
    for(i=0;i<count;i++){
        map[i]=position;phase+=source;
        while(phase>=count){phase-=count;position++;}
    }
}
static inline int ul_mouse_scale(int delta,unsigned source,unsigned displayed,int *remainder){
    int total=delta*(int)source+*remainder,step=total/(int)displayed;
    *remainder=total-step*(int)displayed;return step;
}
