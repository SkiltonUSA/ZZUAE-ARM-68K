# Credits and licensing

- UAE and UAE4ARM: the original authors and contributors, including the
  [Chips-fr UAE4ARM port](https://github.com/Chips-fr/uae4arm-rpi), pinned in the
  build scripts. The scripts fetch that source and apply this port’s changes;
  upstream copyright and license notices remain in those files.
- [Xanxi / XACP-ZZ9000](https://github.com/Xanxi-Amiga/XACP-ZZ9000): framework and
  documented 68K/ARM execution model used by this project.
- ZZDosBox: software scanline brightness routines and native splash lifecycle.
- MUI, Picasso96 and AHI: native AmigaOS interface, graphics and audio facilities.
- Picolibc and GCC runtime: linked build dependencies. The binary package includes
  picolibc notices; the source bundle includes picolibc source. GCC runtime
  components retain their upstream runtime exception.
- Shared runtime source retains its existing per-file license notices, including
  GPL-3.0-or-later on the scalar memory routines. This backup does not relicense
  third-party components.

- AmiPkg: Thomas Luebker and contributors (Apache-2.0). The offline installer
  carries the local 0.7.11-zzinstall1 patch, notices and helper source.

Screenshots illustrate the emulator and its compatibility work. Game and
Workbench names, artwork and trademarks belong to their respective holders.
Kickstart ROMs and disk images are not distributed in this public repository.
