"""Command-line interface for String-Compiler Bench v0.1 and v0.2."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from universe_lab.stringbench.benchmarks import (
    run_f_heterotic_8d,
    run_narain_period_v0_2,
)
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
        "narain_period_v0.2.schema.json",
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


def _git_commit(root: Path) -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "GIT_COMMIT_UNAVAILABLE"


def _v0_2_payload(root: Path) -> dict[str, Any]:
    static = _static_audit(root)
    duality = run_narain_period_v0_2()
    return {
        "suite": "String-Compiler Bench v0.2 Narain-Period Bridge",
        "generated_at": datetime.now(UTC).isoformat(),
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "git_commit": _git_commit(root),
        },
        "static_audit": static,
        "duality": duality,
        "iut": _iut_result(),
        "engineering_status": duality["engineering_status"],
        "scientific_status": duality["scientific_status"],
        "overall_status": duality["overall_status"],
        "known_8d_duality_reproduced": duality["known_8d_duality_reproduced"],
        "stopping_reason": duality["stopping_reason"],
    }


def _save(payload: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def _print_summary(payload: dict[str, Any]) -> None:
    duality = payload["duality"]
    if payload["suite"].startswith("String-Compiler Bench v0.2"):
        local = duality["local_heterotic_lowering"]
        bridge = duality["narain_period_bridge"]
        print(f"static_audit: {'PASS' if payload['static_audit']['passed'] else 'FAIL'}")
        print(f"local_heterotic_lowering: {local['status']}")
        print(f"global_narain_orbit: {bridge['global_orbit_status']}")
        print(f"period_bridge: {bridge['period_status']}")
        print(
            "negative_controls: "
            f"{duality['mutations']['detected']}/{duality['mutations']['required']}"
        )
        print(f"engineering: {payload['engineering_status']}")
        print(f"scientific: {payload['scientific_status']}")
        print(f"overall: {payload['overall_status']}")
        return
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
    parser = argparse.ArgumentParser(description="String-Compiler Bench")
    parser.add_argument("--suite", choices=("all", "v0.2"), help="対象トラックを実行")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/stringbench_v0.1.json"),
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("audit")
    duality_parser = subparsers.add_parser("duality")
    duality_parser.add_argument(
        "--suite",
        choices=("f-heterotic-8d", "narain-period-v0.2"),
        default="f-heterotic-8d",
    )
    subparsers.add_parser("iut-bridge")
    subparsers.add_parser("report")
    args = parser.parse_args()

    root = _root()
    if args.command == "audit":
        result = _static_audit(root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["passed"] else 1
    if args.command == "duality":
        result = (
            run_narain_period_v0_2()
            if args.suite == "narain-period-v0.2"
            else run_f_heterotic_8d()
        )
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
    if args.suite in {"all", "v0.2"} or args.command is None:
        is_v0_2 = args.suite == "v0.2"
        payload = _v0_2_payload(root) if is_v0_2 else _full_payload(root)
        requested_default = Path("results/stringbench_v0.1.json")
        output_argument = (
            Path("results/stringbench_v0.2.json")
            if is_v0_2 and args.output == requested_default
            else args.output
        )
        output = root / output_argument
        _save(payload, output)
        _print_summary(payload)
        print(f"Saved: {output}")
        return 0
    parser.error("choose a command or --suite all")


if __name__ == "__main__":
    raise SystemExit(main())
