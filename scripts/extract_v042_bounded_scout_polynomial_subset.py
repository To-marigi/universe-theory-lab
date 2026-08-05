"""Extract or verify the 20-record bounded-scout polynomial subset fixture.

The default --check mode is read-only. It authenticates every available full
polynomial-arena chunk through the legacy scanner, regenerates the exact
canonical subset bytes in memory, and rejects any fixture difference. The
--write mode is an explicit maintenance operation; after it changes bytes, the
reproduction-input manifest must be intentionally regenerated and reviewed.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from universe_lab.final_theory import (
    sr2v_q5_free_auxiliary_ideal_scout_fixtures_v042 as fixtures,
)
from universe_lab.final_theory import sr2v_q5_free_auxiliary_ideal_worker_v042 as worker


def _extract(repository_root: Path) -> bytes:
    request_path, _prior_result = fixtures.find_stage7_request(repository_root)
    request = worker.load_verified_request(request_path)
    root = worker.load_verified_root(repository_root, request)
    records, loaded_terms = worker._scan_needed_records(
        repository_root,
        root,
        set(fixtures.REQUIRED_POLYNOMIAL_IDS),
        worker.Emitter(),
    )
    if (
        len(records) != len(fixtures.REQUIRED_POLYNOMIAL_IDS)
        or loaded_terms != fixtures.CANDIDATE_ROW10_LOADED_TERM_COUNT
    ):
        raise RuntimeError("full-arena extraction record or term count mismatch")
    payload = fixtures.build_bounded_polynomial_subset_fixture(records)
    return fixtures.canonical_json_bytes(payload) + b"\n"


def run(repository_root: Path, *, write: bool) -> None:
    if not write:
        fixtures.validate_bounded_scout_reproduction_inputs(repository_root)
    expected = _extract(repository_root)
    fixture_path = repository_root / fixtures.POLYNOMIAL_SUBSET_FIXTURE
    if write:
        fixture_path.write_bytes(expected)
        print("bounded_scout_subset=WRITTEN")
        return
    if fixture_path.read_bytes() != expected:
        raise RuntimeError(
            "bounded-scout polynomial subset differs from authenticated full-arena extraction"
        )
    print("bounded_scout_subset=OK")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repository_root", nargs="?", type=Path, default=Path.cwd())
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="read-only verification (default)")
    mode.add_argument("--write", action="store_true", help="explicitly rewrite the fixture")
    arguments = parser.parse_args()
    del arguments.check
    run(arguments.repository_root.resolve(), write=arguments.write)


if __name__ == "__main__":
    main()
