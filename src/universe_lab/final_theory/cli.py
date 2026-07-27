"""Command-line entry point for Final-Theory Bench v0.1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from universe_lab.final_theory.benchmarks import run_final_theory_bench


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/final_theory_bench_v0.1.json"),
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    result = run_final_theory_bench(root)
    destination = args.output
    if not destination.is_absolute():
        destination = root / destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"{result['scientific_status']} "
        f"(spin2_found={result['spin2_found']}, output={destination})"
    )
    return 0 if result["benchmark_integrity_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
