"""Headless Sage/Singular backend for Final-Theory Bench v0.3.5.

The host side invokes the already configured Sage container with JSON on
stdin.  The worker loads the frozen v0.3.4 scalar-expression arena, applies
one exact S1/S2 chart substitution, and performs polynomial ideal operations
over either QQ or a declared finite field.

Finite-field runs are scouts only.  An ideal-solve proof must have
``coefficient_field == "QQ"`` and ``proof_eligible == true``.  A request
that directly verifies a complete exact identity inventory instead uses
the separate ``identity_proof_eligible`` gate.
"""

from __future__ import annotations

import argparse
import contextlib
import gzip
import hashlib
import io
import json
import platform
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import sympy as sp

from universe_lab.final_theory.d2_strata_v034 import (
    StratumChart,
    stratum_charts,
)
from universe_lab.final_theory.gc_semantics_v033 import stable_hash

DEFAULT_ARENA_PATH = "certificates/d2_rational_dag/scalar_expression_arena.json"
DEFAULT_COMPACT_ARENA_PATH = (
    "certificates/d2_saturation/"
    "v0.3.5_compact_expression_arena.json.gz"
)
DEFAULT_DIRECT_SYSTEM_PATH = (
    "certificates/d2_saturation/v0.3.5_direct_operator_system.json"
)
DEFAULT_SYSTEM_PATH = "results/v0.3.4_polynomial_systems.json"
SAGE_CONTAINER_ROOT = Path("/home/sage/work")
LEGACY_RESPONSE_SCHEMA = "final-theory-d2-sage-response-v0.3.5"


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


def _request_semantic_digest(payload: dict[str, Any]) -> str:
    """Hash the semantic request while excluding host-generated identity."""

    return stable_hash(
        {
            key: value
            for key, value in payload.items()
            if key
            not in {
                "request_id",
                "request_semantic_digest_sha256",
            }
        }
    )


def _validated_request_semantic_digest(
    payload: dict[str, Any],
) -> str | None:
    expected = payload.get("request_semantic_digest_sha256")
    if expected is None:
        return None
    actual = _request_semantic_digest(payload)
    if actual != expected:
        raise ValueError(
            "request semantic digest mismatch: "
            f"{actual} != {expected}"
        )
    return actual


def _result_semantic_digest(
    result: dict[str, Any],
    *,
    selection_fields: tuple[str, ...],
) -> str:
    """Preserve v0.3.5 hashes; bind selections only in newer schemas."""

    semantic_payload: dict[str, Any] = {
        "chart": result["chart"],
        "field": result["coefficient_field"],
        "initial_basis": result["initial_groebner_basis"],
        "saturation_trace": result["saturation_trace"],
        "noncommutativity_checks": result[
            "noncommutativity_checks"
        ],
    }
    if result["schema_version"] != LEGACY_RESPONSE_SCHEMA:
        semantic_payload.update(
            {
                field: result.get(field)
                for field in selection_fields
            }
        )
        semantic_payload["request_semantic_digest_sha256"] = result.get(
            "request_semantic_digest_sha256"
        )
    return stable_hash(semantic_payload)


def _zero_condition_substitution(
    conditions: tuple[sp.Expr, ...],
) -> dict[sp.Symbol, sp.Expr]:
    """Solve the triangular chart equalities exactly."""

    substitutions: dict[sp.Symbol, sp.Expr] = {}
    for condition in conditions:
        reduced = sp.expand(condition.subs(substitutions))
        if reduced == 0:
            continue
        symbols = sorted(reduced.free_symbols, key=str)
        if not symbols:
            raise ValueError(f"inconsistent chart equality: {condition}")
        target = symbols[-1]
        solutions = sp.solve(reduced, target, dict=False)
        if len(solutions) != 1:
            raise ValueError(f"chart equality is not triangular: {condition}")
        substitutions[target] = sp.cancel(solutions[0].subs(substitutions))
    return substitutions


def _chart_descriptor(chart: StratumChart) -> dict[str, Any]:
    zero_substitutions = _zero_condition_substitution(chart.zero_conditions)
    q_substitutions = {
        name: sp.cancel(expression.subs(zero_substitutions))
        for name, expression in chart.substitutions.items()
    }
    nonzero_conditions = [
        sp.factor(condition.subs(zero_substitutions))
        for condition in chart.nonzero_conditions
    ]
    q_matrices: dict[int, sp.Matrix] = {}
    for stage in chart.q_indices:
        q_matrices[stage] = sp.Matrix(
            [
                [
                    q_substitutions[f"q{stage}_11"],
                    q_substitutions[f"q{stage}_12"],
                ],
                [
                    q_substitutions[f"q{stage}_21"],
                    q_substitutions[f"q{stage}_22"],
                ],
            ]
        )

    commutator_components: list[dict[str, Any]] = []
    for left_index, left in sorted(q_matrices.items()):
        for right_index, right in sorted(q_matrices.items()):
            if left_index >= right_index:
                continue
            commutator = (left * right - right * left).applyfunc(
                lambda value: sp.factor(value.subs(zero_substitutions))
            )
            # A 2x2 commutator is traceless, hence these three entries suffice.
            for row, column in ((0, 0), (0, 1), (1, 0)):
                expression = commutator[row, column]
                if expression == 0:
                    continue
                commutator_components.append(
                    {
                        "pair": [left_index, right_index],
                        "entry": [row, column],
                        "expression": sp.sstr(expression),
                    }
                )

    free_symbols: set[sp.Symbol] = set()
    for expression in (
        list(q_substitutions.values())
        + nonzero_conditions
        + [
            sp.sympify(record["expression"])
            for record in commutator_components
        ]
    ):
        free_symbols.update(expression.free_symbols)
    variables = sorted(free_symbols, key=str)

    return {
        "chart": chart.chart_id,
        "stratum": chart.stratum,
        "source_index_branch": chart.source_index_branch,
        "variables": [str(symbol) for symbol in variables],
        "q_substitutions": {
            name: sp.sstr(expression)
            for name, expression in sorted(q_substitutions.items())
        },
        "zero_substitutions": {
            str(name): sp.sstr(expression)
            for name, expression in sorted(
                zero_substitutions.items(), key=lambda item: str(item[0])
            )
        },
        "chart_nonzero_conditions": [
            sp.sstr(expression) for expression in nonzero_conditions
        ],
        "commutator_components": commutator_components,
        "cover_provenance": list(chart.cover_provenance),
        "residual_gauge": chart.residual_gauge,
        "pivot": chart.pivot,
    }


def build_chart_payload(
    source_index_branch: str,
    chart_id: str,
    *,
    coefficient_modulus: int = 0,
    operation: str = "compile",
    maximum_source_stage: int = 4,
    saturation: bool = False,
    check_noncommutativity: bool = False,
    factor_denominators: bool = True,
    expression_source: str = "direct_operator",
    include_all_transition_predicates: bool | None = None,
    groebner_algorithm: str = "libsingular:slimgb",
    groebner_strategy: str = "progressive",
    progressive_batch_size: int = 4,
    saturation_factor_order: str = "forward",
) -> dict[str, Any]:
    """Build a small request; the worker reads frozen large artifacts itself."""

    chart = next(
        candidate
        for candidate in stratum_charts(source_index_branch)
        if candidate.chart_id == chart_id
    )
    descriptor = _chart_descriptor(chart)
    return {
        "schema_version": "final-theory-d2-sage-request-v0.3.5",
        "operation": operation,
        "coefficient_modulus": coefficient_modulus,
        "maximum_source_stage": maximum_source_stage,
        "saturation": saturation,
        "check_noncommutativity": check_noncommutativity,
        "factor_denominators": factor_denominators,
        "expression_source": expression_source,
        "groebner_algorithm": groebner_algorithm,
        "groebner_strategy": groebner_strategy,
        "progressive_batch_size": progressive_batch_size,
        "saturation_factor_order": saturation_factor_order,
        "include_all_transition_predicates": (
            maximum_source_stage >= 4
            if include_all_transition_predicates is None
            else include_all_transition_predicates
        ),
        "arena_path": DEFAULT_ARENA_PATH,
        "compact_arena_path": DEFAULT_COMPACT_ARENA_PATH,
        "direct_system_path": DEFAULT_DIRECT_SYSTEM_PATH,
        "system_path": DEFAULT_SYSTEM_PATH,
        **descriptor,
    }


def detect_sage_backend(
    root: Path,
    *,
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    """Probe Sage and its embedded Singular through the configured container."""

    command = [
        "docker",
        "compose",
        "exec",
        "-T",
        "sage",
        "sage",
        "-c",
        (
            "from sage.version import version; "
            "import json; "
            "print(json.dumps({'sage':version,"
            "'singular':singular.version().splitlines()[0]}))"
        ),
    ]
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "available": False,
            "error": type(exc).__name__,
            "wall_time_seconds": time.perf_counter() - started,
            "command": command,
        }
    record: dict[str, Any] = {
        "available": completed.returncode == 0,
        "returncode": completed.returncode,
        "wall_time_seconds": time.perf_counter() - started,
        "command": command,
        "stderr": completed.stderr[-4000:],
    }
    if completed.returncode == 0:
        try:
            record.update(json.loads(completed.stdout.strip().splitlines()[-1]))
        except (IndexError, json.JSONDecodeError):
            record["available"] = False
            record["error"] = "NON_JSON_BACKEND_RESPONSE"
            record["stdout"] = completed.stdout[-4000:]
    else:
        record["stdout"] = completed.stdout[-4000:]
    return record


