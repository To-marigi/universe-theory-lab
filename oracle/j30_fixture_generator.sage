"""Offline exact fixture generator; production code must not import this file."""

from sage.all import *

import json
import sys


def generate(j2, j3, j4, r, name, role):
    j2, j3, j4, r = map(QQ, (j2, j3, j4, r))
    j5 = (
        -6 * r**5
        + 24 * j2 * r**3
        + 12 * j3 * r**2
        - 2 * (9 * j2**2 - 4 * j4) * r
        - 12 * j2 * j3
    ) / 4
    j6 = (
        r**6
        - 6 * j2 * r**4
        - 4 * j3 * r**3
        + (9 * j2**2 - 4 * j4) * r**2
        + (12 * j2 * j3 + 4 * j5) * r
        + 4 * j3**2
    ) / 4
    return {
        "name": name,
        "role": role,
        "j2": str(j2),
        "j3": str(j3),
        "j4": str(j4),
        "j5": str(j5),
        "j6": str(j6),
        "double_root": str(r),
        "generator_constraints": ["D(r)=0", "D'(r)=0"],
    }


if __name__ == "__main__":
    if len(sys.argv) != 7:
        raise SystemExit("usage: sage j30_fixture_generator.sage J2 J3 J4 r name role")
    print(json.dumps(generate(*sys.argv[1:]), sort_keys=True))
