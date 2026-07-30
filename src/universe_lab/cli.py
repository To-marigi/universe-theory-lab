"""環境診断CLI。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

from universe_lab.validation import environment_report, run_validation_suite


def _render() -> int:
    console = Console()
    report = environment_report()
    table = Table(title="Universe Theory Lab / 計算バックエンド")
    table.add_column("Backend")
    table.add_column("Version / status")
    table.add_column("Ready")
    for backend in report["backends"]:
        table.add_row(
            backend["name"],
            backend["version"],
            "[green]yes[/green]" if backend["available"] else "[red]no[/red]",
        )
    console.print(table)

    result = run_validation_suite()
    checks = Table(title="独立検算")
    checks.add_column("Check")
    checks.add_column("Result")
    checks.add_column("Details")
    for check in result["checks"]:
        details = ", ".join(
            f"{key}={value}" for key, value in check.items() if key not in {"name", "passed"}
        )
        checks.add_row(
            check["name"],
            "[green]PASS[/green]" if check["passed"] else "[red]FAIL[/red]",
            details,
        )
    console.print(checks)
    return 0 if result["passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="宇宙理論研究環境を診断します")
    parser.add_argument("--json", type=Path, help="診断結果をJSONにも保存")
    args = parser.parse_args()
    exit_code = _render()
    if args.json:
        payload = {"environment": environment_report(), "validation": run_validation_suite()}
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
            newline="\n",
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