def run_sage_request(
    root: Path,
    payload: dict[str, Any],
    *,
    timeout_seconds: int,
) -> dict[str, Any]:
    """Execute one request in Sage; never substitute a SymPy fallback."""

    request_id = stable_hash(
        {
            "chart": payload["chart"],
            "field": payload["coefficient_modulus"],
            "operation": payload["operation"],
            "started_ns": time.time_ns(),
        }
    )[:20]
    payload = {**payload, "request_id": request_id}
    command = [
        "docker",
        "compose",
        "exec",
        "-T",
    ]
    if "omp_threads_per_worker" in payload:
        thread_count = int(payload["omp_threads_per_worker"])
        if thread_count <= 0:
            raise ValueError("omp_threads_per_worker must be positive")
        command.extend(
            [
                "-e",
                f"OMP_NUM_THREADS={thread_count}",
                "-e",
                f"OPENBLAS_NUM_THREADS={thread_count}",
            ]
        )
    command.extend(
        [
            "-e",
            "PYTHONPATH=/home/sage/work/src",
            "sage",
            "sage",
            "-python",
            (
                "/home/sage/work/src/universe_lab/final_theory/"
                "d2_sage_backend_v035.py"
            ),
            "--worker",
            "--request-id",
            request_id,
        ]
    )
    started = time.perf_counter()
    process = subprocess.Popen(
        command,
        cwd=root,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        stdout, stderr = process.communicate(
            _canonical_json(payload),
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        subprocess.run(
            [
                "docker",
                "compose",
                "exec",
                "-T",
                "sage",
                "pkill",
                "-f",
                (
                    "d2_sage_backend_v035.py --worker --request-id "
                    f"{request_id}"
                ),
            ],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
        process.kill()
        try:
            stdout, stderr = process.communicate(timeout=20)
        except subprocess.TimeoutExpired:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
        return {
            "schema_version": payload.get(
                "response_schema_version",
                LEGACY_RESPONSE_SCHEMA,
            ),
            "chart": payload["chart"],
            "source_index_branch": payload["source_index_branch"],
            "coefficient_field": (
                "QQ"
                if int(payload["coefficient_modulus"]) == 0
                else f"GF({payload['coefficient_modulus']})"
            ),
            "backend": "Sage/Singular exact subprocess",
            "budget_file_sha256": payload.get("budget_file_sha256"),
            "request_semantic_digest_sha256": payload.get(
                "request_semantic_digest_sha256"
            ),
            "request_id": request_id,
            "time_limit_seconds": timeout_seconds,
            "wall_time_seconds": time.perf_counter() - started,
            "exit_status": "TIMEOUT",
            "proof_eligible": False,
            "stdout_tail": (stdout or "")[-4000:],
            "stderr_tail": (stderr or "")[-4000:],
            "verdict": "CPOBC_D2_PARTIAL",
        }
    if process.returncode != 0:
        return {
            "schema_version": payload.get(
                "response_schema_version",
                LEGACY_RESPONSE_SCHEMA,
            ),
            "chart": payload["chart"],
            "source_index_branch": payload["source_index_branch"],
            "coefficient_field": (
                "QQ"
                if int(payload["coefficient_modulus"]) == 0
                else f"GF({payload['coefficient_modulus']})"
            ),
            "coefficient_modulus": int(payload["coefficient_modulus"]),
            "backend": "Sage/Singular exact subprocess",
            "budget_file_sha256": payload.get("budget_file_sha256"),
            "request_semantic_digest_sha256": payload.get(
                "request_semantic_digest_sha256"
            ),
            "request_id": request_id,
            "time_limit_seconds": timeout_seconds,
            "wall_time_seconds": time.perf_counter() - started,
            "exit_status": f"ERROR_{process.returncode}",
            "proof_eligible": False,
            "stdout_tail": stdout[-4000:],
            "stderr_tail": stderr[-8000:],
            "verdict": "CPOBC_D2_PARTIAL",
        }
    try:
        result = json.loads(stdout)
    except json.JSONDecodeError:
        return {
            "schema_version": payload.get(
                "response_schema_version",
                LEGACY_RESPONSE_SCHEMA,
            ),
            "chart": payload["chart"],
            "source_index_branch": payload["source_index_branch"],
            "coefficient_field": (
                "QQ"
                if int(payload["coefficient_modulus"]) == 0
                else f"GF({payload['coefficient_modulus']})"
            ),
            "coefficient_modulus": int(payload["coefficient_modulus"]),
            "backend": "Sage/Singular exact subprocess",
            "budget_file_sha256": payload.get("budget_file_sha256"),
            "request_semantic_digest_sha256": payload.get(
                "request_semantic_digest_sha256"
            ),
            "request_id": request_id,
            "time_limit_seconds": timeout_seconds,
            "wall_time_seconds": time.perf_counter() - started,
            "exit_status": "NON_JSON_BACKEND_RESPONSE",
            "proof_eligible": False,
            "stdout_tail": stdout[-8000:],
            "stderr_tail": stderr[-8000:],
            "verdict": "CPOBC_D2_PARTIAL",
        }
    result["host_observed_wall_time_seconds"] = time.perf_counter() - started
    result["time_limit_seconds"] = timeout_seconds
    result["worker_stderr_tail"] = stderr[-4000:]
    result["request_id"] = request_id
    return result


def _worker_normalise(polynomial: Any) -> Any:
    if polynomial == 0:
        return polynomial
    return polynomial / polynomial.lc()


def _worker_factor_set(
    polynomials: list[Any],
) -> tuple[list[Any], list[dict[str, Any]], dict[str, Any]]:
    unique: dict[str, Any] = {}
    provenance: dict[str, list[dict[str, int]]] = {}
    grouped_source_records: dict[str, dict[str, Any]] = {}
    grouped_source_indices: dict[str, list[int]] = {}
    for index, polynomial in enumerate(polynomials):
        if polynomial == 0:
            return (
                [],
                [
                    {
                        "status": "ZERO_REQUIRED_FACTOR",
                        "source_factor_index": index,
                    }
                ],
                {
                    "all_source_factorisations_reconstructed_exactly": False,
                    "zero_required_factor": True,
                    "source_factorisations": [
                        {
                            "source_factor_index": index,
                            "status": "ZERO_REQUIRED_FACTOR",
                        }
                    ],
                },
            )
        factorisation = polynomial.factor()
        reconstructed = factorisation.unit()
        source_factors: list[dict[str, Any]] = []
        for factor, multiplicity in factorisation:
            reconstructed *= factor ** multiplicity
            normalised = _worker_normalise(factor)
            key = str(normalised)
            unique.setdefault(key, normalised)
            provenance.setdefault(key, []).append(
                {
                    "source_factor_index": index,
                    "multiplicity": int(multiplicity),
                }
            )
            source_factors.append(
                {
                    "normalised_factor": key,
                    "multiplicity": int(multiplicity),
                }
            )
        source_record = {
            "source_polynomial_sha256": stable_hash(str(polynomial)),
            "factorisation_unit": str(factorisation.unit()),
            "irreducible_factors": source_factors,
            "exact_reconstruction_verified": reconstructed == polynomial,
        }
        source_signature = stable_hash(source_record)
        grouped_source_records.setdefault(source_signature, source_record)
        grouped_source_indices.setdefault(source_signature, []).append(index)
    source_records = []
    for source_signature in sorted(grouped_source_records):
        indices = grouped_source_indices[source_signature]
        source_records.append(
            {
                **grouped_source_records[source_signature],
                "source_occurrence_count": len(indices),
                "source_factor_indices_sha256": stable_hash(indices),
                "source_factor_indices_preview": indices[:64],
                "source_factor_indices_preview_truncated": len(indices) > 64,
            }
        )
    records = [
        {
            "factor": key,
            "source_occurrence_count": len(provenance[key]),
            "source_occurrences_sha256": stable_hash(provenance[key]),
            "source_occurrences_preview": provenance[key][:32],
            "source_occurrences_preview_truncated": (
                len(provenance[key]) > 32
            ),
        }
        for key in sorted(unique)
    ]
    equivalence = {
        "all_source_factorisations_reconstructed_exactly": all(
            record["exact_reconstruction_verified"]
            for record in source_records
        ),
        "zero_required_factor": False,
        "source_factorisations": source_records,
        "unique_source_polynomial_count": len(source_records),
        "source_polynomial_occurrence_count": len(polynomials),
        "deduplication_preserves_saturation": True,
        "justification": (
            "Over a field, saturation by a nonzero scalar unit, repeated "
            "irreducible factors, and duplicate factors is unchanged; every "
            "source polynomial was reconstructed exactly from its recorded "
            "unit, irreducible factors, and multiplicities."
        ),
    }
    return [unique[key] for key in sorted(unique)], records, equivalence


def _worker_basis_summary(basis: Any) -> dict[str, Any]:
    values = [str(polynomial) for polynomial in basis]
    return {
        "polynomial_count": len(values),
        "total_character_count": sum(len(value) for value in values),
        "polynomial_character_counts": [len(value) for value in values],
        "is_unit_basis": values == ["1"],
        "sha256": stable_hash(values),
        "preview": [value[:2000] for value in values[:3]],
        "preview_truncated": (
            len(values) > 3 or any(len(value) > 2000 for value in values[:3])
        ),
    }


def _worker_emit_progress(
    payload: dict[str, Any],
    record: dict[str, Any],
) -> None:
    request_id = payload.get("request_id")
    if not request_id:
        return
    progress_path = (
        SAGE_CONTAINER_ROOT
        / "certificates"
        / "d2_saturation"
        / "progress"
        / f"{request_id}.jsonl"
    )
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    with progress_path.open(
        "a",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        handle.write(_canonical_json(record) + "\n")


def _worker_initial_groebner(
    ring: Any,
    equations: list[Any],
    equation_provenance: dict[str, list[dict[str, Any]]],
    *,
    algorithm: str,
    strategy: str,
    progressive_batch_size: int,
) -> tuple[Any, Any, float, list[dict[str, Any]], int]:
    """Compute the numerator ideal, optionally growing it stage by stage.

    If a subset already has Gröbner basis ``[1]``, that is an exact
    certificate that the ideal generated by every equation is also the unit
    ideal, so later generators need not be processed.
    """

    started = time.perf_counter()
    if strategy == "none":
        ideal = ring.ideal(equations)
        return ideal, [], 0.0, [{"strategy": "NOT_COMPUTED"}], 0
    if strategy != "progressive" or not equations:
        ideal = ring.ideal(equations)
        basis = ideal.groebner_basis(algorithm=algorithm)
        return (
            ideal,
            basis,
            time.perf_counter() - started,
            [
                {
                    "strategy": "ONE_SHOT",
                    "equations_added": len(equations),
                    "total_equations_covered": len(equations),
                    "wall_time_seconds": time.perf_counter() - started,
                    "groebner_basis": _worker_basis_summary(basis),
                }
            ],
            len(equations),
        )

    def equation_key(polynomial: Any) -> tuple[int, int, int, str]:
        key = str(polynomial)
        provenance = equation_provenance[key]
        minimum_stage = min(
            int(record["source_stage"]) for record in provenance
        )
        return (
            minimum_stage,
            int(polynomial.degree()),
            len(polynomial.monomials()),
            key,
        )

    ordered = sorted(equations, key=equation_key)
    low_stage = [
        polynomial
        for polynomial in ordered
        if equation_key(polynomial)[0] <= 3
    ]
    high_stage = [
        polynomial
        for polynomial in ordered
        if equation_key(polynomial)[0] > 3
    ]
    batches: list[list[Any]] = []
    if low_stage:
        batches.append(low_stage)
    batch_size = max(1, int(progressive_batch_size))
    batches.extend(
        high_stage[index : index + batch_size]
        for index in range(0, len(high_stage), batch_size)
    )

    basis: Any = []
    ideal = ring.ideal([])
    trace: list[dict[str, Any]] = []
    covered = 0
    for batch_index, batch in enumerate(batches):
        batch_started = time.perf_counter()
        generators = list(basis) + batch if basis else batch
        ideal = ring.ideal(generators)
        basis = ideal.groebner_basis(algorithm=algorithm)
        covered += len(batch)
        unit = len(basis) == 1 and basis[0] == ring.one()
        trace.append(
            {
                "strategy": "PROGRESSIVE",
                "batch_index": batch_index,
                "equations_added": len(batch),
                "total_equations_covered": covered,
                "minimum_source_stage": min(
                    equation_key(polynomial)[0] for polynomial in batch
                ),
                "maximum_source_stage": max(
                    equation_key(polynomial)[0] for polynomial in batch
                ),
                "wall_time_seconds": time.perf_counter() - batch_started,
                "unit_ideal": unit,
                "groebner_basis": _worker_basis_summary(basis),
            }
        )
        if unit:
            break
    return ideal, basis, time.perf_counter() - started, trace, covered


def _worker_versions() -> dict[str, str]:
    from sage.all import singular  # type: ignore[import-not-found]
    from sage.version import version

    return {
        "sage": version,
        "singular": singular.version().splitlines()[0],
        "python": platform.python_version(),
    }


def _worker_apply_memory_limit(
    payload: dict[str, Any],
    resource_module: Any,
) -> dict[str, Any]:
    """Apply an optional hard address-space limit inside the Sage worker."""

    supplied = payload.get("memory_limit_bytes")
    if supplied is None:
        return {
            "requested": False,
            "resource": "RLIMIT_AS",
            "limit_bytes": None,
            "applied": False,
        }
    limit = int(supplied)
    if limit <= 0:
        raise ValueError("memory_limit_bytes must be positive")
    previous_soft, previous_hard = resource_module.getrlimit(
        resource_module.RLIMIT_AS
    )
    infinity = resource_module.RLIM_INFINITY
    effective = (
        limit
        if previous_hard == infinity
        else min(limit, int(previous_hard))
    )
    resource_module.setrlimit(
        resource_module.RLIMIT_AS,
        (effective, effective),
    )
    return {
        "requested": True,
        "resource": "RLIMIT_AS",
        "limit_bytes": limit,
        "effective_limit_bytes": effective,
        "previous_soft_limit_bytes": (
            None if previous_soft == infinity else int(previous_soft)
        ),
        "previous_hard_limit_bytes": (
            None if previous_hard == infinity else int(previous_hard)
        ),
        "applied": True,
    }


def _worker_execute_direct(payload: dict[str, Any]) -> dict[str, Any]:
    """Evaluate reduced operator words directly over a Sage fraction field."""

    import resource

    from sage.all import GF, QQ, MatrixSpace, PolynomialRing  # type: ignore[import-not-found]

    started = time.perf_counter()
    memory_limit = _worker_apply_memory_limit(payload, resource)
    request_semantic_digest = _validated_request_semantic_digest(payload)
    modulus = int(payload["coefficient_modulus"])
    coefficient_field = QQ if modulus == 0 else GF(modulus)
    variable_names = tuple(payload["variables"])
    ring = PolynomialRing(
        coefficient_field,
        names=variable_names,
        order="degrevlex",
    )
    fraction_field = ring.fraction_field()
    matrices = MatrixSpace(fraction_field, 2)
    substitutions = {
        name: fraction_field(ring(expression.replace("**", "^")))
        for name, expression in payload["q_substitutions"].items()
    }
    q_matrices = {
        f"Q_{stage}": matrices(
            [
                substitutions[f"q{stage}_11"],
                substitutions[f"q{stage}_12"],
                substitutions[f"q{stage}_21"],
                substitutions[f"q{stage}_22"],
            ]
        )
        for stage in sorted(
            {
                int(name.split("_", 1)[0][1:])
                for name in payload["q_substitutions"]
            }
        )
    }
    identity = matrices.identity_matrix()

    direct_system_path = (
        SAGE_CONTAINER_ROOT / payload["direct_system_path"]
    )
    direct_system_bytes = direct_system_path.read_bytes()
    direct_system_file_sha256 = hashlib.sha256(
        direct_system_bytes
    ).hexdigest()
    direct_payload = json.loads(direct_system_bytes)
    direct_system_semantic_digest_sha256 = stable_hash(
        {
            "dependency_nodes": direct_payload["dependency_nodes"],
            "relations": direct_payload["relations"],
            "transitions": direct_payload[
                "reconstructed_transition_predicates"
            ],
        }
    )
    direct_system_self_semantic_digest_valid = (
        direct_payload.get("semantic_digest_sha256")
        == direct_system_semantic_digest_sha256
    )
    expected_direct_file_sha256 = payload.get(
        "expected_direct_system_file_sha256"
    )
    expected_direct_semantic_digest = payload.get(
        "expected_direct_system_semantic_digest_sha256"
    )
    if (
        expected_direct_file_sha256 is not None
        and direct_system_file_sha256 != expected_direct_file_sha256
    ):
        raise ValueError("direct-system file SHA-256 mismatch")
    if (
        expected_direct_semantic_digest is not None
        and direct_system_semantic_digest_sha256
        != expected_direct_semantic_digest
    ):
        raise ValueError("direct-system semantic digest mismatch")
    if not direct_system_self_semantic_digest_valid:
        raise ValueError("direct-system self semantic digest mismatch")
    definitions = {
        record["node_id"]: record
        for record in direct_payload["dependency_nodes"]
    }
    matrix_cache: dict[str, Any] = dict(q_matrices)
    inverse_factor_records: list[dict[str, Any]] = []
    raw_required_factors: list[Any] = []

    def record_fraction_nonzero(
        value: Any,
        *,
        origin: str,
        kind: str,
    ) -> None:
        numerator = ring(value.numerator())
        denominator = ring(value.denominator())
        if numerator != ring.one():
            raw_required_factors.append(numerator)
            inverse_factor_records.append(
                {
                    "origin": origin,
                    "kind": kind,
                    "factor": str(numerator),
                }
            )
        if denominator != ring.one():
            raw_required_factors.append(denominator)
            inverse_factor_records.append(
                {
                    "origin": f"denominator({origin})",
                    "kind": "RATIONAL_DENOMINATOR",
                    "factor": str(denominator),
                }
            )

    def invert(matrix: Any, *, origin: str) -> Any:
        determinant = matrix.det()
        record_fraction_nonzero(
            determinant,
            origin=f"det({origin})",
            kind="INVERSE_SITE",
        )
        return matrix.inverse()

    def product(factors: list[Any]) -> Any:
        result = identity
        for factor in factors:
            result *= factor
        return result

    word_product_cache: dict[tuple[str, ...], Any] = {}
    word_product_evaluation_count = 0

    def word_product(word_nodes: list[str]) -> Any:
        nonlocal word_product_evaluation_count
        key = tuple(word_nodes)
        cacheable = all(item.startswith("Q_") for item in word_nodes)
        if cacheable:
            existing = word_product_cache.get(key)
            if existing is not None:
                return existing
        result = product([node(item) for item in word_nodes])
        word_product_evaluation_count += 1
        if cacheable:
            word_product_cache[key] = result
        return result

    visiting: set[str] = set()

    def node(node_id: str) -> Any:
        existing = matrix_cache.get(node_id)
        if existing is not None:
            return existing
        if node_id in visiting:
            raise RuntimeError(f"operator DAG cycle at {node_id}")
        visiting.add(node_id)
        definition = definitions[node_id]
        kind = definition["kind"]
        if kind == "Q_GENERATOR":
            result = q_matrices[node_id]
        elif kind == "Q_GENERATOR_INVERSE":
            base = node_id.removesuffix("^-1")
            result = invert(q_matrices[base], origin=node_id)
        elif kind == "EQ107_EQ108_LINEAR_EXPRESSION":
            result = matrices.zero_matrix()
            for term in definition["terms"]:
                result += int(term["coefficient"]) * word_product(
                    term["word_nodes"]
                )
        elif kind == "FORMAL_TWO_SIDED_INVERSE_AUXILIARY":
            result = invert(
                node(definition["inverse_of_node"]),
                origin=node_id,
            )
        elif kind in {"EQ112_CONJUGATE", "EQ112_CONJUGATE_INVERSE"}:
            result = word_product(definition["ordered_word"])
        else:
            raise ValueError(f"unsupported dependency kind: {kind}")
        visiting.remove(node_id)
        matrix_cache[node_id] = result
        return result

    expression_evaluation_count = 0

    def expression(terms: list[dict[str, Any]]) -> Any:
        nonlocal expression_evaluation_count
        result = matrices.zero_matrix()
        for term in terms:
            result += int(term["coefficient"]) * word_product(
                term["word"]
            )
        expression_evaluation_count += 1
        return result

    stage_selected_relations = [
        record
        for record in direct_payload["relations"][
            payload["source_index_branch"]
        ]
        if int(record["source_stage"])
        <= int(payload["maximum_source_stage"])
    ]
    included_relation_families = {
        str(value)
        for value in payload.get("included_relation_families", [])
    }
    excluded_relation_ids = {
        str(value) for value in payload.get("excluded_relation_ids", [])
    }
    selected_relations = [
        record
        for record in stage_selected_relations
        if (
            not included_relation_families
            or record["family"] in included_relation_families
        )
        and record["relation_id"] not in excluded_relation_ids
    ]
    selected_relation_ids = sorted(
        record["relation_id"] for record in selected_relations
    )
    selected_relation_family_counts = dict(
        sorted(Counter(record["family"] for record in selected_relations).items())
    )
    forbidden_relation_families = {
        str(value)
        for value in payload.get("forbidden_relation_families", [])
    }
    selection_errors: list[str] = []
    expected_relation_count = payload.get("expected_selected_relation_count")
    if (
        expected_relation_count is not None
        and len(selected_relations) != int(expected_relation_count)
    ):
        selection_errors.append("selected matrix relation count mismatch")
    expected_family_counts = payload.get("expected_relation_family_counts")
    if (
        expected_family_counts is not None
        and selected_relation_family_counts
        != {
            str(name): int(count)
            for name, count in expected_family_counts.items()
        }
    ):
        selection_errors.append("selected relation-family counts mismatch")
    if forbidden_relation_families.intersection(
        selected_relation_family_counts
    ):
        selection_errors.append("forbidden relation family selected")
    expected_relation_digest = payload.get(
        "expected_selected_relation_ids_sha256"
    )
    selected_relation_ids_sha256 = stable_hash(selected_relation_ids)
    if (
        expected_relation_digest is not None
        and selected_relation_ids_sha256 != expected_relation_digest
    ):
        selection_errors.append("selected relation-ID digest mismatch")
    if selection_errors:
        raise RuntimeError(
            "direct relation selection failed: "
            + _canonical_json(
                {
                    "errors": selection_errors,
                    "selected_relation_count": len(selected_relations),
                    "selected_relation_family_counts": (
                        selected_relation_family_counts
                    ),
                    "selected_relation_ids_sha256": (
                        selected_relation_ids_sha256
                    ),
                }
            )
        )
    unique_equations: dict[str, Any] = {}
    equation_provenance: dict[str, list[dict[str, Any]]] = {}
    residual_entry_cache: dict[
        str, list[tuple[str | None, int, int]]
    ] = {}
    path_residual_evaluation_count = 0
    evaluated_relation_ids: list[str] = []

    def evaluate_relation(relation: dict[str, Any]) -> list[Any]:
        nonlocal path_residual_evaluation_count
        new_equations: list[Any] = []
        if relation["family"] == "EQ112_PATH_CONSISTENCY":
            residual_key = stable_hash(
                {
                    "kind": "PATH",
                    "lhs": relation["lhs_word"],
                    "rhs": relation["rhs_word"],
                }
            )
            def residual_builder() -> Any:
                return word_product(
                    relation["lhs_word"]
                ) - word_product(relation["rhs_word"])
        else:
            residual_key = stable_hash(
                {
                    "kind": "LINEAR_EXPRESSION",
                    "terms": relation["expression"],
                }
            )
            def residual_builder() -> Any:
                return expression(relation["expression"])
        evaluated_relation_ids.append(relation["relation_id"])
        cached_entries = residual_entry_cache.get(residual_key)
        if cached_entries is not None:
            for key, row, column in cached_entries:
                if key is None:
                    continue
                equation_provenance[key].append(
                    {
                        "relation_id": relation["relation_id"],
                        "family": relation["family"],
                        "source_stage": int(relation["source_stage"]),
                        "matrix_entry": [row, column],
                    }
                )
            return new_equations

        residual = residual_builder()
        if relation["family"] == "EQ112_PATH_CONSISTENCY":
            path_residual_evaluation_count += 1
        entry_records: list[tuple[str | None, int, int]] = []
        for row in range(2):
            for column in range(2):
                entry = residual[row, column]
                numerator = ring(entry.numerator())
                denominator = ring(entry.denominator())
                if denominator != ring.one():
                    raw_required_factors.append(denominator)
                if numerator == 0:
                    entry_records.append((None, row, column))
                    continue
                normalised = _worker_normalise(numerator)
                key = str(normalised)
                if key not in unique_equations:
                    unique_equations[key] = normalised
                    new_equations.append(normalised)
                equation_provenance.setdefault(key, []).append(
                    {
                        "relation_id": relation["relation_id"],
                        "family": relation["family"],
                        "source_stage": int(relation["source_stage"]),
                        "matrix_entry": [row, column],
                    }
                )
                entry_records.append((key, row, column))
        residual_entry_cache[residual_key] = entry_records
        return new_equations

    def relation_cost(relation: dict[str, Any]) -> tuple[Any, ...]:
        family_rank = {
            "STRONG_OPERATOR_MSR": 0,
            "LOCAL_OPERATOR_GC": 1,
            "EQ112_PATH_CONSISTENCY": 2,
            "CPOBC": 3,
        }
        if relation["family"] == "EQ112_PATH_CONSISTENCY":
            term_count = 2
            word_length = len(relation["lhs_word"]) + len(
                relation["rhs_word"]
            )
        else:
            term_count = len(relation["expression"])
            word_length = sum(
                len(term["word"]) for term in relation["expression"]
            )
        return (
            int(relation["source_stage"]),
            family_rank.get(relation["family"], 9),
            word_length,
            term_count,
            relation["relation_id"],
        )

    initial_started = time.perf_counter()
    initial_groebner_trace: list[dict[str, Any]] = []
    equations_covered_by_initial_basis = 0
    ideal = ring.ideal([])
    initial_basis: Any = []
    numerator_initial_unit = False
    pre_stage4_saturation_trace: list[dict[str, Any]] = []
    pre_stage4_factor_records: list[dict[str, Any]] = []
    pre_stage4_factor_equivalence: dict[str, Any] = {}
    pre_stage4_factor_keys: set[str] = set()
    chart_factors_added = False
    strategy = payload["groebner_strategy"]
    if strategy == "progressive":
        ordered_relations = sorted(selected_relations, key=relation_cost)
        low_stage_relations = [
            relation
            for relation in ordered_relations
            if int(relation["source_stage"]) <= 3
        ]
        high_stage_relations = [
            relation
            for relation in ordered_relations
            if int(relation["source_stage"]) > 3
        ]
        relation_batches: list[list[dict[str, Any]]] = []
        if low_stage_relations:
            relation_batches.append(low_stage_relations)
        batch_size = max(1, int(payload["progressive_batch_size"]))
        relation_batches.extend(
            high_stage_relations[index : index + batch_size]
            for index in range(0, len(high_stage_relations), batch_size)
        )
        for batch_index, relation_batch in enumerate(relation_batches):
            batch_started = time.perf_counter()
            new_equations: list[Any] = []
            for relation in relation_batch:
                new_equations.extend(evaluate_relation(relation))
            if new_equations or not initial_basis:
                generators = (
                    list(initial_basis) + new_equations
                    if initial_basis
                    else new_equations
                )
                ideal = ring.ideal(generators)
                initial_basis = ideal.groebner_basis(
                    algorithm=payload["groebner_algorithm"]
                )
            equations_covered_by_initial_basis = len(unique_equations)
            unit = (
                len(initial_basis) == 1
                and initial_basis[0] == ring.one()
            )
            if batch_index == 0:
                numerator_initial_unit = unit
            trace_record = {
                    "strategy": "STREAMING_PROGRESSIVE",
                    "batch_index": batch_index,
                    "relations_added": len(relation_batch),
                    "new_equations_added": len(new_equations),
                    "total_relations_evaluated": len(
                        evaluated_relation_ids
                    ),
                    "total_equations_covered": (
                        equations_covered_by_initial_basis
                    ),
                    "minimum_source_stage": min(
                        int(relation["source_stage"])
                        for relation in relation_batch
                    ),
                    "maximum_source_stage": max(
                        int(relation["source_stage"])
                        for relation in relation_batch
                    ),
                    "families": sorted(
                        {
                            relation["family"]
                            for relation in relation_batch
                        }
                    ),
                    "wall_time_seconds": (
                        time.perf_counter() - batch_started
                    ),
                    "unit_ideal": unit,
                    "groebner_basis": _worker_basis_summary(
                        initial_basis
                    ),
                }
            initial_groebner_trace.append(trace_record)
            sys.stderr.write(
                "V035_PROGRESS "
                + _canonical_json(
                    {
                        "chart": payload["chart"],
                        **trace_record,
                    }
                )
                + "\n"
            )
            sys.stderr.flush()
            _worker_emit_progress(
                payload,
                {
                    "event": "GROEBNER_BATCH_COMPLETED",
                    "elapsed_seconds": time.perf_counter() - started,
                    **trace_record,
                },
            )

            # Localise the inexpensive stage<=3 subsystem before expanding
            # stage 4.  This is exact because
            # ((I:S^infinity)+J):S^infinity = (I+J):S^infinity.
            if (
                batch_index == 0
                and not unit
                and bool(payload["saturation"])
                and int(payload["maximum_source_stage"]) > 3
            ):
                raw_required_factors.extend(
                    ring(value.replace("**", "^"))
                    for value in payload["chart_nonzero_conditions"]
                )
                chart_factors_added = True
                (
                    pre_factors,
                    pre_stage4_factor_records,
                    pre_stage4_factor_equivalence,
                ) = _worker_factor_set(raw_required_factors)
                if payload.get("saturation_factor_order", "forward") == "reverse":
                    pre_factors.reverse()
                pre_zero = any(
                    record.get("status") == "ZERO_REQUIRED_FACTOR"
                    for record in pre_stage4_factor_records
                )
                if pre_zero:
                    ideal = ring.ideal([ring.one()])
                    initial_basis = [ring.one()]
                    unit = True
                    pre_stage4_saturation_trace.append(
                        {
                            "phase": "PRE_STAGE4_LOCALISATION",
                            "status": "UNIT_IDEAL_ZERO_REQUIRED_FACTOR",
                            "wall_time_seconds": 0.0,
                            "unit_ideal_after_step": True,
                            "groebner_basis": _worker_basis_summary(
                                initial_basis
                            ),
                        }
                    )
                else:
                    for factor_index, factor in enumerate(pre_factors):
                        factor_started = time.perf_counter()
                        ideal, _ = ideal.saturation(
                            ring.ideal([factor])
                        )
                        initial_basis = ideal.groebner_basis(
                            algorithm=payload["groebner_algorithm"]
                        )
                        unit = (
                            len(initial_basis) == 1
                            and initial_basis[0] == ring.one()
                        )
                        factor_key = str(factor)
                        pre_stage4_factor_keys.add(factor_key)
                        pre_stage4_saturation_trace.append(
                            {
                                "phase": "PRE_STAGE4_LOCALISATION",
                                "factor_index": factor_index,
                                "factor": factor_key,
                                "wall_time_seconds": (
                                    time.perf_counter()
                                    - factor_started
                                ),
                                "unit_ideal_after_step": unit,
                                "groebner_basis": (
                                    _worker_basis_summary(initial_basis)
                                ),
                            }
                        )
                        _worker_emit_progress(
                            payload,
                            {
                                "event": (
                                    "PRE_STAGE4_SATURATION_STEP_COMPLETED"
                                ),
                                "elapsed_seconds": (
                                    time.perf_counter() - started
                                ),
                                **pre_stage4_saturation_trace[-1],
                            },
                        )
                        if unit:
                            break
            if unit:
                break
    else:
        for relation in selected_relations:
            evaluate_relation(relation)
        equations = list(unique_equations.values())
        (
            ideal,
            initial_basis,
            _unused_initial_seconds,
            initial_groebner_trace,
            equations_covered_by_initial_basis,
        ) = _worker_initial_groebner(
            ring,
            equations,
            equation_provenance,
            algorithm=payload["groebner_algorithm"],
            strategy=strategy,
            progressive_batch_size=payload["progressive_batch_size"],
        )
    equations = list(unique_equations.values())
    initial_gb_seconds = time.perf_counter() - initial_started
    initial_unit = (
        len(initial_basis) == 1 and initial_basis[0] == ring.one()
    )
    if not initial_groebner_trace:
        numerator_initial_unit = initial_unit

    # If a subset already generates 1, the full equation ideal and every
    # localisation of it are also the unit ideal.  Only nonunit cases need
    # the expensive transition-predicate reconstruction.
    transition_count = 0
    unique_transition_expression_count = 0
    if (
        not initial_unit
        and bool(payload["include_all_transition_predicates"])
    ):
        seen_transition_expressions: set[str] = set()
        for transition in direct_payload[
            "reconstructed_transition_predicates"
        ]:
            expression_digest = transition["expression_sha256"]
            if expression_digest in seen_transition_expressions:
                transition_count += 1
                continue
            seen_transition_expressions.add(expression_digest)
            unique_transition_expression_count += 1
            transition_matrix = expression(
                transition["reconstructed_expression"]
            )
            record_fraction_nonzero(
                transition_matrix.det(),
                origin=f"det({transition['occurrence_id']})",
                kind="RECONSTRUCTED_TRANSITION",
            )
            transition_count += 1

    if not initial_unit and not chart_factors_added:
        raw_required_factors.extend(
            ring(expression.replace("**", "^"))
            for expression in payload["chart_nonzero_conditions"]
        )
    if initial_unit:
        if pre_stage4_saturation_trace:
            saturation_factors = []
            factor_records = pre_stage4_factor_records
            factor_reduction_equivalence = (
                pre_stage4_factor_equivalence
            )
        else:
            saturation_factors = []
            factor_records = []
            factor_reduction_equivalence = {
                "performed": False,
                "reason": "NUMERATOR_SUBSET_ALREADY_GENERATES_UNIT_IDEAL",
                "deduplication_preserves_saturation": True,
            }
    elif payload["factor_denominators"]:
        (
            saturation_factors,
            factor_records,
            factor_reduction_equivalence,
        ) = _worker_factor_set(raw_required_factors)
        if payload.get("saturation_factor_order", "forward") == "reverse":
            saturation_factors.reverse()
    else:
        saturation_factors = [
            _worker_normalise(value) for value in raw_required_factors
        ]
        factor_records = [
            {
                "factor": str(value),
                "source_factor_indices": [index],
            }
            for index, value in enumerate(saturation_factors)
        ]
        factor_reduction_equivalence = {
            "performed": False,
            "reason": "factor_denominators=false",
        }
    zero_required_factor = any(
        record.get("status") == "ZERO_REQUIRED_FACTOR"
        for record in factor_records
    )
    saturated_ideal = ideal
    saturation_trace: list[dict[str, Any]] = list(
        pre_stage4_saturation_trace
    )
    current_unit = initial_unit
    if zero_required_factor:
        saturated_ideal = ring.ideal([ring.one()])
        current_unit = True
        saturation_trace.append(
            {
                "status": "UNIT_IDEAL_ZERO_REQUIRED_FACTOR",
                "wall_time_seconds": 0.0,
            }
        )
    elif bool(payload["saturation"]) and not initial_unit:
        for factor_index, factor in enumerate(saturation_factors):
            factor_started = time.perf_counter()
            saturated_ideal, _ = saturated_ideal.saturation(
                ring.ideal([factor])
            )
            saturated_basis = saturated_ideal.groebner_basis(
                algorithm=payload["groebner_algorithm"]
            )
            is_unit = (
                len(saturated_basis) == 1
                and saturated_basis[0] == ring.one()
            )
            current_unit = is_unit
            saturation_trace.append(
                {
                    "factor_index": factor_index,
                    "factor": str(factor),
                    "wall_time_seconds": (
                        time.perf_counter() - factor_started
                    ),
                    "unit_ideal_after_step": is_unit,
                    "groebner_basis": _worker_basis_summary(
                        saturated_basis
                    ),
                }
            )
            if is_unit:
                break

    noncommutativity_checks: list[dict[str, Any]] = []
    if (
        bool(payload["check_noncommutativity"])
        and bool(payload["saturation"])
        and not current_unit
    ):
        grouped_components: dict[str, dict[str, Any]] = {}
        for component in payload["commutator_components"]:
            polynomial = ring(component["expression"].replace("**", "^"))
            if polynomial == 0:
                continue
            polynomial = _worker_normalise(polynomial)
            key = str(polynomial)
            group = grouped_components.setdefault(
                key,
                {
                    "polynomial": polynomial,
                    "components": [],
                },
            )
            group["components"].append(component)
        for key, group in grouped_components.items():
            polynomial = group["polynomial"]
            component_started = time.perf_counter()
            component_ideal, _ = saturated_ideal.saturation(
                ring.ideal([polynomial])
            )
            component_basis = component_ideal.groebner_basis(
                algorithm=payload["groebner_algorithm"]
            )
            unit_ideal = (
                len(component_basis) == 1
                and component_basis[0] == ring.one()
            )
            noncommutativity_checks.append(
                {
                    **group["components"][0],
                    "covered_components": group["components"],
                    "covered_component_count": len(
                        group["components"]
                    ),
                    "normalised_expression": key,
                    "wall_time_seconds": (
                        time.perf_counter() - component_started
                    ),
                    "unit_ideal": unit_ideal,
                    "groebner_basis": _worker_basis_summary(
                        component_basis
                    ),
                    "dimension": (
                        None
                        if unit_ideal
                        else int(component_ideal.dimension())
                    ),
                }
            )

    saturated_unit = current_unit
    surviving_noncommutative = [
        record
        for record in noncommutativity_checks
        if not record["unit_ideal"]
    ]
    covered_commutator_component_count = sum(
        int(record.get("covered_component_count", 1))
        for record in noncommutativity_checks
    )
    final_localisation_complete = bool(payload["saturation"]) and (
        saturated_unit
        or len(
            [
                record
                for record in saturation_trace
                if record.get("phase") != "PRE_STAGE4_LOCALISATION"
            ]
        )
        == len(saturation_factors)
    )
    commutator_coverage_complete = (
        saturated_unit
        or not payload["commutator_components"]
        or covered_commutator_component_count
        == len(payload["commutator_components"])
    )
    peak_rss_bytes = (
        resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    )
    memory_budget_satisfied = (
        payload.get("memory_limit_bytes") is None
        or peak_rss_bytes <= int(payload["memory_limit_bytes"])
    )
    evaluated_relation_ids_sha256 = stable_hash(
        evaluated_relation_ids
    )
    expected_evaluated_relation_digest = payload.get(
        "expected_evaluated_relation_ids_sha256"
    )
    expected_transition_count = payload.get(
        "expected_reconstructed_transition_count"
    )
    canonical_selection_checks_passed = bool(
        payload.get("canonical_ideal_equivalence_certified", False)
    ) or not payload.get("selection_certificate")
    proof_eligible = (
        modulus == 0
        and bool(payload["saturation"])
        and payload["operation"] == "solve"
        and not selection_errors
        and canonical_selection_checks_passed
        and final_localisation_complete
        and commutator_coverage_complete
        and memory_budget_satisfied
    )
    identity_proof_eligible = (
        modulus == 0
        and payload["operation"] == "compile"
        and payload["groebner_strategy"] == "none"
        and not bool(payload["saturation"])
        and not bool(payload["check_noncommutativity"])
        and not selection_errors
        and payload.get("expected_selected_relation_count") is not None
        and len(selected_relations)
        == int(payload["expected_selected_relation_count"])
        and payload.get("expected_selected_relation_ids_sha256")
        is not None
        and selected_relation_ids_sha256
        == payload["expected_selected_relation_ids_sha256"]
        and expected_evaluated_relation_digest is not None
        and evaluated_relation_ids_sha256
        == expected_evaluated_relation_digest
        and len(evaluated_relation_ids) == len(selected_relations)
        and not equations
        and bool(payload["include_all_transition_predicates"])
        and expected_transition_count is not None
        and transition_count == int(expected_transition_count)
        and not zero_required_factor
        and factor_reduction_equivalence.get(
            "all_source_factorisations_reconstructed_exactly"
        )
        is True
        and isinstance(expected_direct_file_sha256, str)
        and direct_system_file_sha256 == expected_direct_file_sha256
        and isinstance(expected_direct_semantic_digest, str)
        and direct_system_semantic_digest_sha256
        == expected_direct_semantic_digest
        and direct_system_self_semantic_digest_valid
        and memory_budget_satisfied
    )
    result: dict[str, Any] = {
        "schema_version": payload.get(
            "response_schema_version",
            LEGACY_RESPONSE_SCHEMA,
        ),
        "chart": payload["chart"],
        "stratum": payload["stratum"],
        "source_index_branch": payload["source_index_branch"],
        "equation_source_index_branch": payload.get(
            "equation_source_index_branch",
            payload["source_index_branch"],
        ),
        "chart_source_index_branch": payload.get(
            "chart_source_index_branch",
            payload["source_index_branch"],
        ),
        "chart_cover_id": payload.get("chart_cover_id", payload["chart"]),
        "selection_label": payload.get(
            "selection_label", "ALL_RELATIONS"
        ),
        "selection_certificate": payload.get("selection_certificate"),
        "selection_certificate_semantic_digest_sha256": payload.get(
            "selection_certificate_semantic_digest_sha256"
        ),
        "budget_file": payload.get("budget_file"),
        "budget_file_sha256": payload.get("budget_file_sha256"),
        "request_semantic_digest_sha256": request_semantic_digest,
        "direct_system_path": payload["direct_system_path"],
        "direct_system_file_sha256": direct_system_file_sha256,
        "direct_system_semantic_digest_sha256": (
            direct_system_semantic_digest_sha256
        ),
        "direct_system_self_semantic_digest_valid": (
            direct_system_self_semantic_digest_valid
        ),
        "semantic_profile": direct_payload["semantic_profile"],
        "coefficient_field": "QQ" if modulus == 0 else f"GF({modulus})",
        "coefficient_modulus": modulus,
        "backend": "Sage fraction field / embedded Singular ideals",
        "backend_versions": _worker_versions(),
        "groebner_algorithm": payload["groebner_algorithm"],
        "groebner_strategy": payload["groebner_strategy"],
        "progressive_batch_size": payload["progressive_batch_size"],
        "saturation_factor_order": payload.get(
            "saturation_factor_order", "forward"
        ),
        "expression_source": "DIRECT_REDUCED_OPERATOR_WORDS",
        "operation": payload["operation"],
        "maximum_source_stage": payload["maximum_source_stage"],
        "all_transition_predicates_requested": bool(
            payload["include_all_transition_predicates"]
        ),
        "check_noncommutativity_requested": bool(
            payload["check_noncommutativity"]
        ),
        "variable_count": len(variable_names),
        "variables": list(variable_names),
        "selected_relation_count": len(selected_relations),
        "selected_matrix_relation_count": len(selected_relations),
        "selected_relation_ids_sha256": selected_relation_ids_sha256,
        "selected_relation_family_counts": (
            selected_relation_family_counts
        ),
        "included_relation_families": sorted(
            included_relation_families
        ),
        "forbidden_relation_families": sorted(
            forbidden_relation_families
        ),
        "relation_selection_checks_passed": not selection_errors,
        "selected_canonical_equation_count": payload.get(
            "expected_selected_canonical_equation_count"
        ),
        "selected_equation_ids_sha256": payload.get(
            "expected_selected_equation_ids_sha256"
        ),
        "selected_expression_ids_sha256": payload.get(
            "expected_selected_expression_ids_sha256"
        ),
        "canonical_selection_checks_passed": (
            canonical_selection_checks_passed
        ),
        "certified_frozen_denominator_factor_count": payload.get(
            "expected_frozen_denominator_factor_count"
        ),
        "selected_denominator_record_count": payload.get(
            "expected_frozen_denominator_factor_count"
        ),
        "denominator_evaluation_route": (
            "DIRECT_INVERSE_AND_TRANSITION_RECONSTRUCTION"
        ),
        "relations_evaluated_count": len(evaluated_relation_ids),
        "evaluated_relation_ids_sha256": (
            evaluated_relation_ids_sha256
        ),
        "nonzero_specialised_equation_count": len(equations),
        "equation_provenance_digest_sha256": stable_hash(
            equation_provenance
        ),
        "equation_complexity_inventory": (
            [
                {
                    "polynomial_sha256": stable_hash(key),
                    "degree": int(polynomial.degree()),
                    "term_count": len(polynomial.monomials()),
                    "character_count": len(key),
                    "minimum_source_stage": min(
                        int(record["source_stage"])
                        for record in equation_provenance[key]
                    ),
                    "provenance": equation_provenance[key],
                }
                for key, polynomial in sorted(
                    unique_equations.items(),
                    key=lambda item: (
                        int(item[1].degree()),
                        len(item[1].monomials()),
                        item[0],
                    ),
                )
            ]
            if payload["groebner_strategy"] == "none"
            else []
        ),
        "dependency_nodes_evaluated": len(matrix_cache),
        "word_products_evaluated": word_product_evaluation_count,
        "cached_q_word_product_count": len(word_product_cache),
        "linear_expressions_evaluated": expression_evaluation_count,
        "path_residuals_evaluated": path_residual_evaluation_count,
        "unique_relation_residual_count": len(residual_entry_cache),
        "reconstructed_transitions_checked": transition_count,
        "unique_reconstructed_transition_expression_count": (
            unique_transition_expression_count
        ),
        "reconstructed_transition_predicates_vacuous_due_to_unit_numerator": (
            numerator_initial_unit
            and transition_count == 0
            and bool(payload["include_all_transition_predicates"])
        ),
        "reconstructed_transition_predicates_vacuous_due_to_unit_localised_subset": (
            initial_unit
            and transition_count == 0
            and bool(payload["include_all_transition_predicates"])
        ),
        "raw_required_factor_count": len(raw_required_factors),
        "effective_saturation_factor_count": len(saturation_factors),
        "factor_reduction_records": factor_records,
        "factor_reduction_equivalence": factor_reduction_equivalence,
        "inverse_factor_records": inverse_factor_records,
        "zero_required_factor": zero_required_factor,
        "initial_groebner_seconds": initial_gb_seconds,
        "initial_groebner_trace": initial_groebner_trace,
        "equations_covered_by_initial_basis": (
            equations_covered_by_initial_basis
        ),
        "unit_subset_certificate": (
            initial_unit
            and len(evaluated_relation_ids) < len(selected_relations)
        ),
        "pre_stage4_localisation_performed": bool(
            pre_stage4_saturation_trace
        ),
        "pre_stage4_localisation_unit_ideal": (
            bool(pre_stage4_saturation_trace) and initial_unit
        ),
        "final_resaturates_pre_stage4_factors": True,
        "initial_groebner_basis": _worker_basis_summary(initial_basis),
        "initial_unit_ideal": numerator_initial_unit,
        "saturation_requested": bool(payload["saturation"]),
        "saturation_method": (
            "SEQUENTIAL_SAGE_NATIVE_IDEAL_SATURATION_ON_SUBSYSTEM"
            if pre_stage4_saturation_trace
            else (
                "NOT_NEEDED_NUMERATOR_IDEAL_ALREADY_UNIT"
                if initial_unit
                else (
                    "SEQUENTIAL_SAGE_NATIVE_IDEAL_SATURATION"
                    if payload["saturation"]
                    else "NOT_REQUESTED"
                )
            )
        ),
        "saturation_trace": saturation_trace,
        "saturated_unit_ideal": saturated_unit,
        "final_localisation_complete": final_localisation_complete,
        "commutator_component_count": len(
            payload["commutator_components"]
        ),
        "covered_commutator_component_count": (
            covered_commutator_component_count
        ),
        "commutator_coverage_complete": commutator_coverage_complete,
        "noncommutativity_checks": noncommutativity_checks,
        "surviving_noncommutative_component_count": len(
            surviving_noncommutative
        ),
        "proof_eligible": proof_eligible,
        "identity_proof_eligible": identity_proof_eligible,
        "resource_usage": {
            "wall_time_seconds": time.perf_counter() - started,
            "peak_rss_bytes": peak_rss_bytes,
            "memory_limit": memory_limit,
            "memory_budget_satisfied": memory_budget_satisfied,
        },
        "exit_status": "COMPLETED",
    }
    if payload["groebner_strategy"] == "none":
        result["chart_verdict"] = "SPECIALISATION_ONLY_NO_IDEAL_SOLVE"
    elif saturated_unit:
        result["chart_verdict"] = "EXACT_EMPTY_CHART"
    elif (
        bool(payload["check_noncommutativity"])
        and bool(payload["saturation"])
        and not payload["commutator_components"]
    ):
        result["chart_verdict"] = (
            "EXACT_NO_NONCOMMUTATIVE_SOLUTION_IN_CHART"
        )
    elif noncommutativity_checks and not surviving_noncommutative:
        result["chart_verdict"] = (
            "EXACT_NO_NONCOMMUTATIVE_SOLUTION_IN_CHART"
        )
    elif surviving_noncommutative:
        result["chart_verdict"] = (
            "EXACT_NONCOMMUTATIVE_COMPONENT_SURVIVES"
        )
    else:
        result["chart_verdict"] = "EXACT_CHART_NONEMPTY_NONCOMM_UNCHECKED"
    result["semantic_digest_sha256"] = _result_semantic_digest(
        result,
        selection_fields=(
            "selection_label",
            "selected_relation_ids_sha256",
            "selected_equation_ids_sha256",
        ),
    )
    return result


def _worker_execute(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("expression_source") == "direct_operator":
        return _worker_execute_direct(payload)

    # Imports are local so the host Python does not require Sage.
    import resource

    from sage.all import GF, QQ, PolynomialRing  # type: ignore[import-not-found]

    started = time.perf_counter()
    memory_limit = _worker_apply_memory_limit(payload, resource)
    request_semantic_digest = _validated_request_semantic_digest(payload)
    modulus = int(payload["coefficient_modulus"])
    coefficient_field = QQ if modulus == 0 else GF(modulus)
    variable_names = tuple(payload["variables"])
    if not variable_names:
        raise ValueError("chart has no polynomial variables")
    ring = PolynomialRing(
        coefficient_field,
        names=variable_names,
        order="degrevlex",
    )
    substitutions = {
        name: ring(expression.replace("**", "^"))
        for name, expression in payload["q_substitutions"].items()
    }

    root = SAGE_CONTAINER_ROOT
    compact_arena_path = root / payload["compact_arena_path"]
    if not compact_arena_path.is_file():
        raise FileNotFoundError(
            f"v0.3.5 compact solver arena is missing: {compact_arena_path}"
        )
    with gzip.open(compact_arena_path, "rt", encoding="utf-8") as handle:
        arena_payload = json.load(handle)
    system_payload = json.loads(
        (root / payload["system_path"]).read_text(encoding="utf-8")
    )
    compact_nodes = arena_payload["nodes"]
    target_indices = arena_payload["target_indices"]
    cache: dict[int, Any] = {}

    def evaluate_index(expression_index: int) -> Any:
        existing = cache.get(expression_index)
        if existing is not None:
            return existing
        node = compact_nodes[expression_index]
        operation = int(node[0])
        if operation == 0:
            value = ring(node[1])
        elif operation == 1:
            value = substitutions[node[1]]
        elif operation == 2:
            value = ring.zero()
            for child in node[1]:
                value += evaluate_index(int(child))
        elif operation == 3:
            value = ring.one()
            counts = Counter(int(child) for child in node[1])
            for child, multiplicity in counts.items():
                value *= evaluate_index(child) ** multiplicity
        else:
            raise ValueError(f"unsupported arena operation: {operation}")
        cache[expression_index] = value
        return value

    def evaluate(expression_id: str) -> Any:
        return evaluate_index(int(target_indices[expression_id]))

    branch_system = system_payload["systems"][payload["source_index_branch"]]
    stage_selected_equations = [
        record
        for record in branch_system["equations"]
        if int(record["maximum_source_stage"])
        <= int(payload["maximum_source_stage"])
    ]
    excluded_equation_ids = {
        str(value) for value in payload.get("excluded_equation_ids", [])
    }
    available_equation_ids = {
        record["equation_id"] for record in stage_selected_equations
    }
    unknown_excluded_equation_ids = sorted(
        excluded_equation_ids - available_equation_ids
    )
    selected_equations = [
        record
        for record in stage_selected_equations
        if record["equation_id"] not in excluded_equation_ids
    ]
    selected_equation_ids = sorted(
        record["equation_id"] for record in selected_equations
    )
    selected_expression_ids = sorted(
        record["canonical_expression_id"] for record in selected_equations
    )
    selected_relation_families: dict[str, str] = {}
    for record in selected_equations:
        for provenance in record["provenance"]:
            relation_id = provenance["relation_id"]
            family = provenance["family"]
            existing_family = selected_relation_families.setdefault(
                relation_id,
                family,
            )
            if existing_family != family:
                raise RuntimeError(
                    f"relation family mismatch for {relation_id}: "
                    f"{existing_family} != {family}"
                )
    selected_relation_family_counts = dict(
        sorted(Counter(selected_relation_families.values()).items())
    )
    selected_provenance_families = sorted(
        set(selected_relation_families.values())
    )
    forbidden_provenance_families = {
        str(value)
        for value in payload.get("forbidden_provenance_families", [])
    }
    selected_equation_ids_sha256 = stable_hash(selected_equation_ids)
    selected_expression_ids_sha256 = stable_hash(selected_expression_ids)
    selection_errors: list[str] = []
    if unknown_excluded_equation_ids:
        selection_errors.append("unknown excluded equation IDs")
    expected_equation_count = payload.get(
        "expected_selected_canonical_equation_count"
    )
    if (
        expected_equation_count is not None
        and len(selected_equations) != int(expected_equation_count)
    ):
        selection_errors.append(
            "selected canonical equation count does not match expectation"
        )
    expected_excluded_count = payload.get("expected_excluded_equation_count")
    if (
        expected_excluded_count is not None
        and len(excluded_equation_ids) != int(expected_excluded_count)
    ):
        selection_errors.append(
            "excluded canonical equation count does not match expectation"
        )
    expected_relation_count = payload.get("expected_selected_relation_count")
    if (
        expected_relation_count is not None
        and len(selected_relation_families) != int(expected_relation_count)
    ):
        selection_errors.append(
            "selected matrix relation count does not match expectation"
        )
    expected_family_counts = payload.get("expected_relation_family_counts")
    if (
        expected_family_counts is not None
        and selected_relation_family_counts
        != {
            str(name): int(count)
            for name, count in expected_family_counts.items()
        }
    ):
        selection_errors.append(
            "selected relation-family counts do not match expectation"
        )
    if forbidden_provenance_families.intersection(
        selected_provenance_families
    ):
        selection_errors.append("forbidden provenance family selected")
    expected_equation_digest = payload.get(
        "expected_selected_equation_ids_sha256"
    )
    if (
        expected_equation_digest is not None
        and selected_equation_ids_sha256 != expected_equation_digest
    ):
        selection_errors.append("selected equation-ID digest mismatch")
    expected_expression_digest = payload.get(
        "expected_selected_expression_ids_sha256"
    )
    if (
        expected_expression_digest is not None
        and selected_expression_ids_sha256 != expected_expression_digest
    ):
        selection_errors.append("selected expression-ID digest mismatch")
    if selection_errors:
        raise RuntimeError(
            "canonical equation selection failed: "
            + _canonical_json(
                {
                    "errors": selection_errors,
                    "unknown_excluded_equation_ids": (
                        unknown_excluded_equation_ids
                    ),
                    "selected_equation_count": len(selected_equations),
                    "selected_relation_count": len(
                        selected_relation_families
                    ),
                    "selected_relation_family_counts": (
                        selected_relation_family_counts
                    ),
                    "selected_provenance_families": (
                        selected_provenance_families
                    ),
                    "selected_equation_ids_sha256": (
                        selected_equation_ids_sha256
                    ),
                    "selected_expression_ids_sha256": (
                        selected_expression_ids_sha256
                    ),
                }
            )
        )
    unique_equations: dict[str, Any] = {}
    equation_provenance: dict[str, list[dict[str, Any]]] = {}
    zero_specialised_equation_count = 0
    nonzero_specialised_canonical_equation_count = 0
    for record in selected_equations:
        polynomial = evaluate(record["canonical_expression_id"])
        if polynomial == 0:
            zero_specialised_equation_count += 1
            continue
        nonzero_specialised_canonical_equation_count += 1
        normalised = _worker_normalise(polynomial)
        key = str(normalised)
        unique_equations.setdefault(key, normalised)
        equation_provenance.setdefault(key, []).append(
            {
                "equation_id": record["equation_id"],
                "source_stage": int(record["minimum_source_stage"]),
            }
        )
    equations = list(unique_equations.values())

    selected_denominator_records = [
        record
        for record in system_payload["denominator_factors"]
        if int(record["stage"]) <= int(payload["maximum_source_stage"])
    ]
    raw_required_factors = [
        evaluate(record["factor_id"])
        for record in selected_denominator_records
    ]
    raw_required_factors.extend(
        ring(expression.replace("**", "^"))
        for expression in payload["chart_nonzero_conditions"]
    )
    if payload["factor_denominators"]:
        (
            saturation_factors,
            factor_records,
            factor_reduction_equivalence,
        ) = _worker_factor_set(
            raw_required_factors
        )
        if payload.get("saturation_factor_order", "forward") == "reverse":
            saturation_factors.reverse()
    else:
        saturation_factors = [
            _worker_normalise(value) for value in raw_required_factors
        ]
        factor_records = [
            {
                "factor": str(value),
                "source_factor_indices": [index],
            }
            for index, value in enumerate(saturation_factors)
        ]
        factor_reduction_equivalence = {
            "performed": False,
            "reason": "factor_denominators=false",
        }

    zero_required_factor = any(
        record.get("status") == "ZERO_REQUIRED_FACTOR"
        for record in factor_records
    )
    (
        ideal,
        initial_basis,
        initial_gb_seconds,
        initial_groebner_trace,
        equations_covered_by_initial_basis,
    ) = _worker_initial_groebner(
        ring,
        equations,
        equation_provenance,
        algorithm=payload["groebner_algorithm"],
        strategy=payload["groebner_strategy"],
        progressive_batch_size=payload["progressive_batch_size"],
    )
    initial_unit = (
        len(initial_basis) == 1 and initial_basis[0] == ring.one()
    )

    saturation_trace: list[dict[str, Any]] = []
    saturated_ideal = ideal
    current_unit = initial_unit
    if zero_required_factor:
        saturated_ideal = ring.ideal([ring.one()])
        current_unit = True
        saturation_trace.append(
            {
                "status": "UNIT_IDEAL_ZERO_REQUIRED_FACTOR",
                "factor": "0",
                "wall_time_seconds": 0.0,
            }
        )
    elif bool(payload["saturation"]) and not initial_unit:
        for factor_index, factor in enumerate(saturation_factors):
            factor_started = time.perf_counter()
            saturated_ideal, _ = saturated_ideal.saturation(
                ring.ideal([factor])
            )
            saturated_basis = saturated_ideal.groebner_basis(
                algorithm=payload["groebner_algorithm"]
            )
            saturated_is_one = (
                len(saturated_basis) == 1
                and saturated_basis[0] == ring.one()
            )
            current_unit = saturated_is_one
            saturation_trace.append(
                {
                    "factor_index": factor_index,
                    "factor": str(factor),
                    "wall_time_seconds": time.perf_counter() - factor_started,
                    "unit_ideal_after_step": saturated_is_one,
                    "groebner_basis": _worker_basis_summary(
                        saturated_basis
                    ),
                }
            )
            if saturated_is_one:
                break

    noncommutativity_checks: list[dict[str, Any]] = []
    if (
        bool(payload["check_noncommutativity"])
        and bool(payload["saturation"])
        and not current_unit
    ):
        grouped_components: dict[str, dict[str, Any]] = {}
        for component in payload["commutator_components"]:
            polynomial = ring(component["expression"].replace("**", "^"))
            if polynomial == 0:
                continue
            polynomial = _worker_normalise(polynomial)
            component_key = str(polynomial)
            group = grouped_components.setdefault(
                component_key,
                {
                    "polynomial": polynomial,
                    "components": [],
                },
            )
            group["components"].append(component)
        for component_key, group in grouped_components.items():
            polynomial = group["polynomial"]
            component_started = time.perf_counter()
            component_ideal, _ = saturated_ideal.saturation(
                ring.ideal([polynomial])
            )
            component_basis = component_ideal.groebner_basis(
                algorithm=payload["groebner_algorithm"]
            )
            component_is_one = (
                len(component_basis) == 1
                and component_basis[0] == ring.one()
            )
            noncommutativity_checks.append(
                {
                    **group["components"][0],
                    "covered_components": group["components"],
                    "covered_component_count": len(
                        group["components"]
                    ),
                    "normalised_expression": component_key,
                    "wall_time_seconds": (
                        time.perf_counter() - component_started
                    ),
                    "unit_ideal": component_is_one,
                    "groebner_basis": _worker_basis_summary(
                        component_basis
                    ),
                    "dimension": (
                        None
                        if component_is_one
                        else int(component_ideal.dimension())
                    ),
                }
            )

    saturated_unit = current_unit
    surviving_noncommutative = [
        record
        for record in noncommutativity_checks
        if not record["unit_ideal"]
    ]
    covered_commutator_component_count = sum(
        int(record.get("covered_component_count", 1))
        for record in noncommutativity_checks
    )
    final_localisation_complete = bool(payload["saturation"]) and (
        saturated_unit
        or len(saturation_trace) == len(saturation_factors)
    )
    commutator_coverage_complete = (
        saturated_unit
        or not payload["commutator_components"]
        or covered_commutator_component_count
        == len(payload["commutator_components"])
    )
    preliminary_proof_eligible = (
        modulus == 0
        and bool(payload["saturation"])
        and payload["operation"] == "solve"
        and final_localisation_complete
        and commutator_coverage_complete
    )
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    memory_budget_satisfied = (
        payload.get("memory_limit_bytes") is None
        or peak_rss <= int(payload["memory_limit_bytes"])
    )
    proof_eligible = (
        preliminary_proof_eligible and memory_budget_satisfied
    )
    result: dict[str, Any] = {
        "schema_version": payload.get(
            "response_schema_version",
            LEGACY_RESPONSE_SCHEMA,
        ),
        "chart": payload["chart"],
        "stratum": payload["stratum"],
        "source_index_branch": payload["source_index_branch"],
        "equation_source_index_branch": payload.get(
            "equation_source_index_branch",
            payload["source_index_branch"],
        ),
        "chart_source_index_branch": payload.get(
            "chart_source_index_branch",
            payload["source_index_branch"],
        ),
        "chart_cover_id": payload.get("chart_cover_id", payload["chart"]),
        "selection_label": payload.get("selection_label", "ALL_EQUATIONS"),
        "selection_certificate": payload.get("selection_certificate"),
        "budget_file": payload.get("budget_file"),
        "budget_file_sha256": payload.get("budget_file_sha256"),
        "request_semantic_digest_sha256": request_semantic_digest,
        "expression_source": "FROZEN_COMPACT_EXPRESSION_ARENA",
        "coefficient_field": "QQ" if modulus == 0 else f"GF({modulus})",
        "coefficient_modulus": modulus,
        "backend": "Sage polynomial ideals / embedded Singular",
        "backend_versions": _worker_versions(),
        "groebner_algorithm": payload["groebner_algorithm"],
        "groebner_strategy": payload["groebner_strategy"],
        "progressive_batch_size": payload["progressive_batch_size"],
        "saturation_factor_order": payload.get(
            "saturation_factor_order", "forward"
        ),
        "operation": payload["operation"],
        "maximum_source_stage": payload["maximum_source_stage"],
        "variable_count": len(variable_names),
        "variables": list(variable_names),
        "selected_canonical_equation_count": len(selected_equations),
        "excluded_canonical_equation_count": len(excluded_equation_ids),
        "selected_equation_ids_sha256": selected_equation_ids_sha256,
        "selected_expression_ids_sha256": selected_expression_ids_sha256,
        "selected_matrix_relation_count": len(selected_relation_families),
        "selected_relation_family_counts": selected_relation_family_counts,
        "selected_provenance_families": selected_provenance_families,
        "forbidden_provenance_families": sorted(
            forbidden_provenance_families
        ),
        "canonical_selection_checks_passed": not selection_errors,
        "nonzero_specialised_equation_count": len(equations),
        "nonzero_specialised_canonical_equation_count": (
            nonzero_specialised_canonical_equation_count
        ),
        "zero_specialised_equation_count": zero_specialised_equation_count,
        "equation_deduplication_count": (
            nonzero_specialised_canonical_equation_count - len(equations)
        ),
        "arena_nodes_evaluated": len(cache),
        "raw_required_factor_count": len(raw_required_factors),
        "selected_denominator_record_count": len(
            selected_denominator_records
        ),
        "effective_saturation_factor_count": len(saturation_factors),
        "factor_reduction_records": factor_records,
        "factor_reduction_equivalence": factor_reduction_equivalence,
        "zero_required_factor": zero_required_factor,
        "initial_groebner_seconds": initial_gb_seconds,
        "initial_groebner_trace": initial_groebner_trace,
        "equations_covered_by_initial_basis": (
            equations_covered_by_initial_basis
        ),
        "initial_groebner_basis": _worker_basis_summary(initial_basis),
        "initial_unit_ideal": initial_unit,
        "saturation_requested": bool(payload["saturation"]),
        "saturation_method": (
            "SEQUENTIAL_SAGE_NATIVE_IDEAL_SATURATION"
            if payload["saturation"]
            else "NOT_REQUESTED"
        ),
        "saturation_trace": saturation_trace,
        "saturated_unit_ideal": saturated_unit,
        "final_localisation_complete": final_localisation_complete,
        "commutator_component_count": len(
            payload["commutator_components"]
        ),
        "covered_commutator_component_count": (
            covered_commutator_component_count
        ),
        "commutator_coverage_complete": commutator_coverage_complete,
        "noncommutativity_checks": noncommutativity_checks,
        "surviving_noncommutative_component_count": len(
            surviving_noncommutative
        ),
        "proof_eligible": proof_eligible,
        "resource_usage": {
            "wall_time_seconds": time.perf_counter() - started,
            "peak_rss_bytes": peak_rss,
            "memory_limit": memory_limit,
            "memory_budget_satisfied": memory_budget_satisfied,
        },
        "exit_status": "COMPLETED",
    }
    if payload["groebner_strategy"] == "none":
        result["chart_verdict"] = "SPECIALISATION_ONLY_NO_IDEAL_SOLVE"
    elif saturated_unit:
        result["chart_verdict"] = "EXACT_EMPTY_CHART"
    elif (
        bool(payload["check_noncommutativity"])
        and bool(payload["saturation"])
        and not payload["commutator_components"]
    ):
        result["chart_verdict"] = (
            "EXACT_NO_NONCOMMUTATIVE_SOLUTION_IN_CHART"
        )
    elif noncommutativity_checks and not surviving_noncommutative:
        result["chart_verdict"] = (
            "EXACT_NO_NONCOMMUTATIVE_SOLUTION_IN_CHART"
        )
    elif surviving_noncommutative:
        result["chart_verdict"] = (
            "EXACT_NONCOMMUTATIVE_COMPONENT_SURVIVES"
        )
    else:
        result["chart_verdict"] = "EXACT_CHART_NONEMPTY_NONCOMM_UNCHECKED"
    result["semantic_digest_sha256"] = _result_semantic_digest(
        result,
        selection_fields=(
            "selection_label",
            "selected_equation_ids_sha256",
            "selected_expression_ids_sha256",
        ),
    )
    return result


def _worker_main() -> int:
    payload = json.loads(sys.stdin.read())
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        result = _worker_execute(payload)
    backend_log = captured.getvalue()
    if backend_log:
        result["backend_log"] = backend_log[-8000:]
    sys.stdout.write(_canonical_json(result))
    return 0


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--request-id")
    parser.add_argument("--source-index-branch")
    parser.add_argument("--chart")
    parser.add_argument("--coefficient-modulus", type=int, default=0)
    parser.add_argument("--operation", default="solve")
    parser.add_argument("--maximum-source-stage", type=int, default=4)
    parser.add_argument("--saturation", action="store_true")
    parser.add_argument("--check-noncommutativity", action="store_true")
    parser.add_argument("--no-factor-denominators", action="store_true")
    parser.add_argument("--no-all-transition-predicates", action="store_true")
    parser.add_argument(
        "--groebner-algorithm",
        default="libsingular:slimgb",
    )
    parser.add_argument(
        "--groebner-strategy",
        choices=("none", "progressive", "one_shot"),
        default="progressive",
    )
    parser.add_argument("--progressive-batch-size", type=int, default=4)
    parser.add_argument(
        "--saturation-factor-order",
        choices=("forward", "reverse"),
        default="forward",
    )
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _argument_parser().parse_args(argv)
    if arguments.worker:
        return _worker_main()
    if not arguments.source_index_branch or not arguments.chart:
        raise SystemExit(
            "--source-index-branch and --chart are required on the host"
        )
    payload = build_chart_payload(
        arguments.source_index_branch,
        arguments.chart,
        coefficient_modulus=arguments.coefficient_modulus,
        operation=arguments.operation,
        maximum_source_stage=arguments.maximum_source_stage,
        saturation=arguments.saturation,
        check_noncommutativity=arguments.check_noncommutativity,
        factor_denominators=not arguments.no_factor_denominators,
        include_all_transition_predicates=(
            not arguments.no_all_transition_predicates
        ),
        groebner_algorithm=arguments.groebner_algorithm,
        groebner_strategy=arguments.groebner_strategy,
        progressive_batch_size=arguments.progressive_batch_size,
        saturation_factor_order=arguments.saturation_factor_order,
    )
    result = run_sage_request(
        Path.cwd(),
        payload,
        timeout_seconds=arguments.timeout_seconds,
    )
    encoded = json.dumps(
        result,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    if arguments.output:
        output_path = Path(arguments.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            encoded,
            encoding="utf-8",
            newline="\n",
        )
    else:
        sys.stdout.write(encoded)
    return 0 if result.get("exit_status") == "COMPLETED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
