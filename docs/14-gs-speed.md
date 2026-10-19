# The GS's speed

Session 5 ended on a title menu that made one frame every four seconds or
so: the game's vblank handler sends its display lists again every field,
and the GS model, drawing inside the handler, took the whole field to draw
them. Session 6 made the rasteriser about 2.5 times faster, with a check
that it draws exactly what the old one drew, and put the GS on a thread of
its own, beside the EE, as on the console. The menu now runs at 50 frames a
second, and cross on MUSOU MODE opens the character select.

```sh
# a recording of the GS's work, from 24 s, 150 fields
PS2KIT_GS_DUMP=build/menu.gsd,24,150 build/recomp-build/ps2run.exe "build/image/Dynasty Warriors 2 (Europe).cue" \
    --headless --seconds 30 --press 8:START,10:START,12:START,14:START,16:START,18:START,20:START,22:START
build/recomp-build/gsreplay.exe build/menu.gsd                  # time the fast rasteriser
build/recomp-build/gsreplay.exe build/menu.gsd --compare        # fast against reference, field by field
build/recomp-build/gsreplay.exe build/menu.gsd --shots DIR      # the PCRTC's picture at every field
build/recomp-build/gsreplay.exe build/menu.gsd --profile        # where the time goes
```

## A recording, played again without the game

`PS2KIT_GS_DUMP=file[,start[,fields]]` (ps2kit `runtime/gs.cpp`) writes,
from the first vertical blank after `start` seconds, the GS's whole state
(local memory, registers, the GIF's packets in progress, a transfer in
progress, the vertex queue), then every quadword given to GIF paths 2 and 3
and a mark at each vertical blank with the PCRTC's registers.
`gsreplay` (ps2kit `runtime/gsreplay.cpp`) loads the state and plays the
packets through the same `gs.cpp`, timing only the drawing; it hashes local
memory after every field and can write each field's picture. Its pictures of
a menu recording are the menu as the game shows it.

That made the GS measurable on its own. The menu, recorded in session 5's
build (100 fields): about 80 primitives and 431 000 pixels written a field;
the background and logo are PSMT8 sprites with a CLUT, the crystals large
Gouraud triangles, perspective-textured (ST/Q, PSMCT16, 1024 x 256) or
translucent and untextured; the frame buffer is PSMCT16, the Z buffer
PSMZ16 with a GEQUAL test. Session 5's rasteriser drew it at 17 to 19
million pixels a second, 23 to 25 ms a field: more than a PAL field.

## Two rasterisers, one result

`--profile` (a sampler of the host's instruction pointer, mapped to source
lines with addr2line) showed no single culprit: every pixel decoded its
registers again, computed its addresses with five integer divisions each
(four accesses a pixel: destination, Z, their writes, and the texel), read
the CLUT through the generic pixel path for every texel, called the
library's `floor`, and divided three times for its barycentric weights.

The rasteriser now comes in two forms that must write the same memory:

* **the reference**: pixel by pixel through `put()`, which reads the
  registers there, as before;
* **the fast one**, which the runtime uses: the registers decoded once per
  primitive (`Draw`), the CLUT read once per primitive into a table, the
  edge functions stepped along each row, the pixel formats of the frame, Z
  buffer and texture folded in at compile time for the common ones
  (PSMCT32 and PSMCT16; PSMZ32, PSMZ24 and PSMZ16; PSMCT32, PSMCT16, PSMT8),
  a sprite's u computed once per column and v once per row.

What decides a pixel's value they share, so that they differ only in how
they get there: coverage, the interpolation (`tri_attr`, `spr_u`,
`spr_v`), the texel formats and the addressing (`Surf`).
`gsreplay --compare` plays a recording with each and compares local memory
after every field; at the first difference it plays that field again packet
by packet and names the packet and the bytes.

Coverage changed in both, on purpose. The edge functions were evaluated in
single precision, where a product of two coordinates in 12.4 fixed point
needs up to 30 bits: near the edges of a large screen they could round.
They are now exact 64-bit integers in 12.4 fixed point (the barycentric
weights are the edge values times one reciprocal of the area, computed
once). On the session-5 recording the new reference writes exactly the
memory the old rasteriser wrote (the same hash after 100 fields), so the
picture did not move.

| | ms a field | million pixels a second |
|---|---|---|
| session 5 | 23-25 | 17-19 |
| addresses with shifts, not divisions (same memory) | 20 | 21 |
| reference (exact edges) | 18-20 | 22-24 |
| fast | 8.5 | 50.7 |

The fast rasteriser and the reference agree after every field of both
recordings: the session-5 one (100 fields, converted to the new state
layout) and one made at full speed after the changes (150 fields, 496 000
pixels a field, 10.2 ms a field).

One difference is allowed by construction and has not happened: the fast
rasteriser reads the CLUT when a primitive starts, the reference at every
texel, so a primitive that drew over its own CLUT would differ. (The console
loads its CLUT buffer when TEX0 is written, CLD; that is still to model.)

## The GS beside the EE

On the console the GS draws while the EE runs; here it drew inside the
DMA's `sceDmaSend`, inside the vblank handler, on the game's thread. Now
(ps2kit `gs.cpp`, "the GS's own thread") what the GIF is given on paths 2
and 3 is copied into a queue and drawn by a thread of its own. DMA channels
1 and 2 end when the GS has taken the last of their data, so the game waits
for the GS where it would wait on the console (`sceDmaSync`, the channel's
interrupt), and a game that sends faster than the GS draws is held back
rather than queueing without end. SIGNAL and FINISH reach the GS's CSR and
the interrupt controller when the GS meets them; the recording's
vertical-blank marks take their place in the queue. `PS2KIT_GS_SYNC=1`
draws on the caller's thread, as before.

With the GS's 10 ms a field on another core, the game has its fields to
itself. On the menu its frame counter (`_gp - 0x64BC`) rises by 50 a
second, where it rose by one every four and a half seconds; the crystals
turn, the menu left alone leaves for the demo, and a
single short press of cross on MUSOU MODE opens the character select: the
title, the spotlight, Zhao Yun's portrait and bars. The character himself
is not there: he is drawn by VU1 (MSCAL, UNPACK V4-32 in the census from
that screen on).

## A hang it exposed: FIELD and the movie player

With the GS on its own thread, about half the runs stopped in the first
movies, for some seconds or for the rest of the run. The game was in
`sceGsSyncV`'s `VSync` (`glue.c`: clear VBON in INTC_STAT, poll it until
it is set again), called in a loop by Koei's movie player
(`kpmStartDisplay`, from `readMpeg`) until FIELD changes. Counters in the
heartbeat showed VSync returning at every blank while the kernel never took
the VBON interrupt: the poll saw the bit and cleared it first. And session
3's model changes FIELD three lines after the kernel takes VBON (the rule
DW2's own vblank handler needs, [11-boot](11-boot.md)): with the
interrupt never taken, FIELD never changed, and the loop went on until a
blank was taken by chance. The timing of the old synchronous GS had hidden
it. Now the guest's own acknowledgement of VBON (writing its bit to
INTC_STAT while it is set) counts as taking it. Six runs in a row then went
through the movies without a stop, and the synchronous mode still reaches
the menu. How the console's kernel leaves the bit for VSync to see with
the interrupt enabled is not known yet: a question for the PCSX2 trace.

## Tools

* `PS2KIT_GS_DUMP=file[,start[,fields]]`: a recording, as above.
* `gsreplay FILE [--ref] [--compare] [--shots DIR] [--repeat N] [--profile]`.
* `PS2KIT_GS_SYNC=1`: no GS thread.
