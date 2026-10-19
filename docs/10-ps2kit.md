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

Game knowledge (file formats of `LINKDATA.BNS`, `SCENE.SDF`, the game's
fixes) stays in this repository's `tools/`; only what any PS2 game could
use goes into ps2kit.
