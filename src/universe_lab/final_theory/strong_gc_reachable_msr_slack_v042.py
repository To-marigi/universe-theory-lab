"""Static, fail-closed design record for the v0.4.2 955-side repair.

The frozen Q presentation is not a coordinate presentation for strong GC plus
reachable-state MSR: its implementation expands Eq. (108), which is an
operator-MSR elimination.  This module records the smaller *local* repair
which is valid at each source causet, while deliberately refusing to claim a
solver-ready global Q presentation.

For a source ``c`` let ``D_c = sum_t A_t - I`` and let ``v_c`` be its
path-independent reachable vector.  Under strong GC and nonsingularity,
``v_c != 0``.  The substitution

    T_c = I - sum_(t non-timid) A_t + N_c,
    N_c = u_c (J v_c)^T,   J = [[0, -1], [1, 0]],

therefore parameterises exactly the 2-by-2 matrices satisfying
``D_c v_c = 0``.  It adds two scalar parameters per source, hence 48 over 24
source causets.  It does *not* license the frozen implementations of Eq.
(107)/(108) or Eq. (112); their dependency trail is exposed in the returned
ledger.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

type Scalar = Fraction
type Vector = tuple[Scalar, Scalar]
type Matrix = tuple[tuple[Scalar, Scalar], tuple[Scalar, Scalar]]

SOURCE_RELATIONS_PATH = "results/v0.3.1_cpobc_relations_n4.json"
REDUCTION_PATH = "results/v0.3.2_cpobc_generator_reduction.json"
EQ112_PATH = "results/v0.3.3_eq112_reduction_n4.json"
DEPENDENCY_PATH = "results/v0.3.1_cpobc_dependency_graph.json"

VERDICT = "V042_955_LOCAL_SLACK_VALID_GLOBAL_COMPILER_PROVENANCE_REQUIRED"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sub(left: Matrix, right: Matrix) -> Matrix:
    return tuple(
        tuple(left[row][column] - right[row][column] for column in range(2)) for row in range(2)
    )  # type: ignore[return-value]


def _matvec(matrix: Matrix, vector: Vector) -> Vector:
    return tuple(
        sum(matrix[row][column] * vector[column] for column in range(2)) for row in range(2)
    )  # type: ignore[return-value]


def _zero_matrix() -> Matrix:
    zero = Fraction(0)
    return ((zero, zero), (zero, zero))


def slack_matrix(u: Vector, v: Vector) -> Matrix:
    """Return ``u (J v)^T`` using exact rational scalars.

    The formula is polynomial, so it needs no normalisation chart for the
    nonzero vector ``v``.
    """

    first, second = v
    return (
        (-u[0] * second, u[0] * first),
        (-u[1] * second, u[1] * first),
    )


def recover_slack_parameter(matrix: Matrix, v: Vector) -> Vector:
    """Recover the unique ``u`` when ``matrix v=0`` and ``v != 0``.

    This is the row-by-row proof algorithm for exhaustiveness.  It raises for
    a zero vector or a matrix outside the reachable-state kernel.
    """

    first, second = v
    if first == 0 and second == 0:
        raise ValueError("reachable vector must be nonzero")
    if _matvec(matrix, v) != (Fraction(0), Fraction(0)):
        raise ValueError("matrix does not annihilate the declared reachable vector")
    if first != 0:
        return (matrix[0][1] / first, matrix[1][1] / first)
    return (-matrix[0][0] / second, -matrix[1][0] / second)


def _semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    encoded = json.dumps(semantic, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def compile_strong_gc_reachable_msr_slack_v042(root: Path) -> dict[str, Any]:
    """Compile a static local-slack/provenance ledger, without solving it."""

    source_path = root / SOURCE_RELATIONS_PATH
    reduction_path = root / REDUCTION_PATH
    eq112_path = root / EQ112_PATH
    dependency_path = root / DEPENDENCY_PATH
    source = _load_json(source_path)
    reduction = _load_json(reduction_path)
    eq112 = _load_json(eq112_path)
    dependency = _load_json(dependency_path)

    constraints = source["MSR_operator_constraints"]
    source_ids = [str(record["source_id"]) for record in constraints]
    if len(source_ids) != len(set(source_ids)):
        raise AssertionError("one slack coordinate pair is required per unique source")
    if len(source_ids) != 24:
        raise AssertionError("the finite n<=4 source inventory must have 24 MSR sources")
    kind_counts: dict[str, int] = {}
    for record in reduction["reduction_map"]:
        kind = str(record["transition_kind"])
        kind_counts[kind] = kind_counts.get(kind, 0) + 1

    eq108_edge = {
        "from": "paper:eq108",
        "to": "axiom:MSR",
        "type": "MSR_ELIMINATION",
    }
    if eq108_edge not in dependency["edges"]:
        raise AssertionError("frozen dependency graph no longer records Eq.(108) MSR elimination")
    forward_dependencies = eq112["equivalence_obligations"]["forward"]["dependencies"]
    if "paper Eqs. (107), (108), (111), and (112)" not in forward_dependencies:
        raise AssertionError("Eq.(112) forward ledger changed; do not silently reuse it")

    slack_records = [
        {
            "source_id": source_id,
            "residual": f"D:{source_id}=sum_t A_t-I",
            "timid_definition": f"T:{source_id}=I-sum_non_timid(A)+N:{source_id}",
            "slack": f"N:{source_id}=u:{source_id}*(J*v:{source_id})^T",
            "new_scalar_parameters": [f"u:{source_id}:0", f"u:{source_id}:1"],
            "reachable_constraint": f"N:{source_id}*v:{source_id}=0",
        }
        for source_id in sorted(source_ids)
    ]
    payload: dict[str, Any] = {
        "schema_version": "final-theory-v0.4.2-955-local-slack-v1",
        "profile": "strong_GC__reachable_state_MSR",
        "identification_mode": "ON_QUOTIENT",
        "field_scope": "characteristic-zero field",
        "dimension": 2,
        "finite_scope": "n<=4",
        "source_artifacts": {
            SOURCE_RELATIONS_PATH: _sha256(source_path),
            REDUCTION_PATH: _sha256(reduction_path),
            EQ112_PATH: _sha256(eq112_path),
            DEPENDENCY_PATH: _sha256(dependency_path),
        },
        "local_parameterisation": {
            "J": [[0, -1], [1, 0]],
            "formula": "N_c=u_c*(J*v_c)^T",
            "residual_after_timid_substitution": "D_c=N_c",
            "proof": [
                "(Jv)^T v=-v_2 v_1+v_1 v_2=0, so every displayed N kills v.",
                "If v!=0 and Nv=0, each row r of N lies in the one-dimensional annihilator of v.",
                "That annihilator is span((Jv)^T), so the two row coefficients form a unique u.",
            ],
            "legacy_strong_MSR_slice": "u_c=(0,0) for every c, equivalently N_c=0",
        },
        "counts": {
            "source_causets": len(source_ids),
            "new_slack_vectors": len(source_ids),
            "new_scalar_parameters": 2 * len(source_ids),
            "expected_new_scalar_parameters": 48,
            "frozen_occurrence_kind_counts": dict(sorted(kind_counts.items())),
        },
        "source_slack_coordinates": slack_records,
        "assumption_ledger": {
            "needed": [
                "Omega is nonzero",
                "every transition on each selected path is nonsingular",
                "strong GC makes the propagated v_c path-independent",
                "the source timid transition is retained as a source-level definition",
            ],
            "consequence": (
                "v_c is nonzero at all 24 sources by invertible path propagation, "
                "so the local parameterisation is exhaustive."
            ),
            "not_assumed": [
                "strong operator MSR",
                "paper Eq.(108) as an operator definition",
                "the frozen Q reconstruction is a cover of this profile",
            ],
        },
        "recursive_effects": {
            "eq107": {
                "status": "SOURCE_NATIVE_REEXPANSION_REQUIRED",
                "reason": (
                    "The frozen non-timid expression uses T_precursor and then "
                    "installs Eq.(108) for that timid operator.  Replacing T by "
                    "source slack requires a recursive source-level rewrite, not "
                    "the stored 117 reduced expressions."
                ),
                "affected_frozen_occurrences": kind_counts.get("NON_TIMID", 0),
            },
            "eq108": {
                "status": "FORBIDDEN_IN_WEAK_MSR_COORDINATE_DEFINITION",
                "reason": "The dependency graph labels Eq.(108) as MSR_ELIMINATION.",
                "affected_frozen_occurrences": (
                    kind_counts.get("NON_TIMID", 0) + kind_counts.get("TIMID", 0)
                ),
            },
            "eq112_B_factors": {
                "status": "NOT_REUSABLE_WITHOUT_NEW_PROVENANCE_PROOF",
                "reason": (
                    "The frozen forward certificate explicitly depends on Eqs. "
                    "(107),(108),(111),(112), and its B definitions expand through "
                    "the v0.3.2 Eq.(107)/(108) reduction."
                ),
            },
        },
        "chart_cover_assessment": {
            "frozen_Q_chart_solver": "NOT_REUSABLE",
            "reason": (
                "Its transition predicates and B auxiliaries are built from the "
                "strong-MSR Q reconstruction; adding N variables afterwards does "
                "not enlarge that coordinate image."
            ),
            "abstract_R2_R4_partition": "CONDITIONALLY_REUSABLE_ONLY",
            "conditions": [
                "define Q_1,...,Q_4 directly from source antichain transitions",
                "prove their invertibility from source nonsingularity",
                (
                    "prove the relevant Eq.(120) identities directly under CPOBC "
                    "plus strong GC without Eq.(108)"
                ),
                (
                    "bind every source-native equation and localisation predicate "
                    "to the selected chart"
                ),
            ],
            "current_status": (
                "No source-native Eq.(120) provenance certificate is present in this "
                "prototype; therefore neither the old charts nor their 42 certificates "
                "may be used as a profile proof."
            ),
        },
        "global_compiler_status": "NOT_COMPILED_FAIL_CLOSED",
        "required_next_provenance": [
            "source-level recursive Eq.(107) compiler retaining each slack timid operator",
            (
                "strong-GC proof for any retained Eq.(112)-style conjugation "
                "without an Eq.(108)-expanded B factor"
            ),
            (
                "source-to-chart coverage certificate for every CPOBC, GC, "
                "reachable-MSR, inverse, and nonsingularity predicate"
            ),
        ],
        "solver_status": "NOT_RUN",
        "verdict": VERDICT,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload
