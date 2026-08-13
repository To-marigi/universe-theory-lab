"""Corrected bounded, hard-timeout preflight for a possible 721 Groebner run.

Not a production gate. Measures actual sympy.groebner() cost on tiny
subsystems made from complete CPOBC residual units. Each residual unit keeps
all nonzero entries of its 2-by-2 residual together; the predecessor probe
incorrectly counted individual scalar entries as residuals. Each subprocess
call is killed at a hard wall-clock timeout.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "scripts" / "probe_v042_721_groebner_preflight_worker.py"
BUILDER = ROOT / "scripts" / "build_v042_721_groebner_residual_cache.py"
CACHE = ROOT / "scratch_v042_721_groebner_preflight_residual_units.json"
TIMEOUT_SECONDS = 90
BUILD_TIMEOUT_SECONDS = 180
COUNTS = [1, 2, 3]

if CACHE.exists():
    print(f"--- reusing residual-unit cache {CACHE.name} ---", flush=True)
else:
    print(
        f"--- build residual-unit cache (timeout {BUILD_TIMEOUT_SECONDS}s) ---",
        flush=True,
    )
    build_start = time.time()
    try:
        build = subprocess.run(
            [sys.executable, str(BUILDER)],
            timeout=BUILD_TIMEOUT_SECONDS,
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired:
        elapsed = time.time() - build_start
        raise SystemExit(
            f"residual-unit cache build timed out after {elapsed:.1f}s; "
            "no Groebner call was attempted"
        ) from None
    if build.returncode:
        raise SystemExit(
            f"residual-unit cache build failed:\n{build.stderr[-4000:]}"
        )
    print(build.stdout.strip(), flush=True)
    print(f"cache_seconds={time.time() - build_start:.3f}", flush=True)

results: list[dict] = []

for count in COUNTS:
    print(f"--- count={count} (timeout {TIMEOUT_SECONDS}s) ---", flush=True)
    start = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, str(WORKER), "--count", str(count)],
            timeout=TIMEOUT_SECONDS,
            capture_output=True,
            text=True,
        )
        elapsed = time.time() - start
        ok = proc.returncode == 0
        results.append(
            {
                "count": count,
                "status": "OK" if ok else "ERROR",
                "wall_seconds": round(elapsed, 3),
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip()[-2000:] if proc.stderr else "",
            }
        )
        print(proc.stdout.strip(), flush=True)
        if not ok:
            print(f"worker failed, stderr tail:\n{proc.stderr[-2000:]}", flush=True)
            break
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        results.append(
            {
                "count": count,
                "status": "TIMEOUT",
                "wall_seconds": round(elapsed, 3),
            }
        )
        print(f"TIMEOUT at count={count} after {elapsed:.1f}s", flush=True)
        break

out_path = ROOT / "scratch_v042_721_groebner_preflight.json"
out_path.write_text(json.dumps(results, indent=2), encoding="utf-8", newline="\n")
print(f"wrote {out_path}", flush=True)
