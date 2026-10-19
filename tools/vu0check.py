"""Check DW2's VU0 micro programs, as ps2kit's runtime runs them, against
what they compute.

    PS2KIT_VU0_LOG=400 ps2run DISC ... 2> run.err
    python tools/vu0check.py build/disc/SLES_500.57 run.err

The game's VU0 microcode (vu0lib.c, uploaded by VIF0 at start-up) is a
trigonometry library called with vcallms. The runtime's log gives each run's
vf1, vf2 and vf16-vf19 before and after; each program is compared with
libm, and the sine and cosine also with their own polynomials, evaluated in
double precision after the microcode's range reduction, with the
coefficients init_vu0_regs loads into vf28 and vf29 (read here from the
executable, at 0x3D0180 and 0x3D0190):

    0000  sin(vf1.x)              -> vf1.x
    0010  cos(vf1.x)              -> vf1.x
    0030  atan2(vf1.x, vf2.x)     -> vf1.x
    0060  the rows of vf16-vf19 rotated about x by vf1.x (y' = y c - z s)
    0070  ... about y, 0080 ... about z
"""
import math
import os
import re
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ps2kit import elf  # noqa: E402

PI = 3.14159274                                   # vf22, as a single


def parse(path):
    runs, pending = {}, {}
    for line in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r"\[vu0\] (\w{4}) (in |out)(.*)", line)
        if not m:
            continue
        regs = {int(r): [float(x) for x in v.split(",")] for r, v in re.findall(r"vf(\d+)=(\S+)", m.group(3))}
        if m.group(2) == "in ":
            pending[m.group(1)] = regs
        elif m.group(1) in pending:
            runs.setdefault(m.group(1), []).append((pending.pop(m.group(1)), regs))
    return runs


def reduce(x, cos):
    """To [-pi, pi] by turns of 2 pi, then to [-pi/2, pi/2]: by reflection
    for the sine, by a half turn and a change of sign for the cosine."""
    while x > 2 * PI:
        x -= 2 * PI
    while x < -2 * PI:
        x += 2 * PI
    if x > PI:
        x -= 2 * PI
    elif x < -PI:
        x += 2 * PI
    sign = 1
    if x > PI / 2:
        x, sign = (x - PI, -1) if cos else (PI - x, 1)
    elif x < -PI / 2:
        x, sign = (x + PI, -1) if cos else (-PI - x, 1)
    return x, sign


def rotate(axis, t, row):
    c, s = math.cos(t), math.sin(t)
    x, y, z, w = row
    return {"x": [x, y * c - z * s, y * s + z * c, w],
            "y": [x * c + z * s, y, -x * s + z * c, w],
            "z": [x * c - y * s, x * s + y * c, z, w]}[axis]


def main():
    exe = elf.Elf(sys.argv[1])
    sin_c = struct.unpack("<4f", exe.read(0x3D0180, 16))
    cos_c = struct.unpack("<4f", exe.read(0x3D0190, 16))

    def poly_sin(x):
        x, _ = reduce(x, False)
        x2 = x * x
        return x * (sin_c[0] + x2 * (sin_c[1] + x2 * (sin_c[2] + x2 * sin_c[3])))

    def poly_cos(x):
        x, s = reduce(x, True)
        x2 = x * x
        return s * (1 + x2 * (cos_c[0] + x2 * (cos_c[1] + x2 * (cos_c[2] + x2 * cos_c[3]))))

    checks = {
        "0000": [("sin", lambda i, o: o[1][0] - math.sin(i[1][0])),
                 ("its polynomial", lambda i, o: o[1][0] - poly_sin(i[1][0]))],
        "0010": [("cos", lambda i, o: o[1][0] - math.cos(i[1][0])),
                 ("its polynomial", lambda i, o: o[1][0] - poly_cos(i[1][0]))],
        "0030": [("atan2", lambda i, o: o[1][0] - math.atan2(i[1][0], i[2][0]))],
    }
    for prog, axis in (("0060", "x"), ("0070", "y"), ("0080", "z")):
        def err(i, o, axis=axis):
            worst = 0
            for r in (16, 17, 18, 19):
                scale = max(1.0, max(abs(v) for v in i[r]))
                worst = max(worst, max(abs(a - b) for a, b in zip(o[r], rotate(axis, i[1][0], i[r]))) / scale)
            return worst
        checks[prog] = [("rotation about " + axis, err)]
    runs = parse(sys.argv[2])
    for prog, items in sorted(runs.items()):
        for name, f in checks.get(prog, []):
            print("%s against %-16s %4d runs, worst |error| %.3g" % (prog, name + ":", len(items),
                                                                      max(abs(f(i, o)) for i, o in items)))
        if prog not in checks:
            print("%s: %d runs, no reference" % (prog, len(items)))


if __name__ == "__main__":
    main()
