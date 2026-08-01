"""Exact bounded ``N != 0`` scout for the source-native 955 profile.

The ansatz assigns one upper-right coordinate to each of the 131 ON quotient
transition orbits,

    A_e = [[p_e, x_[e]], [0, 1]],

where ``p_e`` is the exact CSG character with ``t_j=1``.  It is evaluated
directly against the 783 raw CPOBC equations, the 320 source strong-GC basis
relations, the 24 reachable-state MSR rows at ``Omega=e_1``, and all source
determinants.  At ``p1-0`` the MSR operator residual has lower-right entry one,
so the entire ansatz lies outside the strong-MSR (``N=0``) slice.

The result is only an exact linear scout: all six Q commutators vanish in this
family, but no conclusion is drawn for general ``GL_2`` source operators.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from universe_lab.final_theory.one_sided_d2_v041_scout import (
    _csg_diagonal,
    _load_json,
    _matrix,
    _multiply,
    _profile_record,
    _rank,
    _relation_code,
    _residual,
    _sha256,
    _word,
)

CPOBC_PATH = "results/v0.3.1_cpobc_relations_n4.json"
REDUCTION_PATH = "results/v0.3.2_cpobc_generator_reduction.json"
GC_PATH = "results/v0.3.3_local_operator_gc_n4.json"
SLACK_INVENTORY_PATH = "results/v0.4.2_955_source_native_slack_compiler.json"
RESULT_PATH = "results/v0.4.2_955_n_nonzero_scout.json"

SCHEMA = "final-theory-v042-955-n-nonzero-triangular-scout-v1"
VERDICT = "V042_955_N_NONZERO_SCOUT_NO_WITNESS_OPEN"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def compile_source_native_955_n_nonzero_scout_v042(root: Path) -> dict[str, Any]:
    """Compile the exact QQ-linear scout without invoking a solver."""

    root = root.resolve()
    cpobc_path = root / CPOBC_PATH
    reduction_path = root / REDUCTION_PATH
    gc_path = root / GC_PATH
    slack_inventory_path = root / SLACK_INVENTORY_PATH
    cpobc = _load_json(cpobc_path)
    reduction = _load_json(reduction_path)
    operator_gc = _load_json(gc_path)
    slack_inventory = _load_json(slack_inventory_path)
    if not (
        slack_inventory.get("verdict")
        == "V042_955_SOURCE_NATIVE_SLACK_INVENTORY_READY_NO_SOLVER_RUN"
        and slack_inventory.get("passed") is True
        and slack_inventory.get("semantic_digest_sha256") == semantic_digest(slack_inventory)
    ):
        raise AssertionError("source-native slack inventory binding failed")
    connectivity = slack_inventory["source_state_recurrence"]["path_independence_enforced_by"][
        "endpoint_graph_connectivity"
    ]
    if not (
        connectivity["path_count"] == 407
        and connectivity["endpoint_count"] == 87
        and connectivity["unordered_same_endpoint_pair_count"] == 1529
        and connectivity["basis_edge_count"] == 320
        and connectivity["all_endpoint_graphs_connected"] is True
        and connectivity["connectivity_evidence_sha256"]
        == "1077ec8ce21902c5db6ce106aaf30dd92c4e5d0574edde75b06e3cbdd55c6b54"
    ):
        raise AssertionError("strong-GC connectivity certificate changed")

    records = {str(record["occurrence_id"]): record for record in reduction["reduction_map"]}
    if len(records) != 165:
        raise AssertionError("expected 165 source occurrence records")

    signatures: dict[tuple[int, int, int], str] = {}
    for record in records.values():
        signature = (
            int(record["stage"]),
            _relation_code(tuple(int(row) for row in record["source_relation_rows"])),
            int(record["precursor_code"]),
        )
        previous = signatures.setdefault(signature, str(record["orbit_id"]))
        if previous != record["orbit_id"]:
            raise AssertionError("one source signature maps to multiple ON orbits")

    variables = sorted(set(signatures.values()))
    if len(variables) != 131:
        raise AssertionError("expected 131 ON quotient orbit coordinates")

    def transition(record: dict[str, Any]):
        return _matrix(
            _csg_diagonal(
                int(record["stage"]),
                record["source_relation_rows"],
                int(record["precursor_code"]),
                coupling_ratio=None,
            ),
            Fraction(1),
            str(record["orbit_id"]),
        )

    def signature_transition(signature: dict[str, Any]):
        stage = int(signature["stage"])
        source_code = int(signature["source_relation_code"])
        precursor_code = int(signature["precursor_code"])
        mask = (1 << stage) - 1
        relation = tuple((source_code >> (stage * row)) & mask for row in range(stage))
        return _matrix(
            _csg_diagonal(stage, relation, precursor_code, coupling_ratio=None),
            Fraction(1),
            signatures[(stage, source_code, precursor_code)],
        )

    occurrence_matrices = {
        occurrence_id: transition(record) for occurrence_id, record in records.items()
    }
    if not all(matrix.upper_left != 0 for matrix in occurrence_matrices.values()):
        raise AssertionError("the CSG diagonal character must be nonsingular")

    cpobc_rows: list[dict[str, Fraction]] = []
    for relation in cpobc["relations"]:
        for equation in relation["raw_noncommutative_relation"]:
            identifiers = equation["operator_ids"]
            cpobc_rows.append(
                _residual(
                    _word(
                        occurrence_matrices[identifiers[token]] for token in equation["lhs_word"]
                    ),
                    _word(
                        occurrence_matrices[identifiers[token]] for token in equation["rhs_word"]
                    ),
                )
            )

    path_matrices = {}
    for paths in operator_gc["path_inventory"].values():
        for path in paths:
            product = _matrix(Fraction(1), Fraction(1))
            for transition_record in path["transitions"]:
                product = _multiply(
                    signature_transition(transition_record["quotient_signature"]),
                    product,
                )
            path_matrices[path["path_id"]] = product
    gc_rows = [
        _residual(
            path_matrices[relation["lhs_path_id"]],
            path_matrices[relation["rhs_path_id"]],
        )
        for relation in operator_gc["generating_relation_basis"]
    ]

    reachable_checks: list[dict[str, Any]] = []
    for constraint in cpobc["MSR_operator_constraints"]:
        upper_left = Fraction(int(constraint["identity_coefficient"]))
        lower_right = Fraction(int(constraint["identity_coefficient"]))
        for term in constraint["terms"]:
            coefficient = Fraction(int(term["coefficient"]))
            matrix = occurrence_matrices[term["transition_id"]]
            upper_left += coefficient * matrix.upper_left
            lower_right += coefficient * matrix.lower_right
        if upper_left != 0:
            raise AssertionError(
                f"reachable-state MSR fails on Omega=e1 at {constraint['source_id']}"
            )
        reachable_checks.append(
            {
                "source_id": str(constraint["source_id"]),
                "first_column_residual": ["0", "0"],
                "operator_residual_lower_right": str(lower_right),
            }
        )

    p1 = next(record for record in reachable_checks if record["source_id"] == "p1-0")
    if p1["operator_residual_lower_right"] != "1":
        raise AssertionError("the ansatz no longer has a uniform N!=0 witness at p1-0")

    def q(stage: int):
        return _matrix(
            Fraction(1, 2**stage),
            Fraction(1),
            signatures[(stage, 0, 0)],
        )

    commutators = {
        f"Q{left}_Q{right}": _residual(_multiply(q(left), q(right)), _multiply(q(right), q(left)))
        for left in range(1, 5)
        for right in range(left + 1, 5)
    }
    if len(cpobc_rows) != 783 or len(gc_rows) != 320 or len(reachable_checks) != 24:
        raise AssertionError("source relation census changed")

    cpobc_rank = _rank(cpobc_rows, variables)
    profile = _profile_record(cpobc_rows, gc_rows, commutators, variables)
    if cpobc_rank != 108 or profile["rank"] != 114 or profile["nullity"] != 17:
        raise AssertionError("exact triangular scout ranks changed")
    if profile["all_Q1_through_Q4_commutators_forced_zero_within_declared_ansatz"] is not True:
        raise AssertionError("a noncommutative triangular survivor requires review")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "scope": {
            "finite_source_stages": "n<=4",
            "dimension": 2,
            "field": "QQ",
            "identification_mode": "ON_QUOTIENT",
            "ansatz": "A_e=[[p_e,x_[e]],[0,1]], p_e=CSG(t_j=1), Omega=e1",
        },
        "source_artifact_sha256": {
            CPOBC_PATH: _sha256(cpobc_path),
            REDUCTION_PATH: _sha256(reduction_path),
            GC_PATH: _sha256(gc_path),
            SLACK_INVENTORY_PATH: _sha256(slack_inventory_path),
        },
        "checks": {
            "occurrences": 165,
            "ON_orbits_and_variables": 131,
            "all_determinants_nonzero": True,
            "raw_CPOBC_equations": 783,
            "raw_CPOBC_rank": cpobc_rank,
            "strong_GC_basis_equations": 320,
            "all_same_endpoint_GC_pairs_spanned": 1529,
            "strong_GC_connectivity_evidence_sha256": connectivity["connectivity_evidence_sha256"],
            "reachable_state_MSR_sources": 24,
            "all_reachable_state_residuals_zero": True,
            "uniform_N_nonzero_certificate": {
                "source_id": "p1-0",
                "operator_residual_lower_right": "1",
                "independent_of_upper_right_coordinates": True,
            },
            "combined_profile_rank": profile["rank"],
            "combined_profile_nullity": profile["nullity"],
            "commutator_functionals": profile["commutators"],
            "all_six_Q_commutators_forced_zero_in_ansatz": True,
        },
        "solver_status": "EXACT_SPARSE_QQ_GAUSSIAN_ELIMINATION_ONLY",
        "sage_status": "NOT_INVOKED",
        "numerical_or_finite_field_evidence_used": False,
        "claim_boundary": (
            "This excludes a noncommutative witness only in the declared exact "
            "N!=0 upper-triangular ON-quotient family. It does not prove general "
            "commutativity and it does not close any mixed upper/lower nonlinear patch."
        ),
        "verdict": VERDICT,
        "passed": True,
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def write_source_native_955_n_nonzero_scout_v042(root: Path) -> Path:
    destination = root.resolve() / RESULT_PATH
    payload = compile_source_native_955_n_nonzero_scout_v042(root)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination
