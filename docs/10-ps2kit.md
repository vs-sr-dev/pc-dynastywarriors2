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
| 7 | `b32d650`, `e5dd05e` | `runtime`: VIF1 in full and VU1 (`vif1.cpp`), one micro-mode interpreter with its pipelines for both units (`vu.cpp`), VIF1 and VU1 on their own thread, GIF path 1; `vubench`; `PS2KIT_VU1_DUMP`, `PS2KIT_VU1_VF`; the GS's CLUT buffer (CLD), DMA latencies in the heartbeat; the profiler's guest call chains; `gsreplay --vram`, `gsmem --vram`; `ghidra/Decomp.java` |
| 8 | `c56f9f3`, `ef9af43`, `9e6f1fb`, `abc0171`, `c6db732` | `runtime`: VU0 reaches VU1's VF registers from 0x4000; the fast rasteriser on worker threads (`PS2KIT_GS_THREADS`) with sync jobs and exact block sets; VU1 microcode translated to C++ (`vutrans`, `vu_ops.h`, `PS2KIT_VU1_CHECK`, `PS2KIT_VU1_INTERP`, `vubench --trans`); VIF1/GIF resets (`PS2KIT_RESETS`); `PS2KIT_TIMELINE`; `PS2KIT_VIF1_PROFILE`, `PS2KIT_GS_PROFILE`; faster VIF1 (`PS2KIT_VIF1_CHECK`) |
| 9 | `8d083c1`, `314164f`, `ba8ba3b`, `a11fb84` | `runtime`: VIF1's data and paths 1 and 2 in batches (`gs_gif_batch`); drawing jobs read texture copies (`snap_texture`) and wait at fences; a sprite's texture rectangle; channels end when the GS is given their data (`PS2KIT_GS_LAG`); the clock at time-critical priority; the fast rasteriser specialised for PSMCT32, an SSE2 bilinear sample (`roundcheck`); `profile.cpp` (`PS2KIT_GS_WORKER_PROFILE`, system libraries named); the timeline's callers, sizes and GS lag; `gsreplay --fields` |
| 10 | `224017b`, `b8c4253`, `167281b`, `c68faea`, `f88f20d` | `runtime`: interrupt handler chains in the BIOS kernel's order, stopped by a negative return; IOP modules run on an R3000 interpreter (`iop_cpu.cpp`) with the kernel libraries they import as host code (`iop_os.cpp`: threads, semaphores, event flags, interrupts, hardware timers, RPC servers, disc reads; the IOP's clock); the SPU2 (`spu2.cpp`: ADPCM voices, ADSR, both cores' mixes, reverb, IRQA, transfers; the host's audio device, `--wav`; `PS2KIT_SPU2_LOG`; `PS2KIT_IOP_SOUND=0`); CHCR's TAG field from the tag's own bits (toIPU chains ended in the wrong place); the IPU's thread spins for its next command; `PS2KIT_IPU_ZEROQW` |

Game knowledge (file formats of `LINKDATA.BNS`, `SCENE.SDF`, the game's
fixes) stays in this repository's `tools/`; only what any PS2 game could
use goes into ps2kit.
