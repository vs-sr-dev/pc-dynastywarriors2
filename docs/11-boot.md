# The boot

Phase 2 of [06-attack-plan](06-attack-plan.md), and the start of phase 3:
ps2kit's runtime runs the recompiled game from the disc image, through the
EE kernel, the IOP's reboot and module loading, the first file searches and
reads, pad and sound initialisation, into the game's 50 Hz vblank loop. It
stops at the first memory card request, the next piece to model.

```sh
ninja -C build/recomp-build ps2run
build/recomp-build/ps2run.exe "build/image/Dynasty Warriors 2 (Europe).cue" --trace 1 --seconds 30
```

`--trace 1` logs every system call, IOP command and RPC (repeats counted,
not printed); `--trace 2` adds every hardware register access. Every five
seconds a heartbeat line gives vblanks, DMA traffic per channel, disc reads,
system calls and guest handler calls; `--profile` adds the guest functions
the time goes to.

## What runs where

| ps2kit file | Replaces | As |
|---|---|---|
| `runtime/boot.cpp` | the boot ROM | `SYSTEM.CNF`'s BOOT2 read from the disc; the ELF's segments into RAM; the main thread at `_start`, with the BOOT2 path as `argv[0]` |
| `runtime/kernel.cpp` | the EE kernel | the system calls the game makes (from `klib.s`); one host thread per guest thread, one running at a time; strict priorities; semaphores; INTC and DMAC handlers and alarms delivered at loop back-edges; the SIF registers and DMA; Deci2's TTY |
| `runtime/hw.cpp` | the EE's hardware registers | INTC, DMAC (transfers complete at once; source chains; scratchpad copies), timers counted from the host clock, the GS's CSR and IMR with a 50 Hz vertical blank, SIO, the SIF registers |
| `runtime/iop.cpp` | the IOP | its side of sifcmd and sifrpc, and the RPC servers the game calls, as host code |
| `runtime/disc.cpp` | the drive | `.cue`/`.bin`/`.iso`, ISO 9660, 2048-byte user sectors |

## What the game does, in order

From `--trace 1`; two runs give the same 946 IOP commands and RPC calls and
the same sequence of system calls and results (polling loops aside, whose
repeat counts follow the host's timing):

1. `crt0`: `SetupThread` (stack at 0x1FF0000, 64 KB: the thread starts at
   0x1FFFD60), `SetupHeap`, `FlushCache`, `ei`, `main`. C++ constructors
   make no system call.
2. `init_system` opens the SIF first (`sceSifInitRpc`): there is no
   `printf` before the IOP answers.
3. A reboot of the IOP with `rom0:UDNL cdrom0:\MODULES\IOPRP153.IMG;1`,
   then `sceSifSyncIop`, whose success calls `sceTtyInit` (Deci2 socket,
   protocol 0x210), and the SIF opened again.
4. `sceCdInit`, then ten modules loaded: SIO2MAN, MCMAN, MCSERV, PADMAN,
   LIBSD, MODHSYN, MODMIDI, MODMSIN, KOEIADS, KESSOUND.
5. VIF/VU resets, `sceGsResetGraph`: `SetGsCrt(1, 3, 1)`, PAL interlaced,
   field mode.
6. `sceMcInit`, pads opened on both ports, port 0 set to analog.
7. `set_main_callback`: the vblank handler (`main_callback`) added and
   enabled; from here the game runs its frames.
8. `init_main`: `LINKDATA.BNS` and `BGM.BNS` found, sector reads from
   `LINKDATA.BNS` (fonts, textures, CLUTs: `LoadClut0`, `LoadPixel`).
9. The two sound drivers initialised, 40 KB of IOP heap allocated.
10. The six movies found (`KOEILOGO`, `PALLOGO`, `OMEGA`, `OPENING`,
    `TITLE`, `ENDING`), then `MusouMCardGameStart` asks mcserv for the card
    (function 1, `sceMcGetInfo`): the stop.

Each file search agrees with ps2kit's Python disc reader (`LINKDATA.BNS` at
sector 206 393, 143 947 776 bytes; `BGM.BNS` at 173 887, 66 572 288).

## Findings

**The game prints nothing.** No function of the game's own sources calls
`printf`, `scePrintf` or `kprintf`; only SDK libraries do, on errors (cd,
dma, gs, pad, mc, mpeg, iop reset). A release build. The "first lines on the host
console" planned as phase 2's check cannot happen while things go right; a
run shows its progress through the trace and the heartbeat instead.

