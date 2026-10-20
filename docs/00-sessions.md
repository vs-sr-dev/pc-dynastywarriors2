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


## Session 6 — the GS's speed, the character select

Goal: a GS model fast enough for the title menu ([14-gs-speed](14-gs-speed.md)).

Results:

* **A recording of the GS's work and its replay** (ps2kit
  `PS2KIT_GS_DUMP`, `runtime/gsreplay.cpp`): the GS's state, then every
  packet and vertical blank, played again without the game, timed,
  pictured, profiled.
* **Two rasterisers, one result**: a reference that reads the registers at
  every pixel, and a fast one that decodes them once per primitive;
  `gsreplay --compare` finds them equal after every field of two menu
  recordings (250 fields). 50.7 million pixels a second against session 5's
  17 to 19; 8.5 ms a menu field against 24. Edge functions are exact 64-bit
  integers now; on the session-5 recording that changed no byte.
* **The GS on its own thread**: DMA channels 1 and 2 end when the GS has
  drawn their data, SIGNAL and FINISH arrive when the GS meets them;
  `PS2KIT_GS_SYNC=1` keeps the old way.
* **The menu at full speed** (50 frames a second, was one in four seconds),
  and cross on MUSOU MODE opens the **character select** (Zhao Yun's
  portrait and bars; the model himself is VU1's).
* **FIELD and VBON acknowledged by the guest**: the movie player's
  `kpmStartDisplay` polls VSync until FIELD changes, clearing VBON itself
  before the kernel takes it; FIELD changed only when the kernel took it,
  so movies could hang. The guest's acknowledgement counts now.
* **Played in a window by the user** (keyboard and an Xbox pad): menus,
  character select, a battle without its 3D models. Fixed after it: the
  picture is taken at each vertical blank in the GS's order (it could be
  half drawn), interlaced fields are shown at their own lines and blended
  with the field before (`PS2KIT_DEINTERLACE`; measured on the menu); VIF1
  and the GIF start on STR's 0-to-1 edge only (a CHCR written back while
  busy restarted VIF1's chain from its end and crashed the attract mode);
  local-to-host transfers through VIF1. The user's verdict: everything but
  sound and the 3D works, and the flicker is gone.

What took the time: the first speed-up (shifts for the addresses' divisions)
gave 15%; a profiler, not a guess, showed the cost spread over every
pixel's decoding, which is what the fast rasteriser removes. The hang
looked like a GS-thread race; counters in the heartbeat showed VSync
returning every field while the kernel never took VBON, which led to the
FIELD rule. Twice more a bash heredoc ate backslashes in a Python edit
script (fixed before anything was built); edit scripts now go into files.


## Session 7 — VU1: the 3D models

Goal: VU1, with the character select as its first picture ([15-vu1](15-vu1.md)).

Results:

* **VIF1 in full** (ps2kit `runtime/vif1.cpp`): UNPACK in every format with
  write cycles, masks and modes, the OFFSET/BASE double buffer, ITOP,
  MSCAL/MSCALF/MSCNT, MPG; XGKICK into GIF path 1.
* **One interpreter for VU0 and VU1** (`runtime/vu.cpp`) with the FMAC,
  FDIV, EFU and integer pipelines modelled: DW2's rigid-part program reads
  the MAC flags exactly four pairs after their producer, with newer results
  in flight. VU0's library still checks against libm as before.
* **VIF1 and VU1 on their own thread**: run inside the vblank handler they
  took more than a field and starved the game's main thread (found with a
  profiler that now records whole guest call chains).
* **The character select at 50 frames a second**, its officers drawn; lit
  and textured once vf30, which no program of the game writes before it,
  holds a fog factor (`PS2KIT_VU1_VF`; question below).
* **Speed**: VU pairs decoded once, a no-stall shortcut, FMAC arithmetic
  with DAZ/FTZ: 22 to 50-57 million pairs a second, each step checked byte
  for byte with the new `vubench`. The GS's CLUT buffer loaded as CLD says
  (it was read per triangle): a battle field 15 ms to 8.5 ms.
* **The attract-mode battle draws** (walls, trees, ground, soldiers), but
  one field in four or five the game finds its lists unfinished at the
  vertical blank and resets the GS (`main_callback`, decompiled with the new
  `ghidra/Decomp.java`). Holding the blank was tried and taken out.

What took the time: the black character select was three causes in a row:
VU1 starving the main thread (the fade-in stopped), then a fade sprite that
hid everything, then the fog factor from vf30. Each was found by measuring
(per-record replays of a GS recording, a watch on the fade counter, guest
call chains in the profiler) rather than by reading the microcode, which
was right. A bash heredoc ate backslashes twice more (one compile error
each, nothing kept).


## Session 8 — vf30 found; VU1 translated; the GS on several threads

Goal: the TODO's GS threads and VU1 speed ([16-speed](16-speed.md)).

Results:

* **vf30**: the user checked PCSX2 (fast boot and full BIOS boot both show
  lit officers), so the game sets it: `SetFogOff` stores VU1's fog factor
  through VU0's window on VU1's registers (quadword 0x41E). The runtime now
  maps VU0's addresses from 0x4000 to VU1's VF registers; no preset needed.
