"""Command-line entry point for frozen and additive Final-Theory benches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from universe_lab.final_theory.benchmarks import run_final_theory_bench
from universe_lab.final_theory.v02 import write_v0_2_artifacts
from universe_lab.final_theory.v03 import write_v0_3_artifacts
from universe_lab.final_theory.v031 import write_v0_3_1_artifacts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        choices=("0.1", "0.2", "0.3", "0.3.1"),
        default="0.1",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--production-commit",
        default="UNCOMMITTED_WORKTREE",
        help="Code commit recorded in additive benchmark provenance artifacts.",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    if args.version == "0.3.1":
        written = write_v0_3_1_artifacts(
            root, code_commit=args.production_commit
        )
        print(
            "FINAL_THEORY_OPEN "
            "(v0.3.1 artifacts="
            + ", ".join(str(path) for path in written.values())
            + ")"
        )
        return 0
    if args.version == "0.3":
        written = write_v0_3_artifacts(
            root, code_commit=args.production_commit
        )
        print(
            "FINAL_THEORY_OPEN "
            "(v0.3 artifacts="
            + ", ".join(str(path) for path in written.values())
            + ")"
        )
        return 0
    if args.version == "0.2":
        written = write_v0_2_artifacts(
            root, production_commit=args.production_commit
        )
        print(
            "FINAL_THEORY_OPEN "
            "(v0.2 artifacts="
            + ", ".join(str(path) for path in written.values())
            + ")"
        )
        return 0

    result = run_final_theory_bench(root)
    destination = args.output or Path("results/final_theory_bench_v0.1.json")
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
