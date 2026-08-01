"""Reproduce the fail-closed v0.4.1 955-core partial-slice audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from universe_lab.final_theory.partial_slice_audit_v041 import (
    RESULT_PATH,
    audit_partial_slice_v041,
    write_partial_slice_audit_v041,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--write-audit", action="store_true")
    arguments = parser.parse_args(argv)

    payload = audit_partial_slice_v041(arguments.root)
    if arguments.write_audit:
        write_partial_slice_audit_v041(arguments.root, payload)
    print(
        json.dumps(
            {
                "audit": RESULT_PATH,
                "written": arguments.write_audit,
                "verdict": payload["verdict"],
                "passed": payload["passed"],
                "solver_invoked": False,
                "semantic_digest_sha256": payload["semantic_digest_sha256"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
