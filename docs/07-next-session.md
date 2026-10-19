# TODO — session 4

Where session 3 left the game ([11-boot](11-boot.md)): it boots from the
disc image through the IOP reboot, module loading, file searches and reads,
pad and sound initialisation, runs its 50 Hz vblank loop, and stops at its
first memory card request, `sceMcGetInfo` (mcserv function 1), in
`MusouMCardGameStart`. Nothing is drawn yet.

1. **Decide with the user what "something to show" is now.** The planned
   checkpoint for publishing (the game's first lines on the host console)
   does not exist: DW2 prints nothing while things go right. Candidates:
   the boot as it stands (with its trace), or the first picture (the Koei
   logo movie, or the first GS frame).
2. **The memory card.** Choose what is in the slots (no card, or an empty
   formatted 8 MB card; later a card kept as host files), and answer
   mcserv's functions (1 GetInfo, 2 Open, 3 Close, 4 Seek, 5 Read, 6 Write,
   10 Flush, 12 Chdir, 13 GetDir, 14 SetFileInfo, 15 Delete, 16 Format,
   18 GetEntSpace; numbers from libmc in the game) with the codes MCSERV
   and MCMAN return, read from their code as was done for function 0xFE.
   `sceMcGetInfo` is asynchronous: its end function copies type, free
   space and format from a 0xC0-byte area; `sceMcSync` gets the result.
3. **The movies**: `msPlayMovie` (KOEILOGO.PSS first) through libmpeg and
   the IPU; see what it asks of the IOP (`sceCdStRead`, streaming) and of
   the hardware (IPU FIFO, DMA channels 3 and 4).
4. **Phase 4 begins**: the GS behind GIF DMA (path 3 first, what
   `main_callback` sends every frame: about 23 quadwords), an SDL3 window
   and OpenGL; `ps2kit.gsmem` already models local memory. Then VIF1 and
   VU1 for the 3D.
5. **A PCSX2 trace of the same boot** (still to do): the order of the IOP
   commands and RPC calls up to the memory card, against `--trace 1`.

Open points:
* FIELD changes three lines after the kernel takes VBON (a choice; the
  game only needs "after the interrupt starts"); check against PCSX2.
* The DualShock 2's actuator answers (01 02 00 0A, 01 01 01 14) are from
  public descriptions of the pad protocol; check against PCSX2.
* Koei's sound drivers answer zeros (a silent stand-in); 0 is confirmed as
  success for kessound's init only. Phase 5 ports them from their code.
* Deci2's TTY is implemented from the SDK's code but has printed nothing
  yet (the game prints only on errors).
* From session 2: the FPU/VU model's last-bit differences and exponent 255;
  operations no test exercises (`qmfc2.i`, `sqrt.s`, `viadd`, `vmtir`, a few
  VU0 forms, `divu1`/`mflo1`).

Restarting: run ps2kit from the directory holding the ps2kit checkout (the checkout being edited), not
from this repository's root. Regenerate with `python -m ps2kit.recomp
pc-dynastywarriors2/build/disc/SLES_500.57 --out pc-dynastywarriors2/build/recomp`,
build with `ninja -C build/recomp-build ps2run linkcheck difftest` (clang,
cmake, ninja from MSYS2's MinGW 64-bit environment), test as in
[09-recompiler](09-recompiler.md), run as in [11-boot](11-boot.md). Text
with backslashes goes through the editor, never a bash heredoc.
