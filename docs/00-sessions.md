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
