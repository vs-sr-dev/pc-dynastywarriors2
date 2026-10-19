# The route

A native PC port by **static recompilation with ps2kit's own recompiler and
runtime**. Dynasty Warriors 2 is the first game of that recompiler: until
now ps2kit covered recognition, extraction and code mapping, and the one PS2
game that runs (Extermination) runs on PS2Recomp's runtime with our patches.
From here, layers 4 and 5 are written in ps2kit, the way wiikit's were with
Victorious. PS2Recomp, PCSX2 and the open PS2SDK are read for method and
behaviour, never copied.

## Why this game fits

* **The executable is not stripped**: function boundaries and sizes for all
  4 073 functions, the source file of each, frame sizes, the names of every
  SDK function linked in. No function discovery, no signature matching; the
  recompiler can be judged on translation alone.
* **No overlays**: one executable, loaded once.
* **A CD** of 570 MB and 50 files, all read as ordinary Form 1 data.
* **The SDK is linked with names**, so every boundary where the runtime may
  take over (kernel syscalls, SIF RPC, libgraph, libpad, libmc, the CD
  library, libmpeg) is visible by name.
* The hard parts are real but bounded: VU1 microcode drives the 3D, Koei's
  own IOP sound drivers, PSS movies through a player of the game's own.

## Phases

Each phase ends on something checked, not on something that looks right.

### 1. The translator (ps2kit layer 4)

`python -m ps2kit.recomp SLES_500.57 --functions symbols.tsv --out build/recomp`

* One C++ function per EE function, labels for branch targets, the delay
  slot emitted where it belongs (and for likely branches only on the taken
  path), `jr ra` as return, `jal` as a direct call, `jalr` and computed jumps
  through a dispatch table of every function start.
* Guest state: 32 GPRs of 128 bits, HI/LO and HI1/LO1, SA, 32 FPRs, ACC and
  FCR31, VU0's 32 vector and 16 integer registers, ACC, Q, I, P and flags.
* Instruction semantics as small inline helpers, one per operation in the
  census (202): the integer core, MMI, the FPU (with the PS2's own rules: no
  denormals, no infinities or NaNs, clamping), VU0 macro mode.
* Switch tables found in `.rodata` and sized from the code.

Check: every function compiles and links. Then **differential tests**: a
small reference interpreter in Python (`ps2kit.eeemu`, the same role as
saturnkit's `sh2emu` and ndskit's `armemu`) runs leaf functions of the game
(`memcpy`, `strlen`, `sprintf`, `sqrtf`, the soft-float `dp-bit` routines,
matrix code) on random inputs, and the recompiled C++ must give the same
registers and memory.

### 2. Boot (ps2kit layer 5 begins)

C++20, SDL3, OpenGL 4.5, as in the sibling kits.

* Memory: 32 MB RAM, the 16 KB scratchpad, hardware registers as handlers.
* The EE kernel at the `syscall` boundary (`klib.s` names the calls):
  threads, semaphores, interrupt handlers, alarms, `SifSetDma`.
* `crt0` → `main` → the game's own init, until it waits for the IOP.

Check: the game's own debug output (`printf` through `kprintf`/`tty`) on
the host console, in the order the code implies.

### 3. The IOP side, at the SIF RPC boundary

The IOP's modules are not run; their RPC servers are replaced on the host:
file I/O and `sceCd*` (`cdvdfsv`), pads (`padman`), memory cards (`mcserv`),
`libsd`, and Koei's two sound drivers. The EE side of each (the SDK's
`sceSifCallRpc` callers) runs recompiled unchanged. `ps2kit.irx` reads the
modules' export tables to name what each server must answer.

Check: `LINKDATA.BNS`, `SCENE.SDF` and the movies opened and read where the
code asks, in the order a trace of the real game shows.

### 4. Pictures

* DMA channels, GIF paths 1–3 and the GS as an OpenGL renderer;
  `ps2kit.gsmem` already models GS local memory and its formats.
* VU1 micro mode, from the microcode the game uploads through VIF1: an
  interpreter first (`ps2kit.vu` has the tables), recompiled later if the
  frame time asks for it. VU0 micro mode for the nine `vcallms` routines.
* Movies: libmpeg and libipu are in the executable; the IPU or the
  `sceMpeg*` boundary, whichever the first movie shows to be simpler.

Check: the Koei and PAL logos, the title, the first battle, against the
same screens from an oracle (below).

### 5. Sound, input, saves

`BGM.BNS` and the sound drivers' banks on a host mixer (checked by ear, as
always), pads from SDL3, memory cards as files.

## Oracles

* **The data itself**: symbols, `.mdebug`, the code's own checks.
* **Ghidra** with ghidra-emotionengine-reloaded, as a second decoder (done for
  `ps2kit.ee`) and to decompile when reading a function.
* **PCSX2**, for behaviour: screenshots and video of the same moments, and
  traces (file reads, RPC calls, GS registers) where a phase needs them
  (2.9.129).
* **The user's own console and disc**, for what only the real thing can
  settle.

## What carries over from Extermination

Extermination's runtime patch for PS2Recomp is our code and our findings,
and those findings are facts about the SDK and the hardware, so they hold
here too. The SDK's GNU `crt0` asks `SetupThread` for stack −1. Priority 0
is a valid thread priority. A DMA chain started with `QWC > 0` sends those
quadwords first. Tag addresses with bit 31 set are in the scratchpad.
`sceGsExecLoadImage` takes `dbp` in blocks. `sceGsSetDefDispEnv` fills PMODE
and SMODE2. Vblank pacing follows the host clock. These come in as knowledge,
re-implemented in ps2kit's runtime. Extermination itself moves from
PS2Recomp to ps2kit in its own pipeline, once ps2kit's runtime boots this
game.
