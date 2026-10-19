# The title screen

Session 5 took the game from the end of its movies to its title screen and
menu: input from the host, VU0's micro mode (with VIF0), the start of VIF1
and GIF path 2, the disc's clock. On the menu the game now runs at about
one frame in four seconds, for a reason found at the end of the session
(below): the GS model is too slow for what the game asks of it.

```sh
build/recomp-build/ps2run.exe "build/image/Dynasty Warriors 2 (Europe).cue"
build/recomp-build/ps2run.exe "build/image/Dynasty Warriors 2 (Europe).cue" --headless --seconds 50 \
    --press 8:START,10:START,12:START,14:START,16:START,18:START,20:START,22:START,24:START,26:START,28:START,30:START \
    --shot 36,49 --shot-dir build/shots
```

## Input

`ps2kit/runtime/input.cpp`. Port 0's DualShock 2 now takes the keyboard
and a gamepad (SDL3) in a window, and scripted presses with or without one:
`--press T:NAMES[,...]` holds the buttons (joined with `+`) for 0.2 s at T
seconds of host time, `T-U:NAMES` from T to U. The default keys: arrows,
Enter start, Backspace or Right Shift select, X cross, C circle, Z square,
S triangle, Q L1, W R1, 1 L2, 2 R2.

The button layout was read in the game's code rather than taken from a
description of the pad protocol: `CKzPad::Read` builds its word as
`~(byte2 << 8 | byte3)` and its `IsPush*` tests name every bit (0x800 start,
0x80 square, 0x20 circle, 0x10 triangle, 0x40 cross, ...); `padfunc.c`'s
`CheckPadDataSub` reads the same two bytes as a halfword the other way round
(start 0x8, cross 0x4000), which is the layout the title screen tests.

The movies skip on Start (`movie_skip_key`); after a skipped opening the
title goes straight to its menu (`TITLE_Main` with its second argument set
skips `TITLE_StartManage`, the "press start" loop). The menu
(`TITLE_ModeManage`) moves between its three crystals with left, right and
down (up from the lower one) and confirms with cross; after 751 frames
without a button it returns 5, the demo.

Timing matters for scripts: a press is seen only when it changes between
two of the game's frames, and how long the boot and the movies take depends
on the host and its load (a run beside a busy process was still on the Koei
logo at 30 seconds). Start every two seconds from 8 to 30 reached the menu
at about 32 seconds on an idle host. On the menu a press has to be held for
several seconds (see "Where it stops now"): cross held from 40 to 50
reached the game as a fresh cross at 40.8 seconds.

## VIF0 and VU0's micro mode

`ps2kit/runtime/vu0.cpp`. After the opening the game calls VU0 micro
programs (`vcallms`) about four hundred places in its code. The microcode is
one upload at start-up: a VIF0 DMA chain at `0x3CE500` (STCYCL, STMASK,
STMOD, two MPGs: 256 instructions at 0 and 165 at 0x800), which
`python -m ps2kit.vu SLES_500.57 --dma 0x3CE500` lists. It is a hand-written
trigonometry library (`vu0lib.c`'s `init_vu0_regs` loads its constants into
vf21-vf31: 2 pi, pi, -pi, pi/2, the atan, sine and cosine coefficients, -1,
1): sine, cosine, both, atan2, and rotation matrices about x, y and z.

VIF0 keeps its codes in a FIFO across transfers and writes MPG data into a
4 KB micro memory; other codes it has not met stop the run. A micro program
runs to its end inside `vcallms`, on the calling thread's VU0 registers.
The interpreter takes each instruction pair as PCSX2's VU0 interpreter
does: both halves read the registers as they were before the pair; when
both write the same VF register the lower one is dropped; with the I bit the
lower word goes into I after the upper instruction; one delay slot after a
branch and after the E bit; a conditional branch right after an integer
instruction that wrote its register reads the older value. (That last rule
never applied in DW2's runs; the runtime says so when it does.)

Results come out in program order, as if each instruction finished before
the next. On the console the FMAC pipeline takes 4 cycles, DIV and SQRT 7,
RSQRT 13; a read of a register still in flight stalls, so register values
are the same, but reads of the flags and of Q do not stall. The runtime
counts pairs and says once per address when a program reads flags or Q
sooner than the console's latency (a stall only adds cycles, so a read that
passes this test sees on the console what it sees here). The microcode is
scheduled for exactly these numbers: it reads CLIP's and FMAC's flags four
pairs after the instruction that sets them, and DIV's flag seven; no run
has said anything.

**The check.** With `PS2KIT_VU0_LOG=N` the runtime prints each program's
first N runs (vf1, vf2, vf16-vf19 before and after);
[tools/vu0check.py](../tools/vu0check.py) compares them with libm, and
the sine and cosine also with their own polynomials, evaluated in double
precision after the microcode's range reduction with the coefficients read
from the executable. From 863 runs of a menu session:

