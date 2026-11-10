  // Exact dependency cache: no DMA, Copper or Denise update is skipped.
  struct DelayPlan {
    int con1, mask, size, start_mask, hstart, res, delay[2];
    bool valid;
  };
  static DelayPlan plan;
  if (plan.valid && plan.con1 == bplcon1 && plan.mask == fetchmode_mask
      && plan.size == fetchmode_size && plan.start_mask == fetchstart_mask
      && plan.hstart == bpl_hstart && plan.res == toscr_res) {
    toscr_delay[0] = plan.delay[0];
    toscr_delay[1] = plan.delay[1];
    return;
  }