* **The GS on worker threads** (`PS2KIT_GS_THREADS`, default 4), deferred
  transfers and lone primitives as sync jobs, exact block sets; equal to
  the reference rasteriser on every recording.
* **VU1 microcode translated to C++** (`vutrans`), its timing decided while
  translating; equal to the interpreter on 214 dumped starts and about 3.5
  million in-game starts; VU1 about 6 times faster in a battle.
* **VIF1** faster (batched XGKICKs, specialised UNPACKs checked on 17.7
  million, NOPs, codes in place); the resets after a timeout modelled
  (`PS2KIT_RESETS`, off); `PS2KIT_TIMELINE`, thread profilers.
* **The battle**: more frames drawn, but a large list still outlasts a
  field about half the time, and each such field shows the reset's
  32-bit PCRTC set-up. Next: one list's latency.

What took the time: a slow battle had several bottlenecks in turn (VU1,
then XGKICK hand-offs, then the GS's waits on transfers, then CLUT loads
that looked like conflicts because a span of whole pages ran past the end
of memory); each was found with a profiler or a counter by cause. Three
bash heredocs ate backslashes again (each caught before a build was kept);
a sampling profiler deadlocked by allocating while its target thread held
the heap lock; `vutrans` first linked the code it generates, so a broken
output could not be regenerated (now it stands alone).


## Session 9 — a battle list within its field

Goal: the TODO's first item, one list's latency ([17-latency](17-latency.md)).

Results:

* **VIF1**: a chain's transfers and the GS's paths 1 and 2 handed over in
  batches; a battle list's time in VIF1 from 33 ms to about 7 ms.
* **The GS**: drawing jobs read texture copies, so texture transfers no
  longer stop the drawing threads; the feedback copy is no longer drawn
  alone; jobs that must follow others are fences; PSMCT32 specialised (it
  never was: 0 meant "other"); an SSE2 bilinear sample whose rounding
  `roundcheck` holds to the reference's on every float. The battle's
  recording: 23.4 ms a field on one thread (32.7), 5.3 to 5.9 on eight
  (12.3). Equal to the reference on five recordings.
* **Timing**: a channel ends when the GS is given its data, unless the
  GS's thread is more than a field behind (`PS2KIT_GS_LAG`); the clock runs
  at time-critical priority.
* **The attract battle**: a list every field, 2 to 7 of about 745 cut by
  the game's reset (about half before).
* **Found, open**: the battle's picture shows only its lower half. The
  SDK's 16-bit double buffer, still swapped and cleared by the vblank
  handler, clears half of the 32-bit buffer each field shows. The packets
  are the game's own, so the question is what the PCRTC shows: for PCSX2.

What took the time: each bottleneck hid the next (VIF1's queue, the GS's
queue, sync jobs, a primitive drawn alone, the channel's end, the GS's
thread waiting, a late blank, the pixel loop); each was found with the
timeline (now naming who starts a transfer) or a thread profile (now naming
system libraries, which showed the waits). An exhaustive check caught the
one float where an obvious rounding was wrong, which the recordings had
not. Three bash heredocs ate backslashes again (each a compile error,
nothing kept); edits with a backslash go through Write or Edit only.


## Session 10 — the battle's whole picture; sound

Goal: the TODO's first two items, the battle's picture (after the user's
PCSX2 check) and sound ([17-latency](17-latency.md), [18-sound](18-sound.md)).

Results:

* **The picture**: PCSX2 shows the attract battle whole. The cause was
  ps2kit's interrupt chains: the BIOS kernel (read in the user's ROM 2.20)
  puts a handler added with next = 0 at the head and stops at a negative
  return, so the opening's vblank handler ends the chain and
  `main_callback` (its 16-bit swap and clear, its GS reset) never runs in
  the opening. The attract battle's "cut lists" were the same artifact.
* **Sound**, the route the user chose: LIBSD, MODHSYN, MODMIDI, MODMSIN,
  KOEIADS and KESSOUND run unchanged on an R3000 interpreter at the IOP's
  clock, with about 50 kernel functions as host code, and an SPU2 at its
  registers (voices, ADSR, mixes, reverb, IRQA, transfers); `--wav`.
  Checked by ear against PCSX2: the logos, the movies, the menu's sounds,
  the attract battle's music and effects; the menu is silent there too.
* Fixed on the way: KESSOUND's 4.2 ms timer ticks merged by a coarse wait
  (music at a third of its speed); the BGM stream played past a block not
  yet refilled (samples now stop at an interrupt); core 0 never heard
  (ATTR bit 14 taken as a mute, AVOL/BVOL); movies started again and again
  (CHCR's TAG field filled from the tag's address: a toIPU chain ran past
  its end, zeros to the IPU); the opening movie at 16 pictures a second
  (the IPU's thread now spins for its next command), its sound stuttering.

What took the time: each sound bug hid behind another, and each was found
by a measurement rather than by ear: the timer by interrupts a second, the
gaps by their exact length (one stream block), the silent core by a
key-on's register dump and a voice's peak against the output's, the movie
restarts by a log of all-zero quadwords that showed an impossible TAG
field. One rare host crash (a traced run, while movies were restarting,
before the DMA fix) was not seen again in ten runs; its cause is not
proven. Another heredoc ate a backslash (caught before writing).
