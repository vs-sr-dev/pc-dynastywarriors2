# Sound: the IOP's sound modules, run

Session 10 began phase 5 (sound) with a choice, made with the user: run
the IOP's own sound modules on an interpreter of the IOP's processor, with
an SPU2 modelled at its registers, rather than model Koei's RPC services
at the SIF boundary as the rest of the IOP is. KESSOUND is mostly a
wrapper around Sony's synthesiser (MODHSYN), sequencer (MODMIDI) and MIDI
input (MODMSIN), and it also passes LIBSD batches straight through, so an
SPU2 at its registers was needed either way; running the modules leaves
nothing of their behaviour to reconstruct.

```sh
# the attract mode's sound into a WAV (16-bit stereo, 48 kHz); with a window, the host's audio device
build/recomp-build/ps2run.exe "build/image/Dynasty Warriors 2 (Europe).cue" --headless --seconds 70 \
    --wav out.wav --press 8:START,10:START,12:START,14:START,16:START,18:START,20:START,22:START
PS2KIT_SPU2_LOG=1 ...      # the SPU2's interrupts, transfers and key-ons, by sample
PS2KIT_IOP_SOUND=0 ...     # the modules not run: the silent stand-ins of before
```

## What runs

The six modules the game loads, in its order: LIBSD 1.04, MODHSYN 1.04,
MODMIDI 1.04, MODMSIN 1.01, KOEIADS 1.05, KESSOUND 1.01. Each is
relocated and linked as the IOP's loader does (`runtime/iop_os.cpp`): an
import stub becomes a jump when a run module registered the library
(`RegisterLibraryEntries`), or a SYSCALL whose code names a host function.
Its start function runs on a thread of its own; the EE's `loadfile` call
ends when it returns. The other modules (cdvdman, padman, mcserv and the
rest) stay at the SIF boundary as before.

**The processor** (`runtime/iop_cpu.cpp`): MIPS I with the R3000's two delay
slots (a branch's, and a load's: the next instruction still reads the old
value). Calls from the host into IOP code (thread entries, interrupt
handlers, RPC functions) return to addresses at 0xBFC00000 that the
interpreter does not run.

**The kernel** (about 50 functions, by library and ordinal: the SDK's public
numbering, each checked against the modules' own calls and arguments):
threads by priority, never time-sliced among equals, sleep and wake-up,
semaphores, event flags; interrupt handlers by line, called between
instructions when the running thread has interrupts enabled (whether a
line is enabled is the INTC mask, kept when a handler is released and
registered again, which `sceSdInit` does after KOEIADS enabled its lines);
the hardware timers by mode, compare and clock; SIF DMA to the EE; RPC
servers whose calls run on the thread in `sceSifRpcLoop`, the reply sent
when the function returns (the EE's calls to them are now answered
later, as on the console); sector reads and file searches, done at once;
`printf` to the host's console.

**Time.** The IOP runs at 36.864 MHz, one instruction a cycle, by the
host's clock: KOEIADS's streaming thread (the lowest priority) polls
whenever it has work in hand, and takes the IOP's idle time, not a host
core. KESSOUND's sequencer is woken by a hardware timer
(`AllocHardTimer(horizontal lines, 16 bits)`, compare 66, mode 0x158): a
tick every 66 lines, 4.224 ms in PAL, 236.7 a second. Ticks are delivered
one at a time, the woken thread run before the next, so a host delay does
not merge them: 236.75 a second measured over a minute. (Waiting on a
condition variable overslept by up to 15 ms on Windows, which merged ticks
and played the music at a third of its speed; the IOP's thread waits as
the clock's does, with `Sleep(1)` and a spin, above the drawing threads.)

## The SPU2

`runtime/spu2.cpp`, after psx-spx's description of the PS1's SPU (which the
SPU2 keeps per core) and PCSX2's SPU2 for the PS2's additions:

* voices: SPU ADPCM blocks with their loop flags (ENDX, a repeat or a stop),
  the loop address from a block's flag unless the IOP wrote LSAX after the
  key on, pitch with modulation (PMON), noise, the ADSR envelope (its waits
  and steps), left and right volumes; NAX read back as the voice's position
  (KOEIADS follows its streams by it);
* mixing: each core's dry and wet voice mixes by VMIXL/R and VMIXEL/R, the
  core's gates (MMIX), core 0's output as core 1's external input (BVOL),
  the master volumes;
* the effects (reverb): psx-spx's algorithm as PCSX2 runs it, one side per
  sample at 24 kHz with the 39-tap half-band filter, its area from ESA to
  EEA; both cores have it on (ATTR 0xC080, 0xC081);
* the interrupt on IRQA (a voice reading the block that holds it, a
  transfer through it): SPDIF_IRQINFO and the IOP's line 9;
* transfers: DMA channels 4 and 7 and the data port at TSA; STATX 0 after
  a reset, bit 10 while a transfer runs, bit 7 when one has ended (LIBSD's
  DMA handler waits for it, its reset waits for 0);
* the output: the host's audio device with a window, `--wav` always.

Samples are made by the IOP's thread at most 256 at a time and none after
one that raised an interrupt: the handler, and what it wakes, run before
the SPU2 plays on. KOEIADS streams the music through a ring of two blocks
of 0x800 bytes per channel (core 1, voices 22 and 23, at 44.1 kHz), an
interrupt at each block's start, the other block refilled through the data
port; made 250 ms at a time after a host delay, the voices played past a
block not yet refilled, and the music had gaps of exactly one block
(81.2 ms) every half second. None now in several runs of a minute.

Not modelled yet: volume sweeps (said once if a game sets one; DW2 sets
none), the input from memory (ADMA), the output written back to sound
memory, interrupts on the effects' area. Samples are interpolated with a
cubic, not the SPU2's own Gaussian table.

## Checked so far

* The modules load, start, register their libraries, threads, servers and
  interrupts; every RPC call the game makes is answered by them; the game
  runs through the movies, the menu and the attract battle as before.
* The timer's rate (above); the stream without gaps; no clipping.
* By ear (the user, against PCSX2): the attract mode's recording (the
  logo's jingle, the movies' sound through KOEIADS's host transfer, the
  attract battle's music and effects) is right; the menu is silent on the
  console too. Two sounds were missing, both found from there:
  * the "whoosh" on reaching the menu (KESSOUND, core 0, voice 23): core
    0 was never heard. ATTR bit 14, which LIBSD sets with bit 15, had been
    taken as a mute (it is the PS1's "unmute"; PCSX2 ignores it), and core
    1's external input (core 0's output) was scaled by BVOL as a 15-bit
    voice volume. EVOL, AVOL and BVOL are 16-bit (LIBSD writes 0x7FFF);
    AVOL is the external input's, BVOL the memory input's. Found with
    `PS2KIT_SPU2_LOG`, which now prints each key-on's registers and
    sample, key-offs and each voice's end: the voice played, its peak was
    high, the output stayed at one step of 16 bits;
  * Omega Force's logo: the movie player started it again and again, a
    DMA fault (below, and [12-movies](12-movies.md)). The menu is
  silent in our runs, and the game's calls say so too: with the stand-ins
  of before it called `koeiAdsPlay` first at the attract battle as well.
