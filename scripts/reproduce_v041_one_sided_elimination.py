"""Compile or run the scope-corrected v0.4.1 restricted-locus QQ campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from universe_lab.final_theory.one_sided_elimination_v041 import (
    CAMPAIGN_PATH,
    MANIFEST_PATH,
    PROFILES,
    compile_one_sided_qq_manifest_v041,
    run_one_sided_qq_campaign_v041,
    write_one_sided_qq_manifest_v041,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--profile", choices=PROFILES, action="append")
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument(
        "--run-qq",
        action="store_true",
        help="explicitly invoke Sage/Singular for the bounded QQ-only campaign",
    )
    arguments = parser.parse_args(argv)
    profiles = tuple(arguments.profile) if arguments.profile else PROFILES
    if len(set(profiles)) != len(profiles):
        parser.error("--profile may not be repeated")
    if arguments.run_qq:
        payload = run_one_sided_qq_campaign_v041(arguments.root, profiles=profiles)
        print(
            json.dumps(
                {
                    "written_campaign": CAMPAIGN_PATH,
                    "verdict": payload["verdict"],
                    "planned_run_count": payload["planned_run_count"],
                    "completed_or_terminal_run_count": payload["completed_or_terminal_run_count"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    manifest = compile_one_sided_qq_manifest_v041(arguments.root, profiles=profiles)
    if arguments.write_manifest:
        write_one_sided_qq_manifest_v041(arguments.root, manifest)
    print(
        json.dumps(
            {
                "manifest": MANIFEST_PATH,
                "written": arguments.write_manifest,
                "verdict": manifest["verdict"],
                "planned_run_count": manifest["planned_run_count"],
                "coefficient_fields": manifest["coefficient_fields"],
                "solver_invoked": False,
                "semantic_digest_sha256": manifest["semantic_digest_sha256"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
