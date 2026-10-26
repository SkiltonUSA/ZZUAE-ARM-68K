# Verification

The three-button input checks passed natively and in the ARM instruction model.
The installed 0.4.1-dev build completed a physical 120-guest-frame AHI boot:
60 displayed frames, audio error 0, exit 0, restored register/MMU/cache state
and released memory. One audio queue gap was recorded; the boot PCM was silent.
This does not establish audible quality or physical controller acceptance.

The accompanying newest build manifests describe subsequent version-metadata
and launcher wording rebuilds. These changes did not alter emulation code;
the hardware log belongs to the preceding 0.4.1-dev artifact and is not presented
as a run of the newer hashes. Framework logs were produced in the parent workspace.

Screenshots: launcher and tester are 0.4.1-dev; Alien Syndrome live title and
Badlands bounded title capture are from the earlier physical prototype runs.
Badlands reached its instruction bound at frame 1713; it is not a completed
1800-frame or gameplay test. Workbench 2.0 is from the 0.3.0 profile tests.
