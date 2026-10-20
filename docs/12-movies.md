# The first pictures

Session 4 took the game from its first memory card request to its first
pictures: the Koei and Midas logo movies, decoded by ps2kit's model of the
IPU and drawn by its model of the GS, in a window.

```sh
ninja -C build/recomp-build ps2run
build/recomp-build/ps2run.exe "build/image/Dynasty Warriors 2 (Europe).cue"
build/recomp-build/ps2run.exe "build/image/Dynasty Warriors 2 (Europe).cue" --headless --seconds 20 --shot 9,14 --shot-dir build/shots
```

`--shot` writes the PCRTC's picture as a BMP at the given times (seconds of
host time), with or without a window.

## The memory card: an empty slot

`MusouMCardGameStart` asks for the card in port 0 (`sceMcGetInfo`,
mcserv function 1). The slot is empty, a state a real console can be in, and
everything about the answer was read from the modules' code:

* libmc (the game's `sceMcGetInfo`, `mceGetInfoApdx`): the request carries
  port, slot, three "do you want this" flags and the EE address of a
  0xC0-byte area that the IOP fills with its own SIF DMA: type at +0, free
  clusters at +4, formatted at +0x90. `sceMcSync` reads the result word.
* MCSERV v2.06 (0xA24): it calls mcman's detection (export 21), then the
  type (39), the free space (38) and the format (22), the last two only when
  detection returned -1 or better.
* MCMAN v2.07, detection (0x804): a PS2 card probe (0x2A48: the SIO2
  status word lacks 0x1000, so 0x2C30 returns -11), then a PS1 card probe
  (0x8A94: five tries, -11), then the slot's type and format are cleared.

So the answer is -11, type 0, no free space, not formatted. The game reads
anything above -11 as "a card is there" (`LocalMcGetInfo`), shows its
no-card message and goes on with the default options. A formatted card kept
as host files is for later.

## Streaming from the disc

The movie player (Koei's `playmov.c`, built on the SDK's ezmpeg sample) uses
`sceCdStInit`, `sceCdStStart` and `sceCdStRead`: n-command 9 with
{sector, count, buffer, command, mode}. CDVDFSV v2.08 (inside
`IOPRP153.IMG`) keeps the stream itself (0x20D4): a ring of banks in the IOP
buffer the EE gives at init, filled ahead of the reader. Init, start, seek
and stop answer 1; a read answers the sectors copied in its low half and an
error in its high half. Here the drive is infinitely fast: the ring is
always full and a read gets all it asks for.

## The IPU

`ps2kit/runtime/ipu.cpp`. The game's libmpeg parses the MPEG headers itself
through FDEC, decodes variable-length codes with VDEC, has each macroblock's
blocks decoded by BDEC, does motion compensation on the EE, and converts the
finished pictures with CSC. What it expects of each register and command was
read in its code (`_ipuVdec`, `_peepBit`, `_nextBit`, `_waitBdecOut`,
`_decMB0`, `_mbAddressIncrement`, the motion vector and copy routines,
`csc.c`, `libipu.c`, the SDK's `vibuf.c`):

* VDEC's result is 0 for an invalid code, so a valid one carries its length
  in bits 31:16 (a motion code of 0 is valid); macroblock address
  increments are 1-33, 0x22 stuffing, 0x23 escape.
* BDEC writes 48 quadwords, luma as a 16x16 raster of halfwords.
* Quantiser matrices come in the stream's (zigzag) order.
* sceIpuStopDMA rewinds DMA channel 4 by IFC + FP quadwords and restores
  the bit pointer with BCLR, so every quadword in the FIFO came from the
  channel, in order.
* IPU_TOP's "fewer than 32 bits" case is counted from the bit pointer.

The rest is MPEG-2 itself: Annex B's code tables, the inverse quantisation
of 7.4, an IDCT in double precision. Two checks:

* **The code tables** are checked when the runtime starts: each table's
  share of the code space (the sum of 2^-length) must equal 1 less the
  prefixes Annex B leaves unused. This check, had it been there from the
  start, would have caught the one transcription error the session made:
  motion codes 11 to 16 written one bit short, which desynchronised the
  first B picture.
* **The pictures** against ffmpeg. libmpeg hands its finished pictures to
  CSC as 384-byte macroblocks, stored by macroblock *columns* (its
  `_motionComp0` addresses (column x height + row) x 384); with the
  runtime's `PS2KIT_IPU_DUMP`, the 73 pictures of a 20-second run of
  `KOEILOGO.PSS` compared with ffmpeg's yuv420p decode: at worst 65.8 dB,
  no sample off by more than 4, 9 pictures identical. The differences are
  IDCT rounding carried through P pictures until the next I picture; the
  IPU's own IDCT rounding is unknown, as is CSC's.

For debugging the IPU keeps aids switched on from the environment: a log of
every bit FDEC, VDEC and BDEC consume (it must equal the movie's elementary
stream, extracted with `ps2kit.pss`), the last 4096 commands printed on an
error, a log of every command. The motion-code error was found with them.

Speed: libmpeg issues several hundred thousand FDECs per movie, each
followed by a wait for BUSY to clear. Handing each to the IPU's thread cost
more than the command (62% of the time in `_waitIpuIdle64`), so the short
commands run in the writing thread when the FIFO already holds every bit
they can read. The movies now play at 25 frames a second.

**Movies started again (found in session 10).** With sound, Omega Force's
logo was late or missing: `msPlayMovie` calls `koeiPlayMovie` until it
succeeds, and it failed 24 times for that logo (4 for the PAL logo, a
number that changed from run to run). libmpeg's error callback
(`mpegError`) had set the player's abort flag: BDEC read zeros in the
middle of a slice. They came from channel 4. Koei's video buffer is a ring
of 0x800-byte slots, each behind a `ref` tag, the last one filled behind a
`refe`; `kpmViBufAddDMA` stops the channel, turns that `refe` into `ref`,
and restarts it with CHCR's TAG field set to 3 so that the DMAC goes on to
the next tag. The runtime decides from that field whether a restarted
chain ends, and it filled the field with the tag's bits 47:32 (the low
half of the tag's address: a shift by 16 before the mask) instead of its
bits 31:16. So whether a `refe` ended the chain depended on where the slot
lay; past it, stale slots went to the IPU. Fixed (in the generic chain
too); no restart since, each movie's stream started once.
`PS2KIT_IPU_ZEROQW` logs all-zero quadwords taken by channel 4.

## KOEIADS's host transfer

The player hands the movie's audio (SPU ADPCM, 44.1 kHz stereo in
`KOEILOGO.PSS`) to the IOP, and starts showing pictures only once a full
IOP buffer has been sent. The old silent stand-in answered zeros, a buffer
of size 0, and the player divided by it. KOEIADS v1.05's own code gives the
protocol: 0x9901 sets the buffer (H a multiple of 0x800; here 32 blocks of
0x800), 0x990F answers 2H, 0x9914 answers the host buffer's address while
the SPU side has room for H more bytes, 0x9915 queues the bytes written.
The SPU2's playback that frees the room is replaced by a clock at the
stream's byte rate. The sound itself is phase 5.

## The GS and the window

`ps2kit/runtime/gs.cpp`, `display.cpp`. The movie player uploads each
macroblock with a host-to-local transfer (16x16, PSMCT32) into the buffer
not shown, and its vblank handler swaps the two with `sceGsPutDispEnv`.
The GS model takes path 3 (GIF DMA and the GIF FIFO), PACKED, REGLIST and
IMAGE data, transfers, and draws with a software rasteriser; local memory
uses ps2kit.gsmem's layouts. The picture shown comes from PMODE, SMODE2,
DISPFB and DISPLAY. One point was read rather than guessed: libgraph's
`sceGsSetDefDispEnv` sets DH to the height minus one when SMODE2's FFMD
is clear, and to twice the height minus one when it is set; so with FFMD
the buffer holds half of DH + 1 lines, read by both fields.

The first picture: the Koei logo, 640x512, then "KOEI PRESENTS", then
Midas's logo; confirmed by the user in the window.

## Where it stops now

A two-minute run with a screenshot every ten seconds goes through the Koei
and Midas logos and into the opening movie, which is still playing at two
minutes, with no unmodelled feature met. What follows (the title screen)
is the next piece; it will want VIF1 and VU1, the rest of the GS, the
sound. See [07-next-session](07-next-session.md).
