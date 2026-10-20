# TODO — session 9

Where session 8 left the game ([16-speed](16-speed.md)): the character
select is right with no preset; VU1's programs run as translated C++, the
GS draws on worker threads, VIF1 is faster. The attract mode's battle draws
more frames, but one large list in two still outlasts its field: the game
resets and that field shows the PCRTC's 32-bit default (green or striped).

Before running: make the VU1 translations (they are game data, kept in
`build/`): dump with `PS2KIT_VU1_DUMP` in the battle and the character
select, run `vutrans`, rebuild (commands in [16-speed](16-speed.md)).
Without `build/recomp/vu1_trans.cpp` everything still runs, interpreted.

1. **One list's latency.** A large list takes VIF1 about 14 ms, and the
   GS's decoding and drawing follow behind; it must end within ~17 ms of
   its start. Measure with `PS2KIT_TIMELINE` (start, `vif1done`, end) and
   the profilers. Ideas: VIF1's code walk (a profile showed the walk
   itself, after UNPACK, as large as VU1); the GS's decoding (per-vertex
   work, `fast_prim`, job size); fewer sync jobs (whole transfers instead
   of each packet's share); GS decoding beside VIF1 for path 1 (a second
   decode thread is not possible, the GIF is one stream, but less work per
   packet is).
2. **The PCRTC's feedback blur** (`g_FeedBackPCRTC`, `g_SetBlurPCRTC`,
   `SetFeedBack`): decompiled in session 8 (EXTBUF 0x1429E00: EXBP 0x1E00,
   EXBW 10, WFFMD 1, EMODA 2; FBIN 0, the merged picture written back to
   the buffer circuit 1 reads, ALP 0xBE). Not seen in the attract battle's
   window; find where the game turns it on.
3. **Sound (phase 5).** Koei's two IOP drivers (KESSOUND, KOEIADS); an SPU2
   model; check by ear.
4. Once lists fit: `PS2KIT_RESETS=1` by default (the console's behaviour).
5. From before: battles look dark (compare with PCSX2), the GS's Z and
   PSMCT16S layouts, CSM2, mipmaps, the memory card with data.

Open points:
* `vutrans` translates only what a dump saw (64 micro images at most);
  others run interpreted. A JR to an address not after a BAL/JALR stops.
* The deferred-transfer and alone sync jobs make every drawing thread wait
  for the slowest (about 2 s of 20 per 5 s in a battle).
* The EFU's ESIN, EATAN and EEXP use the host's library.

Restarting: as before (ps2kit in its own checkout; build with
`ninja -C build/recomp-build ps2run gsreplay vubench vutrans linkcheck difftest`).
Start every two seconds from 8 to 22 reaches the menu; cross at 28 opens
the character select; no cross, and the attract battle starts at about 45 s.
Edit scripts with backslashes go into files (Write), never a heredoc.
