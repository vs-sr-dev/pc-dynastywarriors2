# The disc

Dynasty Warriors 2, PAL, SLES-50057 (`SYSTEM.CNF`: `BOOT2 =
cdrom0:\SLES_500.57;1`, `VER = 1.00`, `VMODE = PAL`). A CD, not a DVD:
Redump-style image of two tracks.

| Track | Mode | Length | Contents |
|---|---|---|---|
| 01 | MODE2/2352 (CD-ROM XA) | 276 830 sectors (61:31) | ISO 9660, volume `PLAYSTATION`, created 2000-10-18 07:07 |
| 02 | AUDIO | 15 926 frames (3:32), pregap 150 | silence: a flat noise floor at −71 dBFS, peak 17 of 32 767, from the first second to the last |

Every data sector's subheader was read (`ps2kit.disc`): 276 629 Form 1 data
sectors, 51 Form 1 end-of-file markers, 150 empty; no Form 2 sector. All
files are read through the ordinary 2048-byte path.

## Files

| Path | Size | What |
|---|---|---|
| `SYSTEM.CNF` | 56 | boot configuration |
| `SLES_500.57` | 3 084 705 | the executable, **not stripped** (see [02-executable](02-executable.md)) |
| `MODULES/*.IRX` | 22 modules | IOP modules: Sony's (cdvd, sio2man, padman, mcman/mcserv, libsd, the MIDI/synth stack) and Koei's (`kessen_sound_driver` 1.01, `koeiads_driver` 1.05) |
| `MODULES/CDROM/` | 2 modules | other builds of the same two Koei drivers; these are the ones the code loads |
| `MODULES/IOPRP15*.IMG` | 3 images | IOP replacement images; the code names only `IOPRP153.IMG` |
| `MOVIE/*.PSS` | 18 movies | Sony PSS (MPEG-2 video, SShd audio): logos, opening, title, staff roll, ending, 11 `ADDMOV` scenes |
| `DATA/SCENE.SDF` | 27 MB | unknown container (entropy 7.46) |
| `DATA/LOAD.FTX` | 33 936 | unknown (entropy 0.86, mostly zeros) |
| `BGM.BNS` | 66 MB | raw SPU ADPCM (fingerprint: stereo, interleave 0x100, to be confirmed by ear) |
| `LINKDATA.BNS` | 144 MB | unknown container (entropy 7.83) |
| `SILENCE.DA` | 32 MB | an ISO record pointing at track 2 (the CD-DA silence) |

The code names its files with these paths: `\BGM.BNS;1`, `\LINKDATA.BNS;1`,
`DATA\SCENE.SDF`, `DATA\LOAD.FTX`, each movie as `\MOVIE\NAME.PSS;1`, the
IOP modules it loads (`\MODULES\LIBSD.IRX`, `\MODULES\CDROM\KESSOUND.IRX`,
…) and `cdrom0:\MODULES\IOPRP153.IMG;1`. Not named anywhere in the code:
`ILINK`, `ILSOCK`, `USBD`, `MTAPMAN`, `RSPU2DRV`, `SDRDRV`, `MODDELAY`,
`MODMONO`, `MODSSYN`, `CDVDFSV`, `CDVDMAN`, `IOPRP15.IMG`, `IOPRP151.IMG`
(some may be loaded from inside the IOPRP image; to be checked).

## Commands

```sh
python -m ps2kit.disc "build/image/Dynasty Warriors 2 (Europe).cue" --info
python -m ps2kit.disc "build/image/Dynasty Warriors 2 (Europe).cue" --list --forms
python -m ps2kit.disc "build/image/Dynasty Warriors 2 (Europe).cue" --extract build/disc
python -m ps2kit.fingerprint build/disc --deep
```
