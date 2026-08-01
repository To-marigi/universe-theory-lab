"""Reproduce the fail-closed v0.4.2 source-to-direct provenance audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from universe_lab.final_theory.single_msr_elimination_v042 import (
    RESULT_PATH,
    compile_single_msr_source_to_direct_audit_v042,
    write_single_msr_source_to_direct_audit_v042,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--write-audit", action="store_true")
    arguments = parser.parse_args(argv)
    payload = compile_single_msr_source_to_direct_audit_v042(arguments.root)
    if arguments.write_audit:
        write_single_msr_source_to_direct_audit_v042(arguments.root, payload)
    print(
        json.dumps(
            {
                "audit": RESULT_PATH,
                "written": arguments.write_audit,
                "verdict": payload["verdict"],
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
