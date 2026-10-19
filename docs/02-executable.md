# The executable

`SLES_500.57`: an EE ELF, entry `0x00200008`, one loaded segment at
`0x00200000` (1.9 MB in the file, 3.0 MB in memory). Built with the SDK's
ee-gcc 2.9x (`/usr/local/sce/ee/gcc/build/...`), linked against SDK 1.5.x
libraries (libkernel 1530, libcdvd 1530, libmc 1510, libmpeg 1510).

**It is not stripped.** It keeps:

| Section | What it gives |
|---|---|
| `.symtab` / `.strtab` | 6 964 symbols: 3 737 functions with sizes, globals and statics with sizes, C++ names in GCC 2.9x mangling |
| `.mdebug` | the ECOFF symbolic table: 508 source files, 4 056 procedures with frame sizes and saved-register masks, 21 516 local symbols |
| `.stab` | a little more debug information (not read yet) |
| `.DVP.*` | the VU assembler's overlay tables for the microcode |

## Sections

| Section | Address | Size |
|---|---|---|
| `.text` | 0x00200000 | 0x12E228 |
| `.vutext` | 0x0032E230 | 0x3F60 (VU1 microcode in DMA/VIF packets) |
| `.data` | 0x00332200 | 0x9B210 |
| `.vudata` | 0x003CD500 | 0x1E00 (VU microcode, `MPG_Start`…`MPG_End`) |
| `.rodata` | 0x003CF300 | 0x145D9 |
| `.gcc_except_table` | 0x003E3900 | 0x148 (C++ exceptions) |
| `.lit4`, `.sdata` | 0x003E3A80 | |
| `.sbss`, `.bss` | 0x003E6800 | 0x11B254 |

## Code

The game is codenamed **pale**: its sources were built from
`/HD/home2/morinaka/pale/sc/`. In order of address:

* **The game, in C** (83 files): `main.c`, `system.c`, `view.c`, `texture.c`,
  `cdlib.c`, `gmain.c` … the battle (`unitalgo`, `grpalgo`, `attack`,
  `comalgo`, `collisionf`, `horse`, `arrow`, `effect`, `particle`), the
  officers' and soldiers' control (`gobcon`, `fobcon`, `mobcon`, `cobcon`),
  the stage, minimap, events (`event`, `evefunc`, `eveffect`), briefing,
  options, memory card, character select, ending, title, the HUD (`gagedisp`,
  `killcnt`, `timedisp`).
* **Scenes and effects, in C++** (`BaseScene`, `Scene00`–`Scene10`,
  `SceneManager`, `OpeningManager`, `StageRender`, `ModelObj`, `HumanObj`,
  `HorseObj`, a cloth simulation in `ClothObj` and `EulerClothObj`, managers
  for textures, sprites, lights, the camera and memory). Their header
  inlines are emitted as static copies in every file that uses them: 336
  procedures that only `.mdebug` names.
* **The SDK, linked in with its names**: libgraph (`graphdev.c`), libdma,
  libvu0, libvif/gif packets, libpad, libmc, the CD library (`eecdvd.c`), a
  movie player built on libmpeg and libipu (`playmov.c`, `videodec.c`,
  `audiodec.c`), Koei's EE-side sound libraries (`kessound.c`,
  `koeiads.c`), the kernel's syscall stubs (`klib.s`), SIF DMA, commands and
  RPC, file I/O stubs, IOP heap and module loading, newlib, GCC's soft-float
  for doubles (`dp-bit.c`, `fp-bit.c`).

The function map (`python -m ps2kit.elf SLES_500.57 --functions
build/map/symbols.tsv`) has 4 073 entries and tiles `.text` exactly: no
overlap, every gap all zero. A recompiler needs no function discovery for
this game.

## Instructions

`python -m ps2kit.ee SLES_500.57 --census`: 307 646 instructions, 202
distinct operations, none unknown. Equal to Ghidra's EE decoder
(ghidra-emotionengine-reloaded) on every instruction up to aliases and
notation, and on all 40 425 branch and jump targets.

What the recompiler must handle, from that census: 64-bit integer work
everywhere (`daddu` is the compiler's move, `ld`/`sd` its spills), 128-bit
`lq`/`sq` and MMI (`por`, `pcpyld`, `pextlw`…), the single-precision FPU
with its accumulator ops, branch-likely forms (`beql` and `bnel` alone: 3 836), 731
`break`s (GCC's divide-by-zero traps), unaligned `ldl`/`ldr`/`sdl`/`sdr`
(483 each), and VU0 in macro mode (`lqc2`/`sqc2`, `qmtc2`/`qmfc2`, `vadd`,
`vmul`…, 438 `vcallms`).

## VU microcode

The microcode is symbolised too (labels from the VU assembler):
`Stage_initialize_code`, `Stage_base_code`, `_$RotTransPers`, `_$CLIP`,
`_$DRAW_POLY`, `_$MODEL_LOOP`, `_$LOCUS_LOOP` … The EE calls nine VU0
micro-subroutines with `vcallms` (addresses 0x00 to 0x80 in VU0 micro
memory), from movement and minimap code (`check_move`, `revise_angle`,
`set_minimap_unit_map` …). The rest is VU1 rendering microcode, uploaded
through VIF1.
