# pc-dynastywarriors2

Toward a native PC port of **Dynasty Warriors 2** (PlayStation 2, Omega
Force / Koei, 2000), by static recompilation.

It is the first game of **ps2kit**'s own recompiler and runtime: the
toolkit that grew inside [pc-extermination](https://github.com/vs-sr-dev/pc-extermination)
now stands on its own (submodule `ps2kit/`), and this port is where its
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

## Status

Session 1: the disc and the executable are mapped. The executable is not
stripped: 4 073 functions with their sizes and source files tile its code
exactly, and ps2kit's new EE decoder reads all of it the same way Ghidra
does. Next: the translator. See [docs/00-sessions.md](docs/00-sessions.md)
for the log, [docs/06-attack-plan.md](docs/06-attack-plan.md) for the route
and [docs/07-next-session.md](docs/07-next-session.md) for what is next.

## Documentation

    00-sessions.md      progress log
    01-disc-layout.md   what is on the CD
    02-executable.md    the executable, its symbols, its code
    04-curiosities.md   what the disc reveals about its making
    06-attack-plan.md   the porting route
    07-next-session.md  the plan for the next session
    10-ps2kit.md        what this port asked of ps2kit

## Licence

MIT — see [LICENSE](LICENSE). This covers the documentation and tools in this
repository only. It says nothing about Dynasty Warriors 2 itself, which
remains the property of its rights holders.
