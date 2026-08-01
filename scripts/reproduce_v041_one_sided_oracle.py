"""Audit v0.4.1 QQ arithmetic under the corrected restricted-locus scope."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from universe_lab.final_theory.one_sided_elimination_oracle_v041 import (
    compile_one_sided_elimination_oracle_v041,
    write_one_sided_elimination_oracle_v041,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args(argv)
    payload = compile_one_sided_elimination_oracle_v041(arguments.root)
    if arguments.write:
        write_one_sided_elimination_oracle_v041(arguments.root, payload)
    print(
        json.dumps(
            {
                key: payload[key]
                for key in (
                    "verdict",
                    "terminal_verdict",
                    "source_artifact_mode",
                    "verified_certificate_count",
                    "semantic_digest_sha256",
                )
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
