# Session log

## Session 1 — the disc, the executable, ps2kit on its own

Goal: start the port and the recompiler it is the first case for; see what
the disc and the executable give.

Results:

* **ps2kit split out of pc-extermination** with its history (`git subtree
  split`), as agreed for the second game on the kit: a repository of its
  own beside this one, a submodule here. Not published yet.
* **Disc read** (`ps2kit.disc`, new, adapted from saturnkit's reader): a CD
  of MODE2/2352 data and one CD-DA track, which is silence. All 276 830 data
  sectors' subheaders read: Form 1 only. 50 files extracted
  ([01-disc-layout](01-disc-layout.md)).
* **The executable is not stripped**: `.symtab`, `.mdebug` (508 source
  files, the codename "pale"), `.stab`, VU microcode labels. New in ps2kit:
  `mdebug`, and in `elf` the function map: 4 073 functions that tile
  `.text` exactly ([02-executable](02-executable.md)).
* **ps2kit.ee**, the R5900 decoder, written from the encoding tables: all
  307 646 instructions of the game decoded (202 operations) and equal to
  Ghidra's EE decoder, up to aliases and notation, on every instruction and
  on all 40 425 branch and jump targets. ps2kit no longer needs Ghidra to
  read EE code; Ghidra stays as a second reader (`ghidra/ExportListing.java`).
* **The route** ([06-attack-plan](06-attack-plan.md)): ps2kit's own
  translator and runtime, with this game as their first case.
* Six curiosities ([04-curiosities](04-curiosities.md)), among them
  Kessen's sound driver and the "pale" codename.

One claim was corrected before it was written down: the first draft of the
kit's check table said every `.mdebug` procedure sits at the `.symtab`
address of its name. Checked, 3 720 do; the other 336 are later static copies
of C++ inlines, which `.symtab` names only once.

## Session 2 — the translator, checked function by function

Goal: phase 1 of the plan, ps2kit's own translator from EE code to C++.

Results:

* **`ps2kit.recomp`** (program model, emitter, driver; adapted in shape
  from wiikit's): all 4 073 functions and 307 646 instructions translate,
  none unsupported; 142 switch tables resolved and sized by their bound
  checks; 821 tail calls; one jump into a delay slot handled. 27 MB of C++
  in 38 files, compiled and linked by clang at `-O1` in about 20 seconds,
  no error and no warning ([09-recompiler](09-recompiler.md)).
* **`ps2kit/runtime`** begins: `ee.h` (the guest as the generated code
  sees it: 128-bit registers, memory, the FPU and VU0 helpers), memory and
  dispatch, a stub, the link check.
* **`ps2kit.eeemu`**, a reference interpreter in Python, and
  **differential tests** (`ps2kit.recomp.difftest`): the recompiled C++
  against the interpreter, every register and every byte of memory.
  56 named functions (string routines, 64-bit arithmetic, the SDK's soft
  float, `sprintf`, libvu0) × 10 states: 560 runs, all equal. Every leaf
  function of the game (1 080) fuzzed with two states: 1 751 runs, all
  equal, 409 skipped (the reference could not finish them). Together they
  exercise 179 of the 202 operations the game uses; 7 of the other 23 are
  system operations, which need the runtime.
* **The FPU and VU model** set to PCSX2's default, which the user's
  PCSX2 uses too: round toward zero, no denormals, no infinities or NaNs.
  The reference computes it exactly (rationals, truncated to 24 bits).
* **`ps2kit.fingerprint`** says whether an executable kept its symbols: of
  the three PS2 games so far only this one did.
* **The kernel surface** measured for phase 2: 53 syscall stubs the game
  calls, numbers and names from the SDK's own `klib.s`.

What the tests caught, in order. A dispatch bug in the reference (`vmr32`
and `vmove` share an operand form with `vabs` and fell into its branch).
Wrong cases (float arguments go in `$f12`, integer arguments five to eight in
`t0`–`t3`), and one fix that never landed because a bash heredoc ate its
backslashes. The reference's exact round-toward-zero arithmetic losing the
sign of exact zeros. In every case the recompiled side was right.

## Session 3 — the boot

Goal: phase 2 of the plan, the game started on ps2kit's runtime as far as
it goes before the IOP; it went further ([11-boot](11-boot.md)).

Results:

* **`ps2run`** (ps2kit `runtime/boot.cpp`): the game starts from the disc
  image, as the boot ROM starts it: `SYSTEM.CNF`'s BOOT2, the ELF read from
  the disc, its path as `argv[0]`.
* **The EE kernel** at the syscall boundary (`kernel.cpp`): threads on host
  threads with a baton, strict priorities, semaphores, sleep and wakeup,
  INTC and DMAC handlers and alarms, SIF registers and DMA, Deci2's TTY.
  **The hardware registers** (`hw.cpp`): INTC, DMAC, timers, GS CSR/IMR
  with a 50 Hz vblank, SIO.
* **The first wait on the IOP** came where the code says it would:
  `sceSifInitCmd`, waiting for SMFLG bit 0x20000, before any output.
* **The game prints nothing** on success: no function of its own calls
  `printf`; only SDK libraries do, on errors. The planned check ("its first
  lines on the host console") cannot happen in this game.
* So phase 3 began: **the IOP at the SIF boundary** (`iop.cpp`), every
  packet layout read from the game's own SIF libraries; the IOP reboot
  (`IOPRP153.IMG`), ten modules "loaded" (read from the disc for their
  headers), the RPC servers they bring found in the modules' own code.
  cdvdfsv (init, file search, disk ready, sector reads, errors), loadfile,
  the IOP heap, mcserv's init (versions from MCSERV's code), padman (a
  DualShock 2 on port 0), and a silent stand-in for Koei's two sound
  drivers. **The disc image** (`disc.cpp`): ISO 9660 and sectors, its file
  positions equal to ps2kit's Python reader.
* The game now runs its own frame loop at 50 Hz, reads `LINKDATA.BNS`,
  initialises sound, finds its six movies, and stops at its first memory
  card request (mcserv function 1); two runs give the same 946 IOP
  commands and RPC calls and the same system calls.
* **Diagnostics**: a heartbeat every five seconds (vblanks, DMA per
  channel, disc reads, system calls, handler calls), `--trace 1/2`, and a
  sampling profiler (`--profile`) that names the guest function the time
  goes to, from the executable's unwind tables.
* The differential tests stay green: 560 named runs and 1 751 fuzzed leaf
  runs equal, as in session 2.

What took the time: the game's vblank handler busy-waits for the GS
FIELD bit to change. With FIELD toggled at the start of the blank, each
call waited a whole field and the main thread starved: the profiler showed
97% of the time in `main_callback`. Three causes, found one after another
by measuring: the clock thread overslept by up to 15 ms on Windows; the
guest's tight CSR polling starved the clock of the hardware lock; and
interrupts here are taken at loop back-edges, not within cycles. Reading the
real BIOS kernel (1.60, 2001) settled how the dispatcher takes interrupts
(highest cause only, cleared before the handlers) and that `_EnableIntc`
leaves a pending cause alone, as modelled. Two smaller bugs: an index into
the FIFO table (a crash) and `rt_die` calling `exit()` while other threads
held locks (a hang); the bash-heredoc trap from session 2 bit twice more.

## Session 4 — the first pictures

Goal: the publishing checkpoint, the first picture on screen
([12-movies](12-movies.md)).

Results:

* **The memory card**: an empty slot. mcserv's `sceMcGetInfo` answers -11
  with type 0, as MCMAN's detection does with no card (read in MCSERV
  v2.06 and MCMAN v2.07); the game shows its no-card message and goes on.
* **Streaming**: CDVDFSV's stream commands (init, start, seek, stop, read),
  as its v2.08 code answers them, with an infinitely fast drive.
* **The IPU** (ps2kit `runtime/ipu.cpp`): FIFOs fed and drained by DMA
  channels 4 and 3 on the unit's own thread; BCLR, VDEC, FDEC, BDEC, SETIQ,
  SETVQ, CSC, SETTH. What libmpeg expects of each was read in its code; the
  MPEG-2 tables are checked at start-up by their share of the code space.
  `KOEILOGO.PSS` decodes as ffmpeg decodes it, within IDCT rounding (at
  worst 65.8 dB, no sample off by more than 4).
* **KOEIADS's host transfer**, from the module's code, so that the movie
  player can hand over its audio and start; the playback is a clock.
* **The GS** (ps2kit `runtime/gs.cpp`): local memory with ps2kit.gsmem's
  layouts, GIF path 3, transfers, a software rasteriser, the PCRTC's
  picture; **a window** (SDL3) and `--shot` screenshots.
* **The first picture**: the Koei logo movie, then Midas's, at 25 frames
  a second; confirmed by the user in the window.

What the tests caught: one transcription error in the motion-code table
(codes 11 to 16 one bit short), found by logging every bit the IPU
consumed (equal to the elementary stream) and decoding the failing
macroblock by hand and offline. A hand decode of mine was wrong on the way,
and so, for a while, was the comparison with ffmpeg itself: libmpeg keeps
its pictures by macroblock columns, and the raster comparison showed
errors that were not there. The movies ran at 3.6 frames a second until
the short IPU commands stopped crossing threads.

## Session 5 — the title screen

Goal: past the movies, to the title screen ([13-title](13-title.md)).

Results:

* **Input** (ps2kit `runtime/input.cpp`): the pad in port 0 from the
  keyboard and a gamepad (SDL3), and scripted presses (`--press`) for runs
  without a window. The button layout was read in the game's own pad code
  (`CKzPad`, `padfunc.c`). Start skips the movies; the title's menu takes
  the arrows and cross.
* **VU0's micro mode and VIF0** (ps2kit `runtime/vu0.cpp`): the game's
  trigonometry library, uploaded once by VIF0, runs in an interpreter
  that follows PCSX2's pair rules and checks, at every run, that the
  program reads no flag and no Q sooner than the console's pipeline would
  give them. 863 logged runs of six programs agree with libm and with their
  own polynomials (`tools/vu0check.py`).
* **VIF1 and GIF path 2** (ps2kit `runtime/vif1.cpp`): VIF1's codes are
  counted (the census says what VU1 will need), DIRECT and DIRECTHL go to
  GIF path 2, with a packet in progress per GIF path.
* **The disc's clock** (`sceCdReadClock`), from CDVDFSV's and CDVDMAN's code.
* **The title screen and its menu** on screen: the logo, the three
  crystals. On the menu the game makes a frame every four seconds or so:
  its vblank handler sends the display lists again every field, and the
  GS model takes the whole field to draw them. That is next, then VU1.
* Macro mode follows the same rules as micro mode: MAX and MINI on bit
  patterns without flags, DIV, SQRT and RSQRT with the I and D flags; the
  differential tests still agree.
* Debugging aids: `PS2KIT_WATCH` (guest memory on change), `PS2KIT_VU0_LOG`.

What took the time: the title seemed deaf to start. The pad words were
right; the title had gone straight to its menu (after a skipped opening it
skips "press start"), whose crystals were missing and which wants cross.
A fade after a cross looked like the menu answering; it was the demo's
timeout. Once the crystals were drawn, cross seemed lost; the watch on the
frame counter showed the game making a frame every four seconds.
The crystals were missing because vf0 was (0, 0, 0, 0) in the runtime's
first thread, so the game's VU0 constant vf31 (made as vf0 - vf0 + vf0.w)
was 0 and the cosines, atan2 and rotations came out wrong; checking the
VU0 programs against libm found it at once. The differential tests had
never seen it: they set vf0 themselves. Twice more, a bash heredoc ate backslashes in a Python
edit script; nothing reached a file, the scripts were rewritten.

