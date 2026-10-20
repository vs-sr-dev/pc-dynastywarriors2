# A battle list within its field

Session 9 went after the latency of one list ([16-speed](16-speed.md) left
the attract-mode battle with about half its fields reset by the game). Each
step was found with the timeline or a thread profile, and each change to
the rasteriser was held to the reference with `gsreplay --compare`.

```sh
# who starts each transfer, its size, VIF1's end, the GS's lag at each blank
PS2KIT_TIMELINE=1 build/recomp-build/ps2run.exe "build/image/Dynasty Warriors 2 (Europe).cue" \
    --headless --seconds 62 --press 8:START,10:START,12:START,14:START,16:START,18:START,20:START,22:START
# a thread's profile (offsets for nm; system libraries by name)
PS2KIT_PROFILE_FROM=48 PS2KIT_VIF1_PROFILE=v.txt ...   # or PS2KIT_GS_PROFILE, PS2KIT_GS_WORKER_PROFILE
# a recording's fields one by one; the rasteriser's rounding on every float
build/recomp-build/gsreplay.exe build/s9/battle.gsd --fields
build/recomp-build/roundcheck.exe
```

## How the game sends a field

`main_callback`, at each vertical blank, sends the SDK's double-buffer
packet (path 3) and a 4-quadword VIF1 list; the main thread (`RunOpening`
in the attract mode) then sends its own swap packet and the frame's list:
about 190 000 to 260 000 quadwords on VIF1, some 25 000 DMA tags. At the
next blank the callback asks `sceGsSyncPath` whether both channels are
idle, and resets the GS if not. With the lists fast enough the game sends
one every field (50 a second), where it sent one every two before.

## What took the time, in order

1. **VIF1's queue.** Each DMA tag was one item for VIF1's thread (an
   allocation, the queue's lock, the thread woken): the thread waited more
   than it worked, and a list took 33 ms. A chain's transfers now go in
   batches of 64 KB, the segments noted; 24 ms.
2. **The GS's queue.** XGKICK packets went to the GS at the end of each
   transfer, some 10 000 items a list. Paths 1 and 2 now go together
   (`gs_gif_batch`) at the end of each batch; VIF1's timers read the time
   stamp counter. A list's time in VIF1: about 7 ms.
3. **Sync jobs.** About 70 texture transfers a field land where textures
   drawn just before were read; each was deferred into a sync job that
   stopped every drawing thread. A job now reads its texture from a copy
   made when it is handed out (`snap_texture`), copied again only after
   writes to its pages (by the transfers, the targets of the jobs handed
   out, all memory for what the GS's thread draws itself); a copy still
   read is put aside. No transfer is deferred in a battle any more.
4. **Drawn alone.** The feedback copy (the frame, 640 x 256, to 0x1E00)
   was drawn alone: its texture was taken as 1024 wide and so reached the
   Z buffer. A sprite's texture is now the rectangle its coordinates reach;
   and that copy reads a few filtered texels of the Z buffer, which it only
   tests, so a texture overlapping a Z buffer is a conflict only when the Z
   buffer is written.
5. **The channel's end.** A channel ended only when the GS had taken all
   its data; the host's GS, behind, made the game see busy channels. As on
   the console, a channel now ends when VIF1 or the GIF has handed its data
   on: everything reaches the GS through one queue, in order (a texture
   sent after a list, a read of local memory, the picture of a blank all
   wait for what came before), so the guest sees the GS's progress only in
   time. When the GS's thread is more than `PS2KIT_GS_LAG` ms behind
   (default 20; 0: always), a channel waits for the GS as before, so a game
   that sends faster than the GS draws is held back.
6. **The GS's thread waiting.** Jobs that must follow pending jobs (a
   texture read in place, a target others use) made the GS's thread wait;
   they are now fences the drawing threads wait at, and the GS's thread
   goes on decoding.
7. **A late blank.** With the drawing threads busy, the clock thread was
   once not run for 10 ms: a blank came late and the next field was short.
   The clock runs at time-critical priority.
8. **The pixels.** The fast rasteriser marked "a format it is not
   specialised for" by 0, PSMCT32's own number: 32-bit frames and textures,
   the commonest, always took the generic path (now `ANY`). The bilinear
   sample filters the four channels together in SSE2; its rounding equals
   the reference's for every float in [0, 256) (`roundcheck` tries all 1.1
   billion; the obvious `r + 0.5f` differs at 0.49999997). Transfers write
   a row at a time; copies take only the texture's blocks; spans of
   finished jobs are trimmed every 16 jobs.

## Where it stands

`build/s9/battle.gsd` (100 fields of the attract battle):

| | one thread | eight drawing threads |
|---|---|---|
| start of the session | 32.7 ms a field | 12.3 ms |
| end | 23.4 ms | 5.3 to 5.9 ms |

The attract battle, about 15 seconds: some 745 lists, 2 to 7 of them cut by
the game's reset (about half the fields at the start). The GS's lag at a
blank is 0 most of the time, 13 to 15 ms at the 99th percentile; the cuts
left come from bursts (the battle's first second, many CLUT changes) where
the drawing threads fall more than a field behind. `gsreplay --compare`:
equal on every field of five recordings (`build/s9/battle.gsd`,
`build/s9/menu.gsd`, `build/s7/cs3.gsd`, `demo4.gsd`, `demo5.gsd`) with 0, 2,
4 and 8 drawing threads. `PS2KIT_GS_THREADS` defaults to half the host's
hardware threads (2 to 8); on the 12th-gen Core this was measured on (6
performance cores and 4 efficient ones) 8 did best.

## Open: the battle's picture

The attract battle shows only the lower half of its picture; the upper half
is green or black. Not new (it is in session 7's recordings, and session 6
saw "green and black areas" there before VU1 drew the models), and not a
rasteriser fault: local memory is the reference's.

What happens, from the GS's packets: the battle draws in 32-bit buffers of
640 x 256 at 0 and 0xA0000, Z at 0x140000, and shows them with PMODE
0xBE66 (`sceGsSwapDBuff` on `g_gsDBuff`). But `main_callback` still sends
the SDK's double buffer every blank (`sceGsSwapDBuffDc` on `gpDBuffPtr`,
set up by `set_main_graph` as PSMCT16 640 x 256 at 0 and 0x50000, PSMZ16 at
0xA0000, with its clear sprite), and that clear lands in the battle's
buffers: its colour (16-bit black, 0x8000, which read as 32-bit is green)
into half of buffer 0, its Z (zero) into the top half of buffer 0xA0000.
After each field the buffer just drawn is whole; the buffer PMODE/DISPFB2
name for the field (drawn the field before) has lost its top half. The
packets are the game's own (`gbDrawFlag` stays 1, `gpDBuffPtr` is only set
by `set_main_graph`, GIF_MODE is never written), so the console receives
the same; what differs must be when or what the PCRTC shows. To settle with
PCSX2 (its software renderer): does the attract battle show the whole
picture, and which buffer.
