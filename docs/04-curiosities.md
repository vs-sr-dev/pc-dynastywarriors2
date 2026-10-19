# Curiosities

* **The codename was "pale".** Every C source of the game was built from
  `/HD/home2/morinaka/pale/sc/`; the names survive in the executable's debug
  information, 83 files from `main.c` to `title.c`.
* **The sound driver is Kessen's.** The Koei IOP module reports itself as
  `kessen_sound_driver` 1.01: the engine of Koei's other PS2 launch-window title,
  Kessen (2000), reused here, with its EE-side library `kessound.c` linked
  into the game.
* **Track 2 is called SILENCE.DA, and it is.** Three and a half minutes of
  CD audio at a constant noise floor (−71 dBFS), reachable from the file
  system as a 32 MB file.
* **Leftovers on the disc.** i.LINK (`ILINK.IRX`, `ILSOCK.IRX`), USB
  (`USBD.IRX`), multitap (`MTAPMAN.IRX`) and other modules ship in
  `MODULES/`, and three IOP replacement images sit side by side
  (`IOPRP15`, `151`, `153`); the code names only the last, and none of the
  former.
* **The scenes are C++, the battle is C.** The scene manager, the opening,
  the stage renderer and a cloth simulation (`ClothObj`, `EulerClothObj`,
  `NdimGeometry`) are C++ classes with exceptions enabled; everything about
  the battle itself is plain C.
* **One `host0:` string** remains in the executable: the devkit's host file
  system, left from development.
