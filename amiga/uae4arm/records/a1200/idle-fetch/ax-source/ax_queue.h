/* GPL-3.0-or-later. Three immutable PCM buffers plus permanent silence (sound 3).
 * Task fills only a free buffer and publishes with interrupts disabled.
 * SoundFunc alone advances playback and retires the PREVIOUS sound. A start
 * notification is not completion of the sound that has just started. */
#ifndef ZZ_AX_QUEUE_H
#define ZZ_AX_QUEUE_H
struct ax_queue {
 volatile unsigned occupied[3], ready[3], count[3], write, read, completed, callbacks, silence, starvations, draining;
 volatile int current, scheduled;
};
static void ax_init(struct ax_queue *q){
 unsigned i;for(i=0;i<3;i++)q->occupied[i]=q->ready[i]=q->count[i]=0;
 q->write=q->read=q->completed=q->callbacks=q->silence=q->starvations=q->draining=0;
 q->current=-1;q->scheduled=3;
}
static int ax_free(const struct ax_queue *q){unsigned i=q->write;return q->occupied[i]?-1:(int)i;}
static void ax_publish(struct ax_queue *q,unsigned frames){
 unsigned i=q->write;q->count[i]=frames;q->occupied[i]=q->ready[i]=1;q->write=(i+1)%3u;
}
static int ax_started(struct ax_queue *q){
 unsigned i=q->read;
 if(q->current>=0 && q->current<3){q->completed+=q->count[q->current];q->occupied[q->current]=0;}
 q->current=q->scheduled;q->callbacks++;
 if(q->ready[i]){q->ready[i]=0;q->scheduled=(int)i;q->read=(i+1)%3u;}
 else{q->scheduled=3;q->silence++;if(q->current>=0&&q->current<3&&!q->draining)q->starvations++;}
 return q->scheduled;
}
static int ax_idle(const struct ax_queue *q){return !q->occupied[0]&&!q->occupied[1]&&!q->occupied[2];}
#endif
