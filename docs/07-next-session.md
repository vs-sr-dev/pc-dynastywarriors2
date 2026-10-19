# TODO — session 7

Where session 6 left the game ([14-gs-speed](14-gs-speed.md)): it boots,
plays its movies, shows its title menu at full speed (50 frames a second),
and cross on MUSOU MODE opens the character select: the title, the
spotlight, Zhao Yun's portrait and bars. The character's model is missing:
from that screen on, the census counts VU1's codes (MSCAL, UNPACK V4-32,
STCYCL, OFFSET, BASE). Left alone, the menu goes to the demo, which is VU1's
too (vertical stripes on screen now).

1. **VU1, with the character select as its first picture.** One model, a
   still camera, a known screen around it: the smallest VU1 case the game
   offers. VIF1: UNPACK in the formats the census lists (with STCYCL's
   write masking, STMOD, STMASK, STROW/STCOL), OFFSET/BASE double
   buffering (TOPS, ITOP), MSCAL/MSCALF/MSCNT; VU1's 16 KB data memory and
   micro memory, the EFU (P: ESIN, EATAN, ERSQRT, ...) and XGKICK into GIF
   path 1 (through the GS thread's queue, like paths 2 and 3). `vu0.cpp`'s
   interpreter is the start; its pipeline-timing check matters more here,
   since VU1 code is often scheduled tightly. The 13 MPGs uploaded at
   start-up can be listed from the VIF1 DMA chain (`ps2kit.vu --dma`).
2. **How to check VU1.** VU0 had an oracle in the mathematics; VU1's
   outputs are GS packets. Ideas: PCSX2's GS dump of the same screen, its
   GIF packets against ours; our own recording (`PS2KIT_GS_DUMP`) makes the
   packet side easy to compare.
3. **A PCSX2 trace of the same boot**, still to do: the order of the IOP
   commands and RPC calls, the PCRTC registers, screenshots at the same
   moments (the title menu's crystals: translucency and draw order). One
   question for it now: how the console's kernel leaves VBON in INTC_STAT
   for the SDK's VSync to see while the interrupt is enabled (Koei's movie
   player depends on it; [14-gs-speed](14-gs-speed.md)).
4. **The GS, the rest.** The Z formats' and PSMCT16S's own block layouts,
   CSM2 CLUTs, CLUT loading as the GS does it (CLD, at TEX0), mipmaps; the
   PCRTC's merge of its two read circuits (DW2 turns both on at times; only
   circuit 2 is shown); a check of local-to-host transfers on the moment
   that uses them. Each in both rasterisers, checked with
   `gsreplay --compare`. If the game's 3D scenes are heavier than the menu
   (10 ms a field now on one core), rows spread over several threads.
5. **Sound (phase 5).** Koei's two IOP drivers (KESSOUND, KOEIADS); an SPU2
   model; check by ear.
6. **The memory card with data**: a formatted card kept as host files, for
   saving and loading.

Open points:
* Keyboard and an Xbox pad were tried by the user in session 6: menus,
  character select and a battle work (without VU1's models).
* Deinterlacing is blend by default; whether battles look better with
  weave is for the user's eye (`PS2KIT_DEINTERLACE`).
* `--press` times are host seconds, and the boot's length depends on the
  host's load (and on how quickly the movies are skipped): times in
  vertical blanks would be steadier.
* GS recordings store the runtime's own structures behind a version
  (`GS_STATE_VERSION`): a change to them needs a new version and new
  recordings.
* The fast rasteriser reads the CLUT when a primitive starts, the
  reference at every texel: a primitive that drew over its own CLUT would
  make them differ (not seen).
* VU0: overflow and underflow flags are not modelled; micro programs run at
  once, so an EE that changed VU0 registers while a program ran would see
  a difference (DW2 does not).
* From session 4: the IPU's IDCT and CSC rounding are not the hardware's
  (the movies match ffmpeg within 4 levels); the GS samples pixels at
  integer coordinates with a top-left rule; the KOEIADS playback clock and
  the stream's infinitely fast drive.
* From session 3: FIELD changes three lines after the vblank interrupt is
  taken (a choice; since session 6 the guest's own acknowledgement counts
  as taken); the DualShock 2's actuator answers; Deci2's TTY never printed.
* From session 2: the FPU/VU model's last-bit differences and exponent 255;
  operations no test exercises (`qmfc2.i`, `sqrt.s`, `viadd`, `vmtir`,
  `vmax`, `vmini`, `vrsqrt`, a few VU0 forms, `divu1`/`mflo1`).

Restarting: work on ps2kit in its own checkout beside this repository and
run its Python tools from the directory that holds that checkout (from this
repository's root, `python -m ps2kit` finds the pinned submodule instead).
Regenerate with `python -m ps2kit.recomp pc-dynastywarriors2/build/disc/SLES_500.57
--out pc-dynastywarriors2/build/recomp`, build with `ninja -C
build/recomp-build ps2run gsreplay linkcheck difftest` (MSYS2 MinGW 64-bit:
clang, cmake, ninja, SDL3), test as in [09-recompiler](09-recompiler.md),
run as in [13-title](13-title.md) and [14-gs-speed](14-gs-speed.md).
Starting the run: Start every two seconds from 8 to 22 reaches the menu;
cross at 28 opens the character select. Don't time runs while something
heavy (a differential test) runs beside them.
