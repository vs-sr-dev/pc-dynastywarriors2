# Speed: VU1 translated, the GS on several threads

Session 8 first found who writes vf30 (the EE, through VU0; see
[15-vu1](15-vu1.md), "vf30"), then went after the attract-mode battle's
speed. Each part has an oracle and was checked against it.

```sh
# the GS's recordings: the threaded fast rasteriser against the reference
build/recomp-build/gsreplay.exe build/s7/demo4.gsd --compare
# VU1's programs translated to C++: dump them, translate, rebuild
PS2KIT_VU1_DUMP=build/vu1/battle build/recomp-build/ps2run.exe "build/image/Dynasty Warriors 2 (Europe).cue" \
    --headless --seconds 62 --press 8:START,10:START,12:START,14:START,16:START,18:START,20:START,22:START
PS2KIT_VU1_DUMP=build/vu1/select build/recomp-build/ps2run.exe ... --seconds 42 --press ...,28:CROSS
build/recomp-build/vutrans.exe build/recomp/vu1_trans.cpp build/vu1/battle build/vu1/select
ninja -C build/recomp-build ps2run
# both checked on every start / every UNPACK of a run
PS2KIT_VU1_CHECK=1 PS2KIT_VIF1_CHECK=1 build/recomp-build/ps2run.exe ...
# where the time goes
PS2KIT_TIMELINE=1 ...                                   # blanks, channel starts and ends, resets
PS2KIT_PROFILE_FROM=55 PS2KIT_GS_PROFILE=gs.txt ...      # or PS2KIT_VIF1_PROFILE: offsets, for nm
```

`vu1_trans.cpp` holds the game's microcode, translated: like the recompiled
code it stays in `build/` and is made from the user's own disc.

## The GS on several threads

`PS2KIT_GS_THREADS` (default 4; from session 9 half the host's hardware
threads, 2 to 8: [17-latency](17-latency.md)) drawing threads take the fast rasteriser's
triangles and sprites as jobs; each draws the strips of 8 rows it owns, in
the GS's order, so memory ends as one thread leaves it. The GS's thread
keeps the spans of memory pending jobs write and read and waits only where
order would otherwise change. A transfer into memory pending jobs use, and
a primitive that reads its own target, become *sync jobs*: the threads meet
there and the last one does it, while the GS's thread goes on decoding.
Deferred transfers and textures carry the exact 256-byte blocks they touch
(a CLUT beside a texture, or at the top of memory, is not a conflict).
`gsreplay --compare` equal on every recording; a heavy battle field 50.7 to
about 18 ms, a light one 12.7 to 5 ms.

## VU1 translated to C++

The interpreter's timing (stalls; when Q, P and the flags land; a branch's
view of a VI register written the pair before) depends only on the pairs
and the way through the branches. `vu1_translate` (in `vu.cpp`, sharing the
interpreter's decoding) follows every way through a program with the
pipelines' timing, applies the interpreter's rules pair by pair and emits
each pair for the timing it meets. The code left does the arithmetic on
registers kept as locals, four lanes at a time where no operand has exponent
255, and moves Q, P and the flags where the timing says. `vutrans` writes
the programs of a dump; at each start VIF1 uses the translation whose pairs
micro memory holds, else the interpreter.

Checked equal to the interpreter (data memory, registers, P, XGKICKs and
every count): the 214 dumped starts with `vubench --trans`, and about 3.5
million starts of the character select and the battle with
`PS2KIT_VU1_CHECK`. VU1's time in a battle went from about 2.6 s to 0.4 s
every 5 s.

## VIF1

XGKICK packets go to the GS in batches; UNPACK V4-32/V3/V2/S without mask or
filling by format known to the compiler (`PS2KIT_VIF1_CHECK`: 17.7 million
equal to the generic form); NOPs skipped; codes read in place. With
`PS2KIT_RESETS=1` VIF1's and the GIF's resets drop the work left, as on the
console (off: see below).

## Where the battle is

The game sends one large list every two fields; on the console it ends
within the field. Here VIF1 carries one out in about 14 ms and the GS's
decoding follows behind, so the list is still running at the next vertical
blank about half the time: the game resets (the reset is ignored by
default, the list finishes late), and the field it resets shows the
PCRTC's default 32-bit set-up, green or striped. With VU1 faster the game
sends more frames, so the share of such fields went up (about one in two,
against one in four or five in session 7) while the frames drawn went up
too. `PS2KIT_RESETS=1` models the reset faithfully, and loses nearly every
frame until the lists fit in a field. Next: the latency of one list (VIF1's
code walk, the GS's decoding, the drawing threads) rather than the average.
