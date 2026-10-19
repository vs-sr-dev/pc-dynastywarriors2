# TODO — session 6

Where session 5 left the game ([13-title](13-title.md)): it boots, plays
its movies (Start skips them), shows its title screen and menu with its
three crystals, takes the host's keyboard, gamepad or a script; but on the
menu it makes a frame every four seconds or so, because the GS model takes
a whole field to redraw what the vblank handler sends again every field.

1. **The GS's speed.** About 350 000 pixels a field must take a few
   milliseconds, not twenty: decode the registers once per primitive (not
   per pixel in `put`), keep the frame and Z buffer formats' fast paths,
   look at the bilinear sampler and the CLUT reads; measure pixels per
   second on the menu (the heartbeat's GS count) and the game's frame
   counter (`PS2KIT_WATCH=3E55B4`, `_gp - 0x64BC`). Then perhaps the GS on
   its own thread, as on the console; the ordering with SIGNAL, FINISH and
   the PCRTC's picture must stay as it is. Then cross on the menu, and
   what follows it.
2. **VU1.** The demo and the game itself are VIF1 and VU1:
   UNPACK in the formats the census lists (with STCYCL's write masking,
   STMOD, STMASK, STROW/STCOL), OFFSET/BASE double buffering (TOPS, ITOP),
   MSCAL/MSCALF/MSCNT; VU1's 16 KB data memory and micro memory, the EFU (P:
   ESIN, EATAN, ERSQRT, ...) and XGKICK into GIF path 1. `vu0.cpp`'s
   interpreter is the start (VU1 adds the EFU, XGKICK, the larger memories);
   its pipeline-timing check matters more here, since VU1 code is often
   scheduled tightly. The 13 MPGs uploaded at start-up can be listed from
   the VIF1 DMA chain like VIF0's (`ps2kit.vu --dma`).
3. **How to check VU1.** The VU0 check had an oracle in the mathematics; for
   VU1 the outputs are GS packets. Ideas: compare the GIF packets of one
   frame with PCSX2's (its GS dump), and the pictures with PCSX2's at the
   same moment (point 5).
4. **The GS, the rest.** The Z formats' and PSMCT16S's own block layouts,
   CSM2 CLUTs, CLUT loading as the GS does it (CLD), local-to-host
   transfers, mipmaps.
5. **A PCSX2 trace of the same boot**, still to do: the order of the IOP
   commands and RPC calls, the PCRTC registers, screenshots at the same
   moments (the title menu's crystals are a good first comparison:
   translucency and draw order).
6. **Sound (phase 5).** Koei's two IOP drivers (KESSOUND, KOEIADS); an SPU2
   model; check by ear.
7. **The memory card with data**: a formatted card kept as host files, for
   saving and loading.

Open points:
* The keyboard and gamepad paths were written but only the scripted presses
  were exercised (headless); to try in the window.
* `--press` times are host seconds, and the boot's length depends on the
  host's load: a script that works on an idle machine can miss on a busy one.
  Times in vertical blanks would be steadier.
* VU0: overflow and underflow flags are not modelled; micro programs run at
  once, so an EE that changed VU0 registers while a program ran would see
  a difference (DW2 does not).
* From session 4: the IPU's IDCT and CSC rounding are not the hardware's
  (the movies match ffmpeg within 4 levels); the GS samples pixels at
  integer coordinates with a top-left rule; the KOEIADS playback clock and
  the stream's infinitely fast drive.
* From session 3: FIELD changes three lines after the vblank interrupt is
  taken (a choice); the DualShock 2's actuator answers; Deci2's TTY never
  printed.
* From session 2: the FPU/VU model's last-bit differences and exponent 255;
  operations no test exercises (`qmfc2.i`, `sqrt.s`, `viadd`, `vmtir`,
  `vmax`, `vmini`, `vrsqrt`, a few VU0 forms, `divu1`/`mflo1`).

Restarting: work on ps2kit in its own checkout beside this repository and
run its Python tools from the directory that holds that checkout (from this
repository's root, `python -m ps2kit` finds the pinned submodule instead).
Regenerate with `python -m ps2kit.recomp pc-dynastywarriors2/build/disc/SLES_500.57
--out pc-dynastywarriors2/build/recomp`, build with `ninja -C
build/recomp-build ps2run linkcheck difftest` (MSYS2 MinGW 64-bit: clang,
cmake, ninja, SDL3), test as in [09-recompiler](09-recompiler.md), run as in
[13-title](13-title.md). Don't time runs while something heavy (a
differential test) runs beside them.
