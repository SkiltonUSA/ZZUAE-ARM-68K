# ZZUAE artwork

`zzuae-logo.png` is the transparent source master, generated with the built-in
image-generation tool. `scripts/prepare_uae4arm_art.py` compiles palette/planar
assets for the native MUI splash and 64-pixel Workbench ColorIcon. Generated
headers stay in the build directory; the source alpha channel is preserved.

Generation prompt:

> Create one polished retro Amiga emulator application icon for ZZUAE, also usable as the logo on its native AmigaOS splash screen. Square icon, one central compact emblem, bold simple shapes legible at 64 pixels: a classic beige Amiga 500 keyboard computer in a slight isometric view with a vivid red-and-white checkered Amiga-style sphere rising behind it. Deep blue outline and restrained highlights, crisp illustrated pixel-friendly edges, minimal fine details. The only lettering is large clean 'ZZUAE' along the bottom of the emblem, precisely spelled. No UI mockup, no wallpaper, no additional labels. Transparent background around the complete emblem. Balanced composition with generous transparent edge padding.
