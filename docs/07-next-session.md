# TODO — session 11

Where session 10 left the game ([18-sound](18-sound.md)): the attract mode
is whole, picture and sound (the logos, the movies, the menu's sounds, the
attract battle), checked by ear against PCSX2. The IOP's sound modules run
on an R3000 interpreter; the SPU2 is modelled at its registers.

Before running: make the VU1 translations if `build/recomp/vu1_trans.cpp`
is missing (commands in [16-speed](16-speed.md)); without it everything
runs, interpreted.

1. **A real battle (first).** Everything so far was the attract mode's
   opening; the game proper runs its own vblank handler (`main_callback`,
   with its check of the channels and its GS reset). The user played one
   at the end of session 10 (window, sound, Xbox pad): the battle runs and
   is broadly right, but:
   * **Input queued and replayed**: with many characters on screen,
     presses (up, left, up) do nothing, then 3-4 seconds later the
     character moves up-left-up. A game that reads the pad's state each
     field would lose presses, not replay them: something queues. First
     measure which: SDL's events read late (they are pumped on the main
     thread with the picture), or the picture shown seconds behind the
     game (the GS's lag: `gs_lag`, the heartbeat); then the fix.
   * **The frame rate drops** as characters gather (session 9's slow
     lists, now in a real battle: `PS2KIT_TIMELINE`, the thread profiles;
     count `main_callback`'s resets).
   * **Flicker in the battle's introduction**: the ground's textures come
     and go, then stay stable once the player has control. Record it
     (`PS2KIT_GS_DUMP`) and replay field by field: texture transfers, CLUT
     loads or local-to-local copies landing in the wrong field.
   * The log said once "both PCRTC read circuits at once (circuit 2 shown)
     is not modelled yet": circuit merging, likely the feedback blur (4).
   Then the sound (music, effects, voices) by ear against PCSX2.
2. **`PS2KIT_RESETS=1` by default** (the console's behaviour) once a real
   battle's lists fit in a field.
3. **Sound, what is left**: the SPU2's own Gaussian interpolation (cubic
   now; the table only from a documented source), volume sweeps (DW2 sets
   none so far: said once if seen), memory input (ADMA), interrupts on the
   effects' area. Whatever the real battle needs first.
4. **The PCRTC's feedback blur** (`SetFeedBack`, `g_SetBlurPCRTC`;
   EXTBUF/EXTDATA/EXTWRITE): not used by the attract mode; find where the
   game turns it on, then model the write-back.
5. **The last slow lists** (session 9's item, now for the real battle):
   CLUT slots, strips dealt by load, the GS thread's decoding.
6. From before: battles look dark (compare with PCSX2), the GS's Z and
   PSMCT16S layouts, CSM2, mipmaps, the memory card with data.

Open points:
* One host crash (segmentation fault) in a run with `--trace 1`, while the
  movies were still restarting, before the DMA fix; not seen in ten runs
  since. If it comes back: gdb (`/c/msys64/mingw64/bin/gdb -batch -ex run
  -ex bt --args ...`).
* Texture copies in the menus: about 6 MB a field; each local-to-local
  transfer is a full barrier.
* `vutrans` translates only what a dump saw; a JR to an address not after a
  BAL/JALR stops.
* The EFU's ESIN, EATAN and EEXP use the host's library.
* Scripted presses are timed in seconds: a run can miss them.

Restarting: as before (ps2kit in its own checkout; build with
`ninja -C build/recomp-build ps2run gsreplay vubench vutrans roundcheck linkcheck difftest`,
ninja and clang from `/c/msys64/mingw64/bin`). Start every two seconds
from 8 to 22 reaches the menu; cross at 28 opens the character select; no
cross, and the attract battle starts at about 40 s. `--wav FILE` records
the sound; `PS2KIT_SPU2_LOG=1` logs the SPU2's interrupts, transfers and
voices. Edit scripts with backslashes go into files (Write), never a heredoc.
