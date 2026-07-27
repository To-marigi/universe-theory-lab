"""QG-Bench v0.1 command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from universe_lab.qgbench.benchmarks import ReproductionConfig, run_qgbench, save_results
from universe_lab.qgbench.schemas import (
    load_json_yaml,
    validate_claim_graph,
    validate_theory_card,
)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def validate_knowledge_base(root: Path) -> list[str]:
    """Atlas と Claim Graph をまとめて検証する。"""

    errors: list[str] = []
    atlas = root / "QG-Bench" / "atlas"
    for path in sorted(atlas.glob("*.yaml")):
        try:
            card = load_json_yaml(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: {exc}")
            continue
        errors.extend(f"{path}: {error}" for error in validate_theory_card(card))
    claims = sorted((root / "QG-Bench" / "claims").glob("*.jsonl"))
    errors.extend(validate_claim_graph(claims))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="QG-Bench v0.1")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/qgbench_v0.1.json"),
        help="ベンチマーク結果JSON",
    )
    parser.add_argument("--quick", action="store_true", help="CI向け小規模設定")
    parser.add_argument(
        "--validate-only", action="store_true", help="Atlas/Claim Graphだけを検証"
    )
    args = parser.parse_args()

    root = _repository_root()
    errors = validate_knowledge_base(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 2
    print("Knowledge base: PASS")
    if args.validate_only:
        return 0

    config = None
    if args.quick:
        config = ReproductionConfig(
            counts=(70, 110),
            seeds=(1729, 1730),
            bins=10,
            minimum_bin_count=6,
        )
    result = run_qgbench(config, full=not args.quick)
    save_results(result, root / args.output)
    for benchmark in result["benchmarks"]:
        outcome = "PASS" if benchmark["acceptance"]["passed"] else "FAIL"
        print(f"{benchmark['name']}: {outcome}")
    print(f"Saved: {root / args.output}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
