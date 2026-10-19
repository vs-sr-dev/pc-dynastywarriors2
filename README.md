# pc-dynastywarriors2

Toward a native PC port of **Dynasty Warriors 2** (PlayStation 2, Omega
Force / Koei, 2000), by static recompilation.

It is the first game of **ps2kit**'s own recompiler and runtime: the
toolkit that grew inside [pc-extermination](https://github.com/vs-sr-dev/pc-extermination)
now stands on its own ([ps2kit](https://github.com/vs-sr-dev/ps2kit), submodule `ps2kit/`), and this port is where its
translator from EE code to C++ and its runtime are being written.

## BYOA — Bring Your Own Assets

This repository contains **documentation and tools only**. No game data, no
executables, no assets. You need your own original disc. The work is done on
the PAL release, SLES-50057.

## Layout

    docs/     disc, executable, the route, the session log
    tools/    game-specific tools
    ps2kit/   the game-agnostic PS2 toolkit (submodule)

## Getting started

Python 3.8+, no dependencies.

```sh
python -m ps2kit.disc "Dynasty Warriors 2 (Europe).cue" --extract build/disc
python -m ps2kit.fingerprint build/disc --deep
python -m ps2kit.elf build/disc/SLES_500.57 --functions build/map/symbols.tsv
python -m ps2kit.ee build/disc/SLES_500.57 --census --functions build/map/symbols.tsv
```

Running the game needs the recompiled code built (CMake, Ninja, clang, SDL3;
MSYS2's MinGW 64-bit environment so far, see [docs/09-recompiler.md](docs/09-recompiler.md)):

```sh
python -m ps2kit.recomp build/disc/SLES_500.57 --out build/recomp
cmake -S build/recomp -B build/recomp-build -G Ninja -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_CXX_COMPILER=clang++ -DCMAKE_CXX_FLAGS_RELEASE=-O1
ninja -C build/recomp-build ps2run
build/recomp-build/ps2run "build/image/Dynasty Warriors 2 (Europe).cue"
```

## Status

Session 1: the disc and the executable are mapped. The executable is not
stripped: 4 073 functions with their sizes and source files tile its code
exactly, and ps2kit's new EE decoder reads all of it the same way Ghidra
does. Session 2: ps2kit's translator turns all of it into C++ that compiles
and links, and the recompiled functions match a reference interpreter
register for register and byte for byte (2 311 differential runs, none
different). Session 3: ps2kit's runtime boots the recompiled game from the
disc image, through the IOP's reboot and module loading, file reads, pad and
sound initialisation, into its own 50 Hz frame loop, up to its first memory
card request ([docs/11-boot.md](docs/11-boot.md)). Session 4: the memory
card (an empty slot), streaming from the disc, ps2kit's models of the IPU
(checked against ffmpeg on the game's movies) and of the GS, and a window:
the game shows its first pictures, the Koei and Midas logo movies
([docs/12-movies.md](docs/12-movies.md)). Session 5: input from the host
(keyboard, gamepad, scripted presses), VU0's micro mode (checked against
libm on the game's own trigonometry library), VIF1's direct path to the GS:
the title screen and its menu ([docs/13-title.md](docs/13-title.md)).
Session 6: a GS rasteriser 2.5 times faster, checked against a reference
form of itself field by field, and the GS on its own thread: the menu runs
at full speed and opens the character select
([docs/14-gs-speed.md](docs/14-gs-speed.md)).
See [docs/00-sessions.md](docs/00-sessions.md) for the log, [docs/06-attack-plan.md](docs/06-attack-plan.md) for the route
and [docs/07-next-session.md](docs/07-next-session.md) for what is next.

## Documentation

    00-sessions.md      progress log
    01-disc-layout.md   what is on the CD
    02-executable.md    the executable, its symbols, its code
    04-curiosities.md   what the disc reveals about its making
    06-attack-plan.md   the porting route
    07-next-session.md  the plan for the next session
    09-recompiler.md    the translator and how it is checked
    10-ps2kit.md        what this port asked of ps2kit
    11-boot.md          the runtime's boot, what the game does, what it showed
    12-movies.md        the memory card, streaming, the IPU, the GS: the first pictures
    13-title.md         input, VU0's micro mode, VIF1 and GIF path 2: the title screen
    14-gs-speed.md      the GS's recordings, two rasterisers, the GS's thread: the character select

## Licence

MIT — see [LICENSE](LICENSE). This covers the documentation and tools in this
repository only. It says nothing about Dynasty Warriors 2 itself, which
remains the property of its rights holders.
