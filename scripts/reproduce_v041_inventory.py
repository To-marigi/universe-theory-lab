"""Regenerate the static v0.4.1 one-sided-profile inventory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from universe_lab.final_theory.one_sided_d2_v041 import (
    RESULT_PATH,
    compile_one_sided_d2_v041,
    semantic_digest,
    write_one_sided_d2_v041_result,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--write", action="store_true", help="write the new inventory artifact")
    arguments = parser.parse_args(argv)
    payload = compile_one_sided_d2_v041(arguments.root)
    if arguments.write:
        write_one_sided_d2_v041_result(arguments.root, payload)
    print(
        json.dumps(
            {
                "artifact": RESULT_PATH,
                "written": arguments.write,
                "verdict": payload["verdict"],
                "budget_status": payload["budget_gate"]["status"],
                "q5_free_relation_count": payload["q5_free_relation_inventory"][
                    "q5_free_relation_ids"
                ]["count"],
                "core_counts": {
                    name: payload["q5_free_relation_inventory"][name]["count"]
                    for name in payload["profiles"]
                },
                "semantic_digest_sha256": semantic_digest(payload),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
