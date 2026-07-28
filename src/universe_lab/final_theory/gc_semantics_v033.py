"""GC/MSR semantic profiles and source-equation audit for v0.3.3.

The source paper first defines general covariance on the state obtained from
the fixed initial vector and writes the Markov sum rule on a reachable state.
Later operator identities are used in the CPOBC atomisation argument.  This
module keeps those strengths in separate namespaces and supplies exact
counterexamples to the unsupported reverse implications.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

Matrix2 = tuple[tuple[int, int], tuple[int, int]]
Vector2 = tuple[int, int]

GC_FIXED_VECTOR = "GC_FIXED_VECTOR"
GC_ALL_INITIAL_VECTORS = "GC_ALL_INITIAL_VECTORS"
GC_STRONG_OPERATOR = "GC_STRONG_OPERATOR"

MSR_REACHABLE_STATE = "MSR_REACHABLE_STATE"
MSR_STRONG_OPERATOR = "MSR_STRONG_OPERATOR"

PAPER_STRONG_OPERATOR_PROFILE = "PAPER_STRONG_OPERATOR_PROFILE"
REACHABLE_STATE_PROFILE = "REACHABLE_STATE_PROFILE"

GC_VERDICT = "STRONG_OPERATOR_GC_ADDITIONAL_AXIOM"
MSR_VERDICT = "STRONG_OPERATOR_MSR_ADDITIONAL_AXIOM"
SOURCE_VERDICT = "SOURCE_INDEXING_DISCREPANCY_CANDIDATE"


def stable_hash(value: Any) -> str:
    """Return a deterministic semantic SHA-256 digest."""

    payload = json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def matrix_add(left: Matrix2, right: Matrix2) -> Matrix2:
    return tuple(
        tuple(left[row][column] + right[row][column] for column in range(2))
        for row in range(2)
    )  # type: ignore[return-value]


def matrix_subtract(left: Matrix2, right: Matrix2) -> Matrix2:
    return tuple(
        tuple(left[row][column] - right[row][column] for column in range(2))
        for row in range(2)
    )  # type: ignore[return-value]


def matrix_vector(matrix: Matrix2, vector: Vector2) -> Vector2:
    return (
        matrix[0][0] * vector[0] + matrix[0][1] * vector[1],
        matrix[1][0] * vector[0] + matrix[1][1] * vector[1],
    )


def determinant(matrix: Matrix2) -> int:
    return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]


def _matrix_record(matrix: Matrix2) -> list[list[int]]:
    return [list(row) for row in matrix]


def gc_fixed_vector_counterexample() -> dict[str, Any]:
    """An exact invertible counterexample to fixed-vector => operator equality."""

    identity: Matrix2 = ((1, 0), (0, 1))
    y: Matrix2 = ((1, 1), (0, 1))
    omega: Vector2 = (1, 0)
    x_omega = matrix_vector(identity, omega)
    y_omega = matrix_vector(y, omega)
    return {
        "field": "Z embedded in every characteristic-zero field",
        "Omega": list(omega),
        "X": _matrix_record(identity),
        "Y": _matrix_record(y),
        "X_Omega": list(x_omega),
        "Y_Omega": list(y_omega),
        "det_X": determinant(identity),
        "det_Y": determinant(y),
        "X_equals_Y": identity == y,
        "fixed_vector_equality": x_omega == y_omega,
        "both_operators_invertible": determinant(identity) != 0 and determinant(y) != 0,
        "certifies": "GC_FIXED_VECTOR_DOES_NOT_IMPLY_GC_STRONG_OPERATOR",
    }


def msr_reachable_state_counterexample() -> dict[str, Any]:
    """Exact nonsingular MSR summands whose sum is only correct on one state."""

    identity: Matrix2 = ((1, 0), (0, 1))
    first: Matrix2 = ((2, 0), (0, 2))
    second: Matrix2 = ((-1, 1), (0, -1))
    total = matrix_add(first, second)
    omega: Vector2 = (1, 0)
    residual = matrix_subtract(total, identity)
    residual_on_omega = matrix_vector(residual, omega)
    return {
        "field": "Z embedded in every characteristic-zero field",
        "reachable_state": list(omega),
        "A_1": _matrix_record(first),
        "A_2": _matrix_record(second),
        "sum_A": _matrix_record(total),
        "sum_A_minus_I": _matrix_record(residual),
        "residual_on_reachable_state": list(residual_on_omega),
        "det_A_1": determinant(first),
        "det_A_2": determinant(second),
        "all_transition_summands_invertible": (
            determinant(first) != 0 and determinant(second) != 0
        ),
        "reachable_state_MSR": residual_on_omega == (0, 0),
        "strong_operator_MSR": total == identity,
        "certifies": "MSR_REACHABLE_STATE_DOES_NOT_IMPLY_MSR_STRONG_OPERATOR",
    }


def possible_equivalence_assumptions() -> list[dict[str, Any]]:
    """Audit assumptions that can lift on-state equality to operator equality."""

    return [
        {
            "assumption": "equality is postulated for every initial vector",
            "sufficient": True,
            "necessary": True,
            "qualification": (
                "necessary and sufficient when both sides are linear maps on the same full space"
            ),
            "paper_explicit": False,
            "project_policy": "available only in PAPER_STRONG_OPERATOR_PROFILE",
            "finite_n4_mechanically_checkable": True,
        },
        {
            "assumption": "reachable vectors span H",
            "sufficient": True,
            "necessary": False,
            "qualification": "equality on a spanning reachable set fixes a linear map",
            "paper_explicit": False,
            "project_policy": "not assumed",
            "finite_n4_mechanically_checkable": (
                "only after a concrete representation and its reachable vectors are supplied"
            ),
        },
        {
            "assumption": "Omega is separating for the relevant operator algebra",
            "sufficient": True,
            "necessary": False,
            "qualification": "requires X-Y to lie in the algebra for which Omega is separating",
            "paper_explicit": False,
            "project_policy": "not assumed",
            "finite_n4_mechanically_checkable": (
                "only after a concrete algebra representation is supplied"
            ),
        },
        {
            "assumption": "Omega is cyclic plus X-Y belongs to the appropriate commutant",
            "sufficient": True,
            "necessary": False,
            "qualification": (
                "cyclicity alone is insufficient; the commutant condition is essential"
            ),
            "paper_explicit": False,
            "project_policy": "not assumed",
            "finite_n4_mechanically_checkable": (
                "only after a concrete representation is supplied"
            ),
        },
        {
            "assumption": "transition operators act only on source-state subspaces",
            "sufficient": False,
            "necessary": False,
            "qualification": (
                "defines equality of restrictions, not equality of global operators, unless the "
                "source subspaces span and the restrictions are compatible"
            ),
            "paper_explicit": False,
            "project_policy": "kept in REACHABLE_STATE_PROFILE",
            "finite_n4_mechanically_checkable": (
                "source restrictions are checkable; global lifting is not automatic"
            ),
        },
        {
            "assumption": "operators are quotiented by equality on reachable states",
            "sufficient": True,
            "necessary": False,
            "qualification": (
                "makes equality true in a quotient algebra by definition and changes the "
                "presentation; it does not prove equality in the original operator algebra"
            ),
            "paper_explicit": False,
            "project_policy": "not identified with the strong profile",
            "finite_n4_mechanically_checkable": True,
        },
        {
            "assumption": "faithful representation of the transition algebra",
            "sufficient": False,
            "necessary": False,
            "qualification": (
                "faithfulness transfers an algebra equality to operators but does not turn "
                "equality on one vector into an algebra equality"
            ),
            "paper_explicit": False,
            "project_policy": "not assumed",
            "finite_n4_mechanically_checkable": (
                "only after an algebra and concrete representation are supplied"
            ),
        },
    ]


def validate_relation_namespace(
    *,
    semantic_profile: str,
    relation_strength: str,
) -> bool:
    """Reject strong equations in the weak reachable-state namespace."""

    profiles = {PAPER_STRONG_OPERATOR_PROFILE, REACHABLE_STATE_PROFILE}
    if semantic_profile not in profiles:
        raise ValueError(f"unknown semantic profile: {semantic_profile}")
    if semantic_profile == REACHABLE_STATE_PROFILE and relation_strength in {
        GC_STRONG_OPERATOR,
        MSR_STRONG_OPERATOR,
    }:
        raise ValueError("strong operator relation cannot enter REACHABLE_STATE_PROFILE")
    return True


def gc_msr_semantics_audit() -> dict[str, Any]:
    gc_counterexample = gc_fixed_vector_counterexample()
    msr_counterexample = msr_reachable_state_counterexample()
    passed = bool(
        gc_counterexample["fixed_vector_equality"]
        and gc_counterexample["both_operators_invertible"]
        and not gc_counterexample["X_equals_Y"]
        and msr_counterexample["reachable_state_MSR"]
        and msr_counterexample["all_transition_summands_invertible"]
        and not msr_counterexample["strong_operator_MSR"]
    )
    payload: dict[str, Any] = {
        "semantic_profiles": {
            REACHABLE_STATE_PROFILE: {
                "GC": GC_FIXED_VECTOR,
                "MSR": MSR_REACHABLE_STATE,
                "operator_ideal_relations_emitted": False,
            },
            PAPER_STRONG_OPERATOR_PROFILE: {
                "GC": GC_STRONG_OPERATOR,
                "MSR": MSR_STRONG_OPERATOR,
                "operator_ideal_relations_emitted": True,
                "status": "explicit project profile using additional axioms",
            },
        },
        "implication_diagram": {
            "GC": [
                {
                    "from": GC_STRONG_OPERATOR,
                    "to": GC_ALL_INITIAL_VECTORS,
                    "valid": True,
                },
                {
                    "from": GC_ALL_INITIAL_VECTORS,
                    "to": GC_STRONG_OPERATOR,
                    "valid": True,
                    "reason": "linear maps agreeing on every vector are equal",
                },
                {
                    "from": GC_ALL_INITIAL_VECTORS,
                    "to": GC_FIXED_VECTOR,
                    "valid": True,
                },
                {
                    "from": GC_FIXED_VECTOR,
                    "to": GC_STRONG_OPERATOR,
                    "valid": False,
                    "counterexample": "gc_fixed_vector_counterexample",
                },
            ],
            "MSR": [
                {
                    "from": MSR_STRONG_OPERATOR,
                    "to": MSR_REACHABLE_STATE,
                    "valid": True,
                },
                {
                    "from": MSR_REACHABLE_STATE,
                    "to": MSR_STRONG_OPERATOR,
                    "valid": False,
                    "counterexample": "msr_reachable_state_counterexample",
                },
            ],
        },
        "exact_counterexamples": {
            "gc_fixed_vector_counterexample": gc_counterexample,
            "msr_reachable_state_counterexample": msr_counterexample,
        },
        "possible_equivalence_assumptions": possible_equivalence_assumptions(),
        "source_observations": {
            "eq31_pdf_page": 15,
            "eq32_pdf_page": 15,
            "eq33_pdf_page": 15,
            "GC_definition_pdf_page": 15,
            "eq33_written_strength": MSR_STRONG_OPERATOR,
            "eq33_preceding_premise_strength": MSR_REACHABLE_STATE,
            "GC_written_strength": GC_FIXED_VECTOR,
            "paper_intent_not_inferred": True,
        },
        "GC_verdict": GC_VERDICT,
        "MSR_verdict": MSR_VERDICT,
        "assumptions": [
            "all maps in the exact counterexamples are linear over characteristic zero",
            "the paper's later operator equalities are evaluated in a separate strong profile",
            "no cyclicity, separating-vector, spanning, or faithfulness premise is inferred",
        ],
        "unresolved_components": [
            "whether the authors intended GC/MSR as global operator axioms",
            "whether a future representation supplies a separating or spanning condition",
        ],
        "passed": passed,
    }
    payload["semantic_digest_sha256"] = stable_hash(payload)
    return payload


def source_equation_audit() -> dict[str, Any]:
    """Record the PDF/HTML equation audit and the independent Eq. (112) derivation."""

    equations = {
        "31": {
            "pdf_page": 15,
            "content": "|c_n> = A_{n-1} ... A_1 |Omega> = A_gamma(c_n)|Omega>",
            "visual_pdf_checked": True,
        },
        "32": {
            "pdf_page": 15,
            "content": "|c_n> = sum_j |c_{n+1}^j>",
            "visual_pdf_checked": True,
        },
        "33": {
            "pdf_page": 15,
            "content": "|c_n> = sum_j A_n^j|c_n> => sum_j A_n^j = I",
            "visual_pdf_checked": True,
        },
        "107": {
            "pdf_page": 27,
            "content": "A_n = A_m G_n G_m^-1 for a non-timid transition",
            "visual_pdf_checked": True,
        },
        "108": {
            "pdf_page": 27,
            "content": "timid transition inclusion-exclusion in gregarious operators",
            "visual_pdf_checked": True,
        },
        "109": {
            "pdf_page": 27,
            "content": "G_n^(0) B_(n-1)^(0) = B_n^(1) G_(n-1)^(0)",
            "visual_pdf_checked": True,
        },
        "110": {
            "pdf_page": 27,
            "content": "B_n^(1) G_(n-1)^(0) = B_(n-1)^(0) G_n^(1)",
            "visual_pdf_checked": True,
        },
        "111": {
            "pdf_page": 27,
            "content": "G_n^(0) = B_(n-1)^(0) G_n^(1) (B_(n-1)^(0))^-1",
            "visual_pdf_checked": True,
        },
        "112": {
            "pdf_page": 27,
            "content": "G_n^(0) = S_alpha Q_n S_alpha^-1",
            "visual_pdf_checked": True,
        },
        "113": {
            "pdf_page": 27,
            "pdf_content": "[S_alpha^-1 S_beta, Q_(n+1)] = 0",
            "html_content": "[S_alpha^-1 S_beta, Q_(n+1)] = 0",
            "visual_pdf_checked": True,
        },
        "114": {
            "pdf_page": 27,
            "content": "G_n G_k^-1 G_m = G_m G_k^-1 G_n",
            "visual_pdf_checked": True,
        },
        "163": {
            "pdf_page": 35,
            "content": "[S_2^-1 S_1, Q_4] = 0 for two paths expressing G_4",
            "role": "appendix stage-consistency cross-check",
        },
    }
    independent_derivation = [
        "S_alpha Q_n S_alpha^-1 = S_beta Q_n S_beta^-1",
        "Q_n S_alpha^-1 S_beta = S_alpha^-1 S_beta Q_n",
        "[S_alpha^-1 S_beta, Q_n] = 0",
    ]
    payload: dict[str, Any] = {
        "source": "arXiv:2603.25503v1",
        "equations": equations,
        "independent_eq112_comparison": {
            "steps": independent_derivation,
            "derived_index": "Q_n",
            "printed_eq113_index": "Q_(n+1)",
            "appendix_eq163_index_for_G4": "Q_4",
            "stage_consistency": (
                "G_n and Q_n are stage-n gregarious transitions; every factor of S_alpha "
                "in Eq. (112) is a B_(n-1) operator"
            ),
        },
        "branches": {
            "EQ113_QN_BRANCH": {
                "basis": "formal comparison of Eq. (112) and appendix Eq. (163)",
                "status": "PROJECT_DERIVED_BRANCH",
            },
            "EQ113_QN_PLUS_1_BRANCH": {
                "basis": "literal printed PDF and public HTML Eq. (113)",
                "status": "SOURCE_LITERAL_BRANCH",
            },
        },
        "branch_mixing_forbidden": True,
        "author_query_draft": (
            "In Eq. (112), comparing two atomisation paths for "
            "G_n = S_alpha Q_n S_alpha^{-1} appears to give "
            "[S_alpha^{-1}S_beta,Q_n]=0, and Appendix Eq. (163) uses Q_4 for G_4. "
            "Eq. (113) instead prints Q_{n+1}. Is Q_{n+1} intentional under a stage "
            "convention not stated there, or should the index be Q_n?"
        ),
        "verdict": SOURCE_VERDICT,
        "unresolved_components": [
            "authorial intent behind the Q_(n+1) index in Eq. (113)",
            "effect of a possible stage convention not explicit around Eqs. (112)--(113)",
        ],
        "passed": True,
    }
    payload["semantic_digest_sha256"] = stable_hash(payload)
    return payload


def literature_matrix() -> dict[str, Any]:
    """Classify the mandatory v0.3.3 literature gate."""

    entries = [
        {
            "topic": "arXiv:2603.25503 current source record",
            "classification": "LITERATURE_LOCKED",
            "finding": (
                "official arXiv record remains v1 dated 2026-03-26; no journal reference, "
                "DOI, erratum, or later source version was found in the bounded search"
            ),
            "sources": ["arXiv:2603.25503v1"],
        },
        {
            "topic": "paper Eq. (31)--(33) and GC definition",
            "classification": "SOURCE_AMBIGUITY",
            "finding": (
                "GC is written on A_gamma|Omega>; Eq. (33) promotes an on-state MSR "
                "premise to a global operator equality without a stated lifting assumption"
            ),
            "sources": ["arXiv:2603.25503v1"],
        },
        {
            "topic": "paper atomisation and decimation definition",
            "classification": "LITERATURE_LOCKED",
            "finding": "non-gregarious maximal elements are reinserted gregariously",
            "sources": ["arXiv:2603.25503v1", "arXiv:gr-qc/9904062v3"],
        },
        {
            "topic": "paper CPOBC Eqs. (103)--(114)",
            "classification": "SOURCE_AMBIGUITY",
            "finding": "Eq. (113) prints Q_(n+1), while Eq. (112) directly yields Q_n",
            "sources": ["arXiv:2603.25503v1"],
        },
        {
            "topic": "classical discrete general covariance and path independence",
            "classification": "LITERATURE_LOCKED",
            "finding": "classical same-endpoint products are path independent",
            "sources": ["arXiv:gr-qc/9904062v3"],
        },
        {
            "topic": "classical solution with vanishing transitions",
            "classification": "LITERATURE_LOCKED",
            "finding": (
                "the extended classical axioms and completely general tower-of-turtles "
                "solution are available in the versioned primary source"
            ),
            "sources": ["arXiv:gr-qc/0504066v3"],
        },
        {
            "topic": "operator-valued GC/path-independence follow-up",
            "classification": "FORMULATION_MISMATCH",
            "finding": (
                "bounded searches found QSGP, quantum-causal-history, and on-state operator "
                "formalisms, but no source resolving this CPOBC operator-GC lifting"
            ),
            "sources": [
                "arXiv:1204.5767v1",
                "arXiv:1303.0433v1",
                "arXiv:quant-ph/9902008v3",
            ],
        },
        {
            "topic": "general CPOBC d=2 representation and atomisation compiler follow-up",
            "classification": "OPEN_TARGET",
            "finding": (
                "no resolving primary source was found by exact-title, author, terminology, "
                "arXiv concept, and citation-route searches; this is search-bounded, not a "
                "global nonexistence claim"
            ),
            "sources": ["arXiv:2603.25503v1"],
        },
    ]
    payload: dict[str, Any] = {
        "search_date": "2026-07-28",
        "search_routes": [
            "exact arXiv ID and exact title",
            "both author names",
            "exact equation and atomisation terminology",
            "operator general covariance",
            "quantum sequential growth path independence",
            "CPOBC representation",
            "journal, DOI, erratum, and source-version record",
            "citation and bibliography follow-up",
        ],
        "entries": entries,
        "search_boundary": (
            "absence findings are limited to the documented primary-source search routes "
            "and are not proofs of worldwide nonexistence"
        ),
        "passed": all(
            entry["classification"]
            in {
                "LITERATURE_LOCKED",
                "REGRESSION_ONLY",
                "OPEN_TARGET",
                "CLAIMED_BUT_UNVERIFIED",
                "FORMULATION_MISMATCH",
                "SOURCE_AMBIGUITY",
            }
            for entry in entries
        ),
    }
    payload["semantic_digest_sha256"] = stable_hash(payload)
    return payload