**`printf` goes to Deci2, not to the IOP.** newlib's `write` calls
`sceTtyWrite`, which speaks Deci2 (the devkit's debug channel) through the
`Deci2Call` system call: open a socket of protocol 0x210 with a handler,
`ReqSend`, then `Poll` until the handler has been called with event 3 (it
hands the bytes over with `ExSend`) and event 4 (done). The packet has a
12-byte header, then the text with `\n` as `\r\n`. The kernel here is the
far end and prints the text; `kputs` (`Deci2Call` 0x10) and the SIO
transmit register print too. Read from the SDK's own `tty.c` and `deci2.c`
in the executable; not exercised yet, since nothing printed.

**The SIF protocol, from the EE's side.** Every packet layout and register
use the IOP side follows was read from the game's `sifcmd.c`, `sifrpc.c`,
`iopreset.c` and the library callers: the 16-byte header (sizes, data
destination, command id, option); the EE's receive buffer at 0x4FF480
given with command 0x80000002; `sceSifInitRpc` waiting for its software
register 0, which the IOP sets with a 0x80000001 packet; the reset packet
(0x80000003, 0x68 bytes, the reboot string at +0x18) after which the EE
clears SMFLG's 0x10000 and 0x20000 and waits for 0x40000; bind (0x80000009,
server id at +0x20) and call (0x8000000A: function, sizes, receive address,
mode, server at +0x20...+0x34) answered with 0x80000008 packets (client at
+0x1C, the ended command at +0x20, server, buffers). The first run of the
whole exchange worked without a correction.

**Which module serves which RPC id** was read from the modules themselves,
from the constant each passes to `sceSifRegisterRpc`: CDVDFSV 0x80000592,
0x593, 0x595, 0x597, 0x59A; PADMAN 0x8000010F and 0x11F; MCSERV
0x80000400; KESSOUND 0x4000009A; KOEIADS 0x40000099. The IOPRP images
carry FILEIO (0x80000001, and 0x80000003 for the IOP heap) and CDVDFSV;
LOADFILE (0x80000006) is the boot ROM's.

**The answers the servers give, and where each comes from.**

| Server, function | Answer | From |
|---|---|---|
| loadfile 0 | a module id; the module's header read from the disc | `_sceSifLoadModule`'s packet: {arguments length, -, path[252], arguments[252]} |
| cdvdfsv init 0 | nothing | `sceCdInit` (mode 0) |
| cdvdfsv search 0 | 1 found / 0; {sector, size, name} written to the EE block | `sceCdSearchFile`'s 0x124-byte block; `InitFilePosInfo` keeps only the sector |
| cdvdfsv disk ready 0, n-command 14 | 2 | the game's readers loop until exactly 2; libcdvd treats 6 as not ready |
| cdvdfsv n-command 1 | the sectors into the EE buffer; head/tail sizes 0 | `sceCdRead` and its end function `cd_read_intr` (unaligned head and tail come through a 0x90-byte area) |
| cdvdfsv s-command 4 | 0, no error | `sceCdGetError` |
| mcserv 0xFE | {0, mcserv's version, mcman's version} | MCSERV's own code: mcman export 37 (returns 0), its version halfword, mcman's module version |
| padman 1 | per command (init 1, open 1, mode info, actuators) | libpad v2.01's 128-byte block; the DualShock 2's answers to the actuator query from public protocol descriptions (to check against PCSX2) |
| iopheap 1, 2 | an IOP address; 0 | `sceSifAllocIopHeap`, `sceSifFreeIopHeap` |
| kessound, koeiads | zeros (silent stand-in) | KESSOUND's own init returns 0 on success, -3/-9/-99 on failure; the other commands are not ported yet |

Pads: port 0 holds a DualShock 2, digital at power-on (ID 4) as the real
one is, analog (ID 7, answer 0x73) once the game asks; port 1 is empty.
padman writes the older of two 128-byte frames each vblank (counter, state
6, request state, the 32-byte answer, its length): read from `scePadRead`
and `scePadGetState`.

**The vblank handler and the FIELD bit.** The game's own vblank handler,
`main_callback`, increments a counter and busy-waits until the GS CSR's
FIELD bit differs from the counter's parity; `set_main_callback` sets the
counter from FIELD right after `VSync()` (which clears INTC's VBON bit and
waits for the next one). This works in a few lines only if FIELD changes
*after* the vblank interrupt starts, and the handler runs before it does.
With FIELD toggled at the start of the blank, every handler call waited a
whole field and the game starved (97% of the time in `main_callback`, found
with the profiler). Three causes were found and fixed in turn: the clock
thread overslept by up to 15 ms (a condition variable, then the C++
library's sleep, on Windows; now `Sleep(1)` and a spin); the guest's tight
polling of the CSR starved the clock thread of the hardware lock (CSR and
INTC_STAT are now read without it); and the guest takes interrupts at loop
back-edges, later than the console's few cycles. FIELD now changes three
lines after the kernel takes the VBON interrupt (or after the blank begins,
if VBON is masked). The real kernel was read to settle how interrupts are
taken: the BIOS's INT0 dispatcher (ROM 1.60, 2001-10-04, at 0x80000380)
takes the highest pending cause only, clears it in INTC_STAT before calling
the handler chain, and `_EnableIntc` (0x800008C0) does not clear a pending
cause; both as modelled here.

## Not modelled yet (each stops the run with a message)

* The memory card (mcserv functions other than 0xFE): the current stop.
* The GS, VIF and VU1 (DMA to them is counted, not drawn), VU0 micro mode,
  the IPU (movies), the SPU2 and Koei's drivers (sound), timer interrupts.
* Deci2 reads; `sceCdRead` with 2328- or 2340-byte sectors; the other
  cdvdfsv, padman and loadfile functions.
* Transfer time: every DMA and disc read completes at once.
