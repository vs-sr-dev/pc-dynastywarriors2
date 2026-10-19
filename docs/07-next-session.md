# TODO — session 8

Where session 7 left the game ([15-vu1](15-vu1.md)): VIF1 and VU1 work, on
a thread of their own. The character select runs at 50 frames a second with
its 3D officers (lit and textured with `PS2KIT_VU1_VF="30:0,0,255,0"`, black
without). The attract mode's battle draws, but one field in four or five the
game finds the frame's lists still running at the vertical blank and resets
the GS (a green field, a lost frame). The heartbeat prints VIF1's and the
GIF's start-to-end times: up to about 20 ms in a battle.

1. **The GS on several threads.** The plan worked out at the end of session
   7: the GS thread decodes registers and builds a job per triangle or
   sprite (the decoded `Draw`, the texture, copied vertices, a CLUT slot from
   a small pool); worker threads (`PS2KIT_GS_THREADS`, about 4) each draw the
   rows they own (strips of 8 rows). A barrier (all jobs done) before
   anything that reads or writes local memory outside the jobs: transfers in
   both directions, local-to-local, the reference rasteriser (points, lines,
   `--ref`), the PCRTC's picture, recordings, `gs_vram()`; a CLUT load or a
   texture whose blocks overlap what pending jobs write; a frame or Z target
   that overlaps another pending target. `put_fast` returns its pixel count
   instead of counting globally. Checked with `gsreplay --compare` (the
   result must equal the reference byte for byte) and timed on the battle
   recordings (8.5-12.5 ms a field on one thread now).
2. **VU1 faster.** 50-57 million pairs a second; a battle field needs about
   half a million, the character select more. The large step is a
   translator of VU1 microcode to C++ (ps2kit's way), with `vubench` and the
   interpreter as its oracle; the microcode comes from MPGs (13 at start-up,
   then about one a frame in battle: which programs, from where, to find
   first). Smaller: `ps2f` in the remaining paths, the MAC computation.
3. **vf30, a question for PCSX2 or a console.** The character select's fog
   factor reads vf30, which no program of the game writes before it. Does the
   character select show black officers in PCSX2 with a fast boot, and lit
   ones with a full BIOS boot (whose start-up animation runs on VU1)? Then
   the port needs to start VU1 as the BIOS leaves it, or the preset.
4. **The PCRTC's feedback blur** (`g_FeedBackPCRTC`, `g_SetBlurPCRTC` in
   `effctlow.cpp`): EXTBUF/EXTDATA/EXTWRITE write the read circuit's output
   back into local memory, and PMODE blends the two circuits (ALP 0xBE).
   Neither is modelled; battles turn it on.
5. **Battles look dark**: compare a battle field with PCSX2 (fog colour
   0x3C1400, F values) once the resets are gone.
6. **Sound (phase 5).** Koei's two IOP drivers (KESSOUND, KOEIADS); an SPU2
   model; check by ear.
7. From before: the PCSX2 trace of the boot, the GS's Z and PSMCT16S
   layouts, CSM2, mipmaps (battle textures use MXL up to 4), the memory card
   with data.

Open points:
* `sceGsSyncPath`'s other conditions (VIF1_STAT, VPU_STAT's VU1 bit,
  GIF_STAT) read idle here; only the channels' STR bits can be busy.
* VIF1's FBRST (the game's reset after a timeout) is ignored; VU1 and VIF1
  keep their state.
* The EFU's ESIN, EATAN and EEXP use the host's library, not the VU's series.
* PS2Recomp-style "infinitely fast" units: VU0 runs inside vcallms, VU1
  inside the VIF1 thread; the EE never sees VU1 running (VPU_STAT 0).
* Older open points: see session 6's list in the history of this file.

Restarting: work on ps2kit in its own checkout beside this repository and
run its Python tools from the directory that holds that checkout. Build with
`ninja -C build/recomp-build ps2run gsreplay vubench linkcheck difftest`.
Starting a run: Start every two seconds from 8 to 22 reaches the menu; cross
at 28 opens the character select; no cross, and the attract mode's battle
starts at about 45 s. Don't time runs while something heavy runs beside
them.
