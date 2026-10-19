# ps2kit in this port

ps2kit is a submodule at `ps2kit/`, from
[github.com/vs-sr-dev/ps2kit](https://github.com/vs-sr-dev/ps2kit) (clone
this repository with `--recurse-submodules`). Run its tools from the repository
root: `python -m ps2kit.<module>`.

## What this game asked of it

| Session | ps2kit commit | Added |
|---|---|---|
| 1 | `05532fe` | the split from pc-extermination; `disc` (CD images, `SYSTEM.CNF`), `elf` symbols and function map, `mdebug`, `ee` (the R5900 decoder), `ghidra/ExportListing.java` |
| 2 | `ca47262` | `recomp` (the translator to C++), `runtime` (ee.h, memory and dispatch, stub, link check, difftest driver), `eeemu` (reference interpreter), `recomp.difftest`, `fingerprint` reports symbols |
| 3 | `0db071d`, `11d5ef6` | `runtime`: `ps2run` (boot from the disc image), the EE kernel at the syscall boundary, the hardware registers, the IOP at the SIF boundary with the RPC servers this game calls up to its memory card, the disc image reader, heartbeat and profiler |
| 4 | `6232b9b`, `a63f37c`, `bacc163`, `da05a5c` | `runtime`: the IPU (`ipu.cpp`), the GS with a software rasteriser and the PCRTC (`gs.cpp`), an SDL3 window and screenshots (`display.cpp`); mcserv with an empty slot, CDVDFSV streaming, KOEIADS's host transfer; `recomp.difftest` takes the MinGW path from `PS2KIT_MINGW_BIN` |
| 5 | `1427bfc` | `runtime`: the pad from the host (`input.cpp`, `--press`), VIF0 and VU0's micro mode (`vu0.cpp`), VIF1's census and GIF path 2 (`vif1.cpp`), `sceCdReadClock`, vf0 = (0, 0, 0, 1), `PS2KIT_WATCH`; VU0 MAX/MINI and DIV/SQRT/RSQRT rules in `recomp` and `eeemu` |
| 6 | `79c615c`, `fa1d37f` | `runtime`: GS recordings (`PS2KIT_GS_DUMP`) and `gsreplay` (replay, timing, pictures, a host profiler, `--compare`); the rasteriser as a reference and a fast form checked against it, exact edge functions; the GS on its own thread (`PS2KIT_GS_SYNC`); FIELD after the guest's own VBON acknowledgement; the picture taken at each vertical blank, interlaced fields blended (`PS2KIT_DEINTERLACE`); DMA starts on STR's edge; local-to-host transfers |

Game knowledge (file formats of `LINKDATA.BNS`, `SCENE.SDF`, the game's
fixes) stays in this repository's `tools/`; only what any PS2 game could
use goes into ps2kit.
