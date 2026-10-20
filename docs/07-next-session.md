# TODO — session 10

Where session 9 left the game ([17-latency](17-latency.md)): the attract
battle sends a list every field and 2 to 7 in about 745 are cut by the
game's reset; the menus and the character select are right. The battle's
picture shows only its lower half (below).

Before running: make the VU1 translations if `build/recomp/vu1_trans.cpp`
is missing (commands in [16-speed](16-speed.md)); without it everything
runs, interpreted.

1. **The battle's picture (first).** Check with PCSX2, software renderer:
   does the attract battle show the whole picture, and is it the buffer
   DISPFB2 names (drawn the field before) or the one drawn in the field? In
   our model the vblank handler's SDK swap (16-bit, `gpDBuffPtr`, with its
   clear) wipes half of the 32-bit buffer each field shows (details in
   17-latency, "Open"). Then fix what the PCRTC shows, or what we got wrong
   on the way there.
2. **Sound (phase 5).** Koei's two IOP drivers (KESSOUND, KOEIADS) and an
   SPU2: decide first between running the IOP modules on an IOP
   interpreter with an SPU2 model, and modelling Koei's RPC services at
   the SIF boundary as the rest of the IOP is. Check by ear.
3. **The last cut lists.** Bursts where the drawing threads fall a field
   behind (the battle's first second; CLUT changes: `CLUT_SLOTS` is 64).
   Ideas: more CLUT slots; strips dealt to threads by load rather than
   fixed (the host's efficient cores are slower); the GS thread's decoding
   (`fast_prim`, `vertex`).
4. **The PCRTC's feedback blur** (`SetFeedBack`, `g_SetBlurPCRTC`;
   EXTBUF/EXTDATA/EXTWRITE): not used by the attract mode (no write to
   them); find where the game turns it on, then model the write-back.
5. Once lists fit: `PS2KIT_RESETS=1` by default (the console's behaviour).
6. From before: battles look dark (compare with PCSX2), the GS's Z and
   PSMCT16S layouts, CSM2, mipmaps, the memory card with data.

Open points:
* Texture copies in the menus: about 6 MB a field (the destinations of
  local-to-local transfers, used as textures after); each local-to-local
  transfer is a full barrier.
* `vutrans` translates only what a dump saw; a JR to an address not after a
  BAL/JALR stops.
* The EFU's ESIN, EATAN and EEXP use the host's library.
* Scripted presses are timed in seconds: once in session 9 a run stayed in
  the movies (the presses missed); run again.

Restarting: as before (ps2kit in its own checkout; build with
`ninja -C build/recomp-build ps2run gsreplay vubench vutrans roundcheck linkcheck difftest`).
Start every two seconds from 8 to 22 reaches the menu; cross at 28 opens
the character select; no cross, and the attract battle starts at about 45 s.
Edit scripts with backslashes go into files (Write), never a heredoc.
