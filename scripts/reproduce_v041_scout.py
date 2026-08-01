"""Regenerate the exact bounded v0.4.1 one-sided triangular scout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from universe_lab.final_theory.one_sided_d2_v041_scout import (
    RESULT_PATH,
    compile_one_sided_d2_v041_scout,
    write_one_sided_d2_v041_scout,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--write", action="store_true", help="write the canonical result artifact")
    arguments = parser.parse_args(argv)
    payload = compile_one_sided_d2_v041_scout(arguments.root)
    if arguments.write:
        write_one_sided_d2_v041_scout(arguments.root, payload)
    print(
        json.dumps(
            {
                "artifact": RESULT_PATH,
                "written": arguments.write,
                "verdict": payload["verdict"],
                "profiles": {
                    name: {
                        "rank": record["rank"],
                        "all_commutators_forced_within_declared_ansatz": record[
                            "all_Q1_through_Q4_commutators_forced_zero_within_declared_ansatz"
                        ],
                    }
                    for name, record in payload["profiles"].items()
                },
                "semantic_digest_sha256": payload["semantic_digest_sha256"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
