# TODO — session 2

Phase 1 of [06-attack-plan](06-attack-plan.md): the translator.

1. `ps2kit.recomp`, first cut: one C++ function per entry of
   `build/map/symbols.tsv`, branch labels, delay slots (likely branches on the
   taken path only), `jal` direct, `jr ra` return, `jalr`/`jr` through a
   dispatch table; the guest state struct; one helper per operation of the
   census. Goal: all 4 073 functions compile and link (a stub runtime is
   enough).
2. Switch tables: find the `jr` that are not `jr ra` (there are
   3 986 `jr`; how many are tables?), size them from the bounds check before
   them, read their targets from `.rodata`.
3. `ps2kit.eeemu`, a reference interpreter in Python, and the first
   differential tests on leaf functions of the game (`memcpy`, `strlen`,
   `strcmp`, the soft-float routines in `dp-bit.c`/`fp-bit.c`, `sqrtf`).
4. The FPU's PS2 rules (no denormals, no inf/NaN, clamping): write them down
   with a source for each, test them in the interpreter and the helpers.

5. `ps2kit.fingerprint`: report whether each executable is stripped
   (`.symtab` functions, `.mdebug`), so a candidate game's luck is known at
   once. Of the three PS2 games so far only this one keeps its symbols
   (Extermination: an empty `.symtab`; Evergrace: none).

Decided after session 1:
* ps2kit and this repo go public on GitHub, but only once the recompiler
  shows something.
* PCSX2 is the behaviour oracle: a portable 2.9.129 build
  (BIOS dumps beside it).
