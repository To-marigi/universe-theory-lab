"""Sweep every 721 GC endpoint-size tier under the saturated inverse tokens.

Mirrors ``run_v042_721_gc_remaining_tiers.py``: runs the generalised
resaturated tier gate (source_native_721_gc_tier_resaturated_v042.py) for
every tier that has at least one pair, writing each tier's result to its
own file as soon as that tier finishes so a crash or interruption partway
through does not lose already-completed tiers. Progress is printed with a
flush after every tier so a background run can be tailed.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from universe_lab.final_theory.source_native_721_gc_tier_resaturated_v042 import (  # noqa: E402
    result_path,
    write_gc_tier_resaturated,
)

ALL_TIERS_WITH_PAIRS = [3, 4, 5, 6, 7, 8, 9, 10, 11, 15, 25]


def main() -> int:
    overall_start = time.time()
    for path_count in ALL_TIERS_WITH_PAIRS:
        target = ROOT / result_path(path_count)
        if target.is_file():
            print(f"tier {path_count}: already present at {target}, skipping", flush=True)
            continue
        start = time.time()
        print(f"tier {path_count}: starting", flush=True)
        try:
            written = write_gc_tier_resaturated(ROOT, path_count)
        except Exception as exc:  # noqa: BLE001
            elapsed = time.time() - start
            print(f"tier {path_count}: FAILED after {elapsed:.1f}s: {exc!r}", flush=True)
            return 1
        print(f"tier {path_count}: wrote {written} in {time.time() - start:.1f}s", flush=True)
    print(f"all tiers done in {time.time() - overall_start:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
