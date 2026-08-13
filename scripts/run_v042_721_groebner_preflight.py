"""Bounded, hard-timeout preflight for a possible full 721 Groebner run.

Not a production gate. Measures actual sympy.groebner() cost on tiny
subsystems (smallest reduced CPOBC residuals + only the defining relations
whose tokens appear in them) before any owner decision about attempting the
full combined-ideal computation (1,967 residuals + 8 relations, ~104
variables). Each subprocess call is killed at a hard wall-clock timeout so
a blow-up cannot hang the session.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "scripts" / "probe_v042_721_groebner_preflight_worker.py"
TIMEOUT_SECONDS = 90
COUNTS = [1, 2, 3, 5, 8, 12, 20]

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