| Program | Computes | Runs | Worst error |
|---|---|---|---|
| 0000 | sin(vf1.x) | 87 | 1.4e-4 (its polynomial: 1.4e-7) |
| 0010 | cos(vf1.x) | 87 | 2.2e-5 (its polynomial: 1.9e-7) |
| 0030 | atan2(vf1.x, vf2.x) | 4 | 3.0e-7 |
| 0060, 0070, 0080 | vf16-vf19 rotated about x, y, z by vf1.x | 685 | 3.0e-7 |

The sine and cosine errors against libm are the polynomials' own: their
first terms left out, x^9/9! and x^10/10! at pi/2, are 1.6e-4 and 2.5e-5.

The same rules hold now for VU0's macro mode, in the translator and in its
reference interpreter: MAX and MINI compare bit patterns and set no flags;
DIV, SQRT and RSQRT set the status flags I and D (the flag rules, and
RSQRT's 0/0 giving a signed zero, are PCSX2's). The differential tests
still agree (560 named runs, 1 751 fuzzed leaf runs); among the game's
functions they reach `vdiv` and `vsqrt`, not `vmax`, `vmini` or `vrsqrt`.

**A bug the check found.** The first logs gave atan2(-200, 1000) = 0: vf31
was 0, not 1. `init_vu0_regs` makes it as vf0 - vf0 plus vf0's w, and the
runtime's first thread started with vf0 all zeros; every thread takes its
VU0 registers from it. vf0 is (0, 0, 0, 1) now. The differential tests had
never seen it, because they set vf0 themselves. Before the fix the title
menu's crystals were not there at all; after it they turn as they should.

## VIF1 and GIF path 2

`ps2kit/runtime/vif1.cpp`. VIF1's codes are walked and counted; the census
in the heartbeat says what the game needs from it, in three phases:

* at start-up: 13 MPGs (13 176 bytes of VU1 microcode) and a few DIRECTs;
* the title screen and its menu: DIRECT only, with FLUSH (2D, through
  GIF path 2);
* the demo, which the menu starts after 751 idle frames (seen in runs made
  before the vf0 fix below, when the menu ran fast because its crystals
  were not drawn): first STCYCL, OFFSET, BASE, MSCAL, MSCALF and
  UNPACK V4-32, then also MSCNT, FLUSHE, FLUSHA, DIRECTHL, UNPACK S-32, S-8,
  V2-32, V3-32, V4-8, about 1 700 MPGs, and DMA tags sent with TTE.

DIRECT and DIRECTHL now hand their data to GIF path 2. The GIF keeps a
packet in progress per path (it changes paths only between packets), into
the one GS. The census also counts MPG and DIRECT data that would not start
on a 64- or 128-bit boundary of the stream: none, in millions of codes.

The title screen and its menu are path 2's: the background, the logo, the
three translucent crystals (MUSOU MODE, FREE MODE, OPTIONS), and the fade
to the demo. The demo is VU1's.

## The disc's clock

`sceCdReadClock` (CDVDFSV's s-command 1) is read from the modules: CDVDFSV
v2.08 (0x30C0) answers the word cdvdman's `sceCdReadClock` returns, then
the 8-byte clock; CDVDMAN v2.09 (0x28C8) gets the bytes with the
mechanism's S-command 8, clears byte 4 and bit 7 of byte 6, and returns 1
when the command completed (0xE48). The bytes are the status (0), second,
minute, hour, 0, day, month, year, in BCD; the console keeps Japan time, so
here it is the host's UTC plus nine hours.

## Debugging aids

* `PS2KIT_WATCH=ADDR[:SIZE],...`: guest memory printed whenever it changes
  (looked at every 5 ms) and with each heartbeat. The title's pad words
  are at `_gp - 0x64A0` (held) and `_gp - 0x6498` (pressed this frame),
  `_gp` = 0x3EBA70.
* `PS2KIT_VU0_LOG=N` (and `PS2KIT_VU0_LOG_ALL=1` for all 32 registers).

## Where it stops now: the GS's speed

On the menu the game makes a new frame about every four and a half
seconds (`_gp - 0x64BC`, counted by `main_callback` each time it takes a
new frame, rises by one in that time), so presses shorter than that are
lost and the menu's animations crawl. The cause is in `main_callback`, the
vblank handler (`system.c`): when the game has a new frame it swaps the
buffers, sends the new display lists and reads the pad; when it has not,
it sends the current lists again, every field. On the console the GS draws
them in a millisecond or two. Here the GS rasterises them inside
`sceDmaSend`, inside the interrupt: about 350 000 pixels a field (the
background and the large translucent crystals), at some 17 million pixels
a second, which is the whole field. The game's thread is left almost no
time. (Building the runtime at -O2 instead of -O1 changed nothing
measurable.)

So the next piece is the GS's speed (a rasteriser that decodes its
registers once per primitive rather than per pixel, and probably the GS on
its own thread, as the console's GS works beside the EE), then VU1 for the
demo and the game. See [07-next-session](07-next-session.md).

Session 6 did both ([14-gs-speed](14-gs-speed.md)): the menu runs at 50
frames a second, and a short press of cross opens the character select.
