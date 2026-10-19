# Session log

## Session 1 — the disc, the executable, ps2kit on its own

Goal: start the port and the recompiler it is the first case for; see what
the disc and the executable give.

Results:

* **ps2kit split out of pc-extermination** with its history (`git subtree
  split`), as agreed for the second game on the kit: a repository of its
  own beside this one, a submodule here. Not published yet.
* **Disc read** (`ps2kit.disc`, new, adapted from saturnkit's reader): a CD
  of MODE2/2352 data and one CD-DA track, which is silence. All 276 830 data
  sectors' subheaders read: Form 1 only. 50 files extracted
  ([01-disc-layout](01-disc-layout.md)).
* **The executable is not stripped**: `.symtab`, `.mdebug` (508 source
  files, the codename "pale"), `.stab`, VU microcode labels. New in ps2kit:
  `mdebug`, and in `elf` the function map: 4 073 functions that tile
  `.text` exactly ([02-executable](02-executable.md)).
* **ps2kit.ee**, the R5900 decoder, written from the encoding tables: all
  307 646 instructions of the game decoded (202 operations) and equal to
  Ghidra's EE decoder, up to aliases and notation, on every instruction and
  on all 40 425 branch and jump targets. ps2kit no longer needs Ghidra to
  read EE code; Ghidra stays as a second reader (`ghidra/ExportListing.java`).
* **The route** ([06-attack-plan](06-attack-plan.md)): ps2kit's own
  translator and runtime, with this game as their first case.
* Six curiosities ([04-curiosities](04-curiosities.md)), among them
  Kessen's sound driver and the "pale" codename.

One claim was corrected before it was written down: the first draft of the
kit's check table said every `.mdebug` procedure sits at the `.symtab`
address of its name. Checked, 3 720 do; the other 336 are later static copies
of C++ inlines, which `.symtab` names only once.

## Session 2 — the translator, checked function by function

Goal: phase 1 of the plan, ps2kit's own translator from EE code to C++.

Results:

* **`ps2kit.recomp`** (program model, emitter, driver; adapted in shape
  from wiikit's): all 4 073 functions and 307 646 instructions translate,
  none unsupported; 142 switch tables resolved and sized by their bound
  checks; 821 tail calls; one jump into a delay slot handled. 27 MB of C++
  in 38 files, compiled and linked by clang at `-O1` in about 20 seconds,
  no error and no warning ([09-recompiler](09-recompiler.md)).
* **`ps2kit/runtime`** begins: `ee.h` (the guest as the generated code
  sees it: 128-bit registers, memory, the FPU and VU0 helpers), memory and
  dispatch, a stub, the link check.
* **`ps2kit.eeemu`**, a reference interpreter in Python, and
  **differential tests** (`ps2kit.recomp.difftest`): the recompiled C++
  against the interpreter, every register and every byte of memory.
  56 named functions (string routines, 64-bit arithmetic, the SDK's soft
  float, `sprintf`, libvu0) × 10 states: 560 runs, all equal. Every leaf
  function of the game (1 080) fuzzed with two states: 1 751 runs, all
  equal, 409 skipped (the reference could not finish them). Together they
  exercise 179 of the 202 operations the game uses; 7 of the other 23 are
  system operations, which need the runtime.
* **The FPU and VU model** set to PCSX2's default, which the user's
  PCSX2 uses too: round toward zero, no denormals, no infinities or NaNs.
  The reference computes it exactly (rationals, truncated to 24 bits).
* **`ps2kit.fingerprint`** says whether an executable kept its symbols: of
  the three PS2 games so far only this one did.
* **The kernel surface** measured for phase 2: 53 syscall stubs the game
  calls, numbers and names from the SDK's own `klib.s`.

What the tests caught, in order. A dispatch bug in the reference (`vmr32`
and `vmove` share an operand form with `vabs` and fell into its branch).
Wrong cases (float arguments go in `$f12`, integer arguments five to eight in
`t0`–`t3`), and one fix that never landed because a bash heredoc ate its
backslashes. The reference's exact round-toward-zero arithmetic losing the
sign of exact zeros. In every case the recompiled side was right.
