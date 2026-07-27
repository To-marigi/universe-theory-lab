"""Command-line interface for String-Compiler Bench v0.1."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from universe_lab.stringbench.benchmarks import run_f_heterotic_8d
from universe_lab.stringbench.iut import (
    FrameIsolationAudit,
    evaluate_iut_bridge,
)


def _root() -> Path:
    return Path(__file__).resolve().parents[3]


def _static_audit(root: Path) -> dict[str, Any]:
    specs = root / "String-Compiler-Bench" / "specs"
    required = (
        "frame_card.schema.json",
        "duality_link.schema.json",
        "vacuum_ir.schema.json",
    )
    checks: dict[str, bool] = {}
    errors: list[str] = []
    for name in required:
        path = specs / name
        checks[name] = path.exists()
        if not path.exists():
            errors.append(f"missing {path}")
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: {exc}")
    return {
        "name": "static_asset_audit",
        "checks": checks,
        "errors": errors,
        "passed": not errors,
    }


def _iut_result() -> dict[str, Any]:
    isolation = FrameIsolationAudit(
        raw_cross_frame_comparison_blocked=True,
        morphism_permission_checked=True,
        preserved_structure_recorded=True,
        forgotten_structure_recorded=True,
    )
    evaluation = evaluate_iut_bridge(isolation)
    return {
        "overall_status": evaluation.overall_status.value,
        "type_system_status": evaluation.type_system_status.value,
        "native_bridge_status": evaluation.native_bridge_status.value,
        "gates": [
            {
                **asdict(gate),
                "status": gate.status.value if gate.status is not None else None,
            }
            for gate in evaluation.gates
        ],
    }


def _full_payload(root: Path) -> dict[str, Any]:
    static = _static_audit(root)
    duality = run_f_heterotic_8d()
    iut = _iut_result()
    return {
        "suite": "String-Compiler Bench v0.1",
        "generated_at": datetime.now(UTC).isoformat(),
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "git_commit": "UNBORN_BRANCH_NO_COMMIT",
        },
        "static_audit": static,
        "duality": duality,
        "iut": iut,
        "overall_status": "PARTIAL",
        "string_compiler_v0_1_pass": False,
        "stopping_reason": (
            "four F-theory fibrations are symbolically checked, but the independent "
            "four-branch heterotic lowering, round trip, held-out split, and all "
            "critical mutations are not complete"
        ),
    }


def _save(payload: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def _print_summary(payload: dict[str, Any]) -> None:
    duality = payload["duality"]
    print(f"static_audit: {'PASS' if payload['static_audit']['passed'] else 'FAIL'}")
    print(f"f_theory_four_fibrations: {duality['f_theory']['status']}")
    print(f"heterotic_four_branch_lowering: {duality['heterotic']['status']}")
    print(f"round_trip: {duality['round_trip']['status']}")
    detected = duality["mutations"]["detected"]
    required = duality["mutations"]["required"]
    print(f"negative_controls: {detected}/{required}")
    print(f"iut: {payload['iut']['overall_status']}")
    print(f"overall: {payload['overall_status']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="String-Compiler Bench v0.1")
    parser.add_argument("--suite", choices=("all",), help="全トラックを実行")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/stringbench_v0.1.json"),
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("audit")
    duality_parser = subparsers.add_parser("duality")
    duality_parser.add_argument("--suite", default="f-heterotic-8d")
    subparsers.add_parser("iut-bridge")
    subparsers.add_parser("report")
    args = parser.parse_args()

    root = _root()
    if args.command == "audit":
        result = _static_audit(root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["passed"] else 1
    if args.command == "duality":
        if args.suite != "f-heterotic-8d":
            parser.error("only f-heterotic-8d is available")
        result = run_f_heterotic_8d()
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        # PARTIAL is a scientifically valid completed run, but not a suite PASS.
        return 0
    if args.command == "iut-bridge":
        result = _iut_result()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "report":
        output = root / args.output
        if not output.exists():
            print(f"missing report: {output}")
            return 1
        _print_summary(json.loads(output.read_text(encoding="utf-8")))
        return 0
    if args.suite == "all" or args.command is None:
        payload = _full_payload(root)
        output = root / args.output
        _save(payload, output)
        _print_summary(payload)
        print(f"Saved: {output}")
        return 0
    parser.error("choose a command or --suite all")


if __name__ == "__main__":
    raise SystemExit(main())
