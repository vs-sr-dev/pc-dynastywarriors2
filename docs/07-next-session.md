# TODO — session 5

Where session 4 left the game ([12-movies](12-movies.md)): it boots, finds no
memory card, and plays its logo movies through ps2kit's IPU and GS models
in a window, at 25 frames a second. The repositories were published at that
checkpoint.

1. **After the movies.** The logos and the opening play (two minutes of a
   run, no stop); see where the game goes after the opening and what stops
   it: the title screen (a TITLE movie exists too) is the next picture to
   aim at.
2. **Input.** The DualShock 2 on port 0 never has a button down: the
   title screen will wait for Start. SDL3 keyboard and gamepad events into
   padman's per-vblank frames (`iop.cpp`, `pad_vblank`), with a default
   mapping; for runs without a window, a scripted input (`--press T:START`).
3. **VIF1 and VU1.** DMA to VIF1 is counted, not run. The 3D (and probably
   the title's 2D overlays) go through VIF1 packets, VU1 microprograms and
   XGKICK (GIF path 1); ps2kit has `vif.py` and `vu.py` in Python as a start.
   VIF1 DIRECT/DIRECTHL is GIF path 2.
4. **The GS, the rest.** The Z formats' and PSMCT16S's own block layouts,
   CSM2 CLUTs, CLUT loading as the GS does it (CLD), local-to-host
   transfers, mipmaps; each said once when a game first uses it.
5. **Sound (phase 5).** Koei's two IOP drivers (KESSOUND, KOEIADS) answer
   from a stand-in; the movies' ADPCM reaches the IOP and goes nowhere. Port
   their logic from their code; an SPU2 model; check by ear.
6. **A PCSX2 trace of the same boot**, still to do: the order of the IOP
   commands and RPC calls, the PCRTC registers, a few screenshots at the
   same moments.
7. **The memory card with data**: a formatted card kept as host files, for
   saving and loading.

Open points:
* The IPU's IDCT and CSC rounding are not the hardware's (unknown); the
  movies match ffmpeg within 4 levels.
* The GS samples pixels at integer coordinates with a top-left rule: to
  check against PCSX2 when 3D arrives.
* The KOEIADS playback clock and the stream's infinitely fast drive are
  stand-ins for timing.
* From session 3: FIELD changes three lines after the vblank interrupt is
  taken (a choice); the DualShock 2's actuator answers; Deci2's TTY never
  printed.
* From session 2: the FPU/VU model's last-bit differences and exponent 255;
  operations no test exercises (`qmfc2.i`, `sqrt.s`, `viadd`, `vmtir`, a few
  VU0 forms, `divu1`/`mflo1`).

Restarting: work on ps2kit in its own checkout beside this repository and
run its Python tools from the directory that holds that checkout (from this
repository's root, `python -m ps2kit` finds the pinned submodule instead).
Regenerate with `python -m ps2kit.recomp pc-dynastywarriors2/build/disc/SLES_500.57
--out pc-dynastywarriors2/build/recomp`, build with `ninja -C
build/recomp-build ps2run linkcheck difftest` (MSYS2 MinGW 64-bit: clang,
cmake, ninja, SDL3), test as in [09-recompiler](09-recompiler.md), run as in
[12-movies](12-movies.md). Debugging the IPU: `PS2KIT_IPU_BITLOG`,
`PS2KIT_IPU_DUMP`, `PS2KIT_IPU_CMDLOG` (see `runtime/ipu.cpp`).
