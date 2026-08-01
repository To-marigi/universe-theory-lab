"""Reproduce the v0.4 weak-semantics rational witness and exact audits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from universe_lab.final_theory.weak_d2_v04 import (
    VERDICT,
    compile_v04,
    semantic_digest,
    write_v04_result,
)

RESULT_PATH = "results/v0.4_weak_d2_classification.json"


def verify_v04(root: Path, *, write: bool = False) -> dict[str, Any]:
    root = root.resolve()
    rebuilt = compile_v04(root)
    result_path = root / RESULT_PATH
    if write:
        write_v04_result(root, rebuilt)
    stored = json.loads(result_path.read_text(encoding="utf-8"))
    regenerated_exactly = stored == rebuilt
    passed = bool(rebuilt["passed"]) and regenerated_exactly
    return {
        "version": "0.4",
        "artifact": RESULT_PATH,
        "semantic_digest_sha256": semantic_digest(rebuilt),
        "regenerated_exactly": regenerated_exactly,
        "verdict": rebuilt["verdict"],
        "expected_verdict": VERDICT,
        "passed": passed and rebuilt["verdict"] == VERDICT,
    }


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--write",
        action="store_true",
        help="replace the frozen result with a freshly compiled artifact",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = _parse_args(argv)
    summary = verify_v04(arguments.root, write=arguments.write)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
