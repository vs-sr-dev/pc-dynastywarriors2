# TODO — session 3

Phase 2 of [06-attack-plan](06-attack-plan.md): boot. The translator is
done and checked ([09-recompiler](09-recompiler.md)); the runtime so far is
memory, dispatch and a stub that stops at the first system call.

1. **Loader and entry**: load the ELF's segments, `_start` with the
   arguments the boot ROM gives (`argc`/`argv`: `cdrom0:\SLES_500.57;1`),
   the host thread that runs guest code with `rt_init_fpu()`.
2. **The kernel at the syscall boundary**, the surface the game uses
   (53 stubs it calls; numbers from the SDK's own `klib.s`, listed in
   session 2): `SetupThread` (60) and `SetupHeap` (61) from `crt0`;
   threads (`CreateThread`, `StartThread`, `GetThreadId`,
   `ReferThreadStatus`, `ChangeThreadPriority`, `RotateThreadReadyQueue`,
   `SleepThread`/`WakeupThread`, `ExitThread`); semaphores (`CreateSema`,
   `SignalSema` ×51, `WaitSema`, `PollSema`, `iSignalSema`); interrupt and
   DMA handlers (`AddIntcHandler`, `AddDmacHandler`, `_EnableIntc`...),
   alarms, `FlushCache`, `GsGetIMR`/`GsPutIMR`, `SetVSyncFlag`, the SIF
   (`sceSifSetDma`, `sceSifSetDChain`, `sceSifSetReg`/`GetReg`,
   `sceSifDmaStat`), `Deci2Call` (devkit leftovers: answer "no").
   Guest threads as host threads (or fibers), one running at a time, as
   wiikit's `os.cpp` does.
3. **First output**: the game's `printf` reaches the host console; run to
   the first wait on the IOP (`sceSifInitRpc`, module loading). Record the
   order of the calls; compare with a PCSX2 trace of the same boot if the
   order is in doubt.
4. Keep the differential tests green on every runtime change (named suite
   and leaf fuzzing; numbers in [00-sessions](00-sessions.md)).

5. When the game prints its first lines on the host: ask the user whether
   that is "something to show" for publishing ps2kit and this repo on
   GitHub (decided after session 1: public, but not before).

Restarting: run ps2kit from the directory that holds the checkout being
edited (the directory holding the ps2kit checkout), not from this repository's root, where the pinned
submodule would be imported. Regenerate with `python -m ps2kit.recomp
pc-dynastywarriors2/build/disc/SLES_500.57 --out pc-dynastywarriors2/build/recomp`,
rebuild with `ninja -C build/recomp-build` (clang, cmake, ninja from
MSYS2's MinGW 64-bit environment), test as in [09-recompiler](09-recompiler.md).

Open points from session 2:
* The model of the FPU and VUs is PCSX2's default (round toward zero,
  clamping); the console's last-bit differences in products and its
  exponent-255 numbers are not modelled.
* Operations never exercised by a test (system ones aside): `qmfc2.i`,
  `sqrt.s`, `viadd`, `vmtir` and a few VU0 forms (`vmax`, `vmini*`,
  `vmsuba*`, `vmula[iw]`, `vmuli`), `divu1`/`mflo1`. They sit in non-leaf
  functions; a named case or two would cover them.
