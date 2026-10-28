#!/usr/bin/env python3
"""The handheld bake id: which bake a binary can read.

    python scripts/handheld/bake_id.py      # the bake id of this source tree

It is a short hash over the sources that make the baked data: scripts/pack.py's
BAKE_INPUTS without the workspace's Cargo.toml / Cargo.lock (a dependency bump
anywhere in the engine changes those, not the data), and MISSION_INPUTS. The
release workflow puts the tree's id in manifest.json; pack-handheld.py writes
the id of the bake it packs next to openbf.pak (openbf.pak.bake). The launcher
only swaps in a new binary when the two match.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pack  # noqa: E402  (scripts/pack.py: BAKE_INPUTS, MISSION_INPUTS, inputs_hash, the stamps)


DATA_INPUTS = tuple(p for p in pack.BAKE_INPUTS if not p.startswith("engine/Cargo.")) + pack.MISSION_INPUTS


def tree_id():
    """The bake id of this source tree."""
    return pack.inputs_hash(DATA_INPUTS)[:16]


def bake_is_current():
    """True / False: whether pack.py's last bake here was made from this tree
    (its own stamps, full inputs); None when it left no stamps."""
    if not os.path.isfile(pack.BAKE_STAMP):
        return None
    return pack.stale(pack.BAKE_STAMP, pack.BAKE_INPUTS) is None and \
        pack.stale(pack.MISSION_STAMP, pack.MISSION_INPUTS) is None


if __name__ == "__main__":
    print(tree_id())
