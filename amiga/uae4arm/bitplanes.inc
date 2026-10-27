/* Opt-in OCS/ECS bitplane transpose experiment. The scalar path remains
 * available when XACP's existing NEON access policy does not permit use. */
#ifdef ZZUAE_NEON_BITPLANES
extern "C" unsigned zu_neon_available(void);
extern "C" void zu_bitplane_neon(void*,unsigned,const void*,unsigned);
static bool zu_bitplanes_ready;
unsigned zu_bitplanes_neon_rows,zu_bitplanes_scalar_rows;
#endif
