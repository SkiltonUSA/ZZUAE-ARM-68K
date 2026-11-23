# Published source reconciliation

The 0.6.1 source archive included later RGB565 presentation, picture positioning,
compact controls, splash rendering and audio diagnostics that had not all reached
the canonical Git tree. It also contained uncommitted clock/menu controls and
supporting test sources. These published files have now been reconciled.

[The audit](release-source-audit.json) identifies the archive and every file by
SHA-256. A three-way comparison preserved the local pause/clock/hotkey changes.
Three adjacent-edit conflicts were reviewed: the audio report declaration,
compact joystick/scanline buttons and the replacement splash. Each resolves to
the already-published source. Original local files were backed up first.

This is source-history repair, not a new optimisation or player release. Installed
binaries and published release archives are unchanged. Other untracked experiment
records, including unpublished JSON measurements, remain preserved and outside
this commit; they are not claimed to be audited or release-ready.
