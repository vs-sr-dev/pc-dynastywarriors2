# The recompiler

ps2kit's translator from EE code to C++ (`ps2kit/recomp`), its runtime
interface (`ps2kit/runtime/ee.h`) and how it is checked, with Dynasty
Warriors 2 as the first case.

```sh
python -m ps2kit.recomp build/disc/SLES_500.57 --out build/recomp
cmake -S build/recomp -B build/recomp-build -G Ninja -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_CXX_COMPILER=clang++ -DCMAKE_CXX_FLAGS_RELEASE=-O1
ninja -C build/recomp-build linkcheck difftest
python -m ps2kit.recomp.difftest build/disc/SLES_500.57 --driver build/recomp-build/difftest.exe
python -m ps2kit.recomp.difftest build/disc/SLES_500.57 --driver build/recomp-build/difftest.exe --leaves --seeds 2
```

(Run from the directory that holds the `ps2kit` checkout being worked on;
clang, cmake and ninja from MSYS2's MinGW 64-bit environment.)

## The program

`program.py` takes the function map (`ps2kit.elf.functions()`: `.symtab`
and `.mdebug`) and decodes every function with `ps2kit.ee`. For this game:

| | |
|---|---|
| units | 4 073, tiling `.text`; no gap holds code |
| entry points | 4 073: every branch that leaves its function lands on a function start (821 tail calls), every `jal` too |
| switch tables | 142, each sized by the `sltiu` bound before it and every entry inside its function |
| other `jr` | 3, in libgcc's C++ exception unwinder (`__sjthrow`, `throw_helper`, `__rethrow`): indirect jumps through the runtime |
| jumps into a delay slot | 1, handled (the slot is emitted twice, with a label) |

## The translation

One C++ function per entry, `void f_XXXXXXXX(EEContext& c)`:

* **Registers**: 32 GPRs of 128 bits; 32-bit operations sign-extend into
  the low 64 bits and leave the upper half alone; MMI, `lq`/`sq` and the
  COP2 moves are the only writers of bits 64–127. `$zero` is never written.
* **Delay slots**: a branch's condition (or a `jr`'s target) is read
  first, the slot runs, then the transfer: the slot may change the operands.
  A likely branch runs the slot only when taken.
* **Calls and returns**: `jal` sets `ra`, runs the slot and calls the target
  as a C++ function; `jr ra` returns. A `j` or branch to another function
  is a tail call. `jalr` and other `jr` go through `ee_call`, a binary
  search of the sorted entry table.
* **Switch tables** become C++ `switch` statements over the target address.
* **Back-edges** (a branch to an earlier address in the same function) are
  where pending interrupts are delivered (`EE_POLL`).
* **Memory**: an address below 32 MB is RAM, read and written directly;
  anything else (the uncached mirrors, the scratchpad, the hardware) goes
  through the runtime. The guest is little-endian like the host: no swaps.
* **The FPU and VU0** compute in host single precision with the PS2's
  rules as far as they are modelled: denormals flushed, no infinities or
  NaNs (clamped to the largest finite value), the host set to round toward
  zero. VU0 macro instructions set the MAC and status flags (the game reads
  them: `CEulerClothObj::Tick`, the SDK's clip functions) and the clip flags.
* **Division by zero**, which the R5900 leaves undefined, gets the values
  written next to `ee_div`.

All 307 646 instructions translate (no unsupported operation); the
generated C++ is 27 MB in 38 files and compiles and links in about 20
seconds with clang at `-O1`.

## How it is checked

**Differential tests** (`ps2kit/recomp/difftest.py`): the same call runs in
`ps2kit.eeemu`, a reference interpreter in Python written from the
instruction semantics and not from the emitter, and in the recompiled C++
(`ps2kit/runtime/difftest.cpp`). Both start from the same machine state:
every register filled with pseudo-random 128-bit values, so that a lost
upper half shows. Then every register and every byte of RAM, scratchpad and
VU0 memory must be equal.

* **Named cases**: newlib's R5900 string routines, libgcc's 64-bit
  arithmetic, the SDK's soft float (`dpadd`, `fpmul`, `litodp`...),
  `sprintf`, `rand`, and libvu0's matrix and vector functions, with
  arguments that make sense for each (float arguments in `$f12`...).
* **Leaf fuzzing**: every function that calls nothing and reaches neither
  the kernel nor the hardware (1 080 of them), its pointer arguments into a
  buffer of mixed words (pointers back into the buffer, small integers,
  floats). A run the reference cannot finish (a pointer leaving RAM, a loop,
  a division by zero) is skipped and counted.

The numbers are in the session log ([00-sessions](00-sessions.md)).

What the tests caught on the way: a dispatch bug in the reference
interpreter (`vmr32` and `vmove` share their operand form with `vabs`, and
fell into the wrong branch); wrong argument conventions in the first cases
(float arguments go in `$f12`, integer arguments five to eight in
`t0`–`t3`); and, after the switch to round-toward-zero, the reference's
exact arithmetic losing the sign of exact zeros. Each time the recompiled
side was right and the oracle or the case was wrong, which is the point of
having two independent sides.

## What the tests do not show

They compare the translation with a second reading of the same semantics.
Whether those semantics are the PS2's is a different question: the FPU and
VU model is PCSX2's default (round toward zero, clamping), known to differ
from the console in the last bit of some products and in treating exponent
255 as an ordinary exponent. That question goes to PCSX2 and the console,
when the game runs.
