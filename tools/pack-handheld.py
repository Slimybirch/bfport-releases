#!/usr/bin/env python3
"""Write the handheld's game data as one file, openbf.pak, on the PC.

The handheld layout keeps the game binary and its data apart, so an update can
replace the small binary and leave the data alone:

    ports/openbf.sh
    ports/openbf/openbf-aarch64
    ports/openbf/openbf.pak        <- this script's output
    ports/openbf/openbf.pak.bake   <- its bake id, for the launcher's update check

openbf.pak is OpenBF's own pack format (engine/crates/pak) with no executable
before it: [file bodies][index][footer], pack start 0. The game finds it
beside its binary (or via OPENBF_PAK).

Source: the pack that scripts/pack.py appends to dist/openbf(.exe). Run
pack.py first (or again after the bake changes); this script only copies the
data out and rebases its offsets, so it takes about as long as copying the file.

    python scripts/handheld/pack-handheld.py
    python scripts/handheld/pack-handheld.py --src dist/openbf.exe --out builds/openbf/openbf.pak

The output contains the games' own content: keep it on your machine and your
handheld, never upload or share it.
"""
import argparse
import os
import struct
import sys

MAGIC = b"OPENBFPK"
FOOTER = 32
CHUNK = 8 << 20
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def default_src():
    for name in ("openbf.exe", "openbf"):
        p = os.path.join(ROOT, "dist", name)
        if os.path.isfile(p):
            return p
    return os.path.join(ROOT, "dist", "openbf.exe")


def write_stamp(out, assume_current=False):
    """openbf.pak.bake: the id of the bake this pack holds, for the launcher's
    update check (a new binary is only swapped in when its bake id matches)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import bake_id
    current = bake_id.bake_is_current()
    if current is False and not assume_current:
        sys.exit("pack-handheld: the bake in extracted/ is older than this checkout's bake code;\n"
                 "run scripts/pack.py first (it re-bakes), then this script again\n"
                 "(or --assume-current when only Cargo.toml / Cargo.lock changed)")
    if current is None:
        print("note: pack.py left no bake stamps in extracted/; assuming the bake matches this checkout")
    made = bake_id.tree_id()
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out + ".bake", "w", newline="\n") as f:
        f.write(made + "\n")
    print(f"wrote {out}.bake (bake id {made}); copy it beside openbf.pak")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--src", default=default_src(), help="packed game from scripts/pack.py")
    ap.add_argument("--out", default=os.path.join(ROOT, "builds", "openbf", "openbf.pak"))
    ap.add_argument("--stamp-only", action="store_true",
                    help="only write openbf.pak.bake (the bake id) beside --out")
    ap.add_argument("--assume-current", action="store_true",
                    help="write the bake id even when pack.py's stamps say the bake is older than this checkout")
    a = ap.parse_args()
    if a.stamp_only:
        write_stamp(a.out, a.assume_current)
        return

    size = os.path.getsize(a.src)
    with open(a.src, "rb") as f:
        f.seek(size - FOOTER)
        foot = f.read(FOOTER)
        if foot[:8] != MAGIC:
            sys.exit(f"{a.src} carries no pack: run scripts/pack.py first")
        start, at, length = struct.unpack("<QQQ", foot[8:])
        if at + length + FOOTER != size or start > at:
            sys.exit(f"{a.src}: footer does not match the file size")
        f.seek(at)
        index = f.read(length)

        # Rebase every entry's offset so the bodies start at byte 0.
        count = struct.unpack_from("<I", index, 0)[0]
        out_index = bytearray(index[:4])
        i = 4
        for _ in range(count):
            (plen,) = struct.unpack_from("<H", index, i)
            name = index[i + 2 : i + 2 + plen]
            off, n = struct.unpack_from("<QQ", index, i + 2 + plen)
            if off < start or off + n > at:
                sys.exit(f"{a.src}: entry {name!r} lies outside the pack")
            out_index += struct.pack("<H", plen) + name + struct.pack("<QQ", off - start, n)
            i += 2 + plen + 16
        if i != len(index):
            sys.exit(f"{a.src}: index has {len(index) - i} trailing bytes")

        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        tmp = a.out + ".new"
        with open(tmp, "wb") as o:
            f.seek(start)
            left = at - start
            while left:
                buf = f.read(min(CHUNK, left))
                if not buf:
                    sys.exit(f"{a.src}: file ended early")
                o.write(buf)
                left -= len(buf)
            o.write(out_index)
            o.write(MAGIC + struct.pack("<QQQ", 0, at - start, len(out_index)))
    os.replace(tmp, a.out)
    write_stamp(a.out, a.assume_current)
    gib = os.path.getsize(a.out) / (1 << 30)
    print(f"wrote {a.out} ({count} files, {gib:.2f} GiB)")
    print("Copy it to ports/openbf/ beside openbf-aarch64; remove any loose")
    print("assets_baked/ and missions/ folders there (a folder on disk wins over the pack).")


if __name__ == "__main__":
    main()
