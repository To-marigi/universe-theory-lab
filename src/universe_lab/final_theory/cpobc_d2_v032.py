"""Exact, deliberately partial d=2 CPOBC classification audit for v0.3.2.

The v0.3.1 finite compiler is treated as frozen input.  This module performs
the parts of the requested d=2 programme that can currently be certified:

* re-check the frozen n<=4 inventory and the paper-defined necessary
  relations used by the d=2 reduction;
* reduce every transition occurrence through paper Eqs. (107) and (108) to
  gregarious generators attached to finite causets;
* rewrite all 783 denominator-cleared Bell equations and all 24 MSR
  constraints through that occurrence map;
* certify the exhaustive S1/S2/S3 split of the commuting antichain ratios
  R_n = Q_1^-1 Q_n.

The operator GC identities and atomisation paths required to apply Eq. (112)
to the twenty non-antichain gregarious generators are not present in the
v0.3.1 compiler.  Consequently the full stratum eliminations are not run and
the only permitted release verdict is ``CPOBC_D2_PARTIAL``.
"""

from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import platform
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import sympy as sp

from universe_lab.final_theory.causal_sets import (
    Relation,
    canonicalize,
    causet_id,
    enumerate_unlabeled_posets,
    has_relation,
)
from universe_lab.final_theory.cpobc_v03 import compile_cpobc_relations
from universe_lab.final_theory.cpobc_v031 import (
    PAPER_PDF,
    PAPER_SHA256,
    compile_cpobc_relations_v031,
)

BRANCH = "codex/final-theory-v0.3.2-cpobc-d2-classification-20260728"
SOURCE_COMMIT = "3ee453c574ad2e98132d6bb1965836529809ea49"
PAPER_ID = "arXiv:2603.25503v1"
COMPILER_MAX_STAGE = 4
D2 = 2

FROZEN_RELATIONS_PATH = "results/v0.3.1_cpobc_relations_n4.json"
FROZEN_RELATIONS_SHA256 = "77277a09323d225cc0df00277a6dcedde317120bd6f75db0c006f3de8a0e23d3"
FROZEN_D3_PATH = "results/v0.3.1_d3_strata_manifest.json"
FROZEN_D3_SHA256 = "3729a701f6f909cecb6d6889d72bcb7cd5b4d03cc9822d39c56329432e9297c5"

VERDICT_FOUND = "CPOBC_D2_NONCOMMUTATIVE_REPRESENTATION_FOUND"
VERDICT_NO_GO = "CPOBC_D2_COMPLETE_NO_GO"
VERDICT_PARTIAL = "CPOBC_D2_PARTIAL"
ALLOWED_VERDICTS = {VERDICT_FOUND, VERDICT_NO_GO, VERDICT_PARTIAL}

EXPECTED_FROZEN_COUNTS = {
    "compiled_cross_stage_relations": 641,
    "denominator_cleared_word_equations": 783,
    "transition_occurrence_variables": 165,
    "MSR_operator_constraints": 24,
    "bell_families": 146,
    "transition_orbits": 131,
}

Word = tuple[str, ...]
LinearExpression = dict[Word, int]


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_head(root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    commit = completed.stdout.strip()
    if len(commit) != 40:
        raise RuntimeError(f"unexpected git HEAD: {commit!r}")
    return commit


def _exact(value: Any) -> str:
    return str(sp.factor(sp.cancel(sp.sympify(value))))


def _matrix_record(matrix: sp.MatrixBase) -> list[list[str]]:
    return [
        [_exact(matrix[row, column]) for column in range(matrix.cols)] for row in range(matrix.rows)
    ]


def _zero_matrix(matrix: sp.MatrixBase) -> bool:
    return all(sp.cancel(sp.expand(entry)) == 0 for entry in matrix)


def _inverse_token(token: str) -> str:
    return token.removesuffix("^-1") if token.endswith("^-1") else token + "^-1"


def _free_reduce_word(word: Word) -> Word:
    reduced: list[str] = []
    for token in word:
        if reduced and reduced[-1] == _inverse_token(token):
            reduced.pop()
        else:
            reduced.append(token)
    return tuple(reduced)


def _normalise_expression(terms: LinearExpression) -> LinearExpression:
    return {word: coefficient for word, coefficient in sorted(terms.items()) if coefficient}


def _add_term(expression: LinearExpression, coefficient: int, word: Word) -> None:
    reduced = _free_reduce_word(word)
    expression[reduced] = expression.get(reduced, 0) + coefficient


def _scale_expression(
    expression: LinearExpression,
    coefficient: int,
) -> LinearExpression:
    return _normalise_expression({word: coefficient * value for word, value in expression.items()})


def _add_expressions(*expressions: LinearExpression) -> LinearExpression:
    result: LinearExpression = {}
    for expression in expressions:
        for word, coefficient in expression.items():
            _add_term(result, coefficient, word)
    return _normalise_expression(result)


def _multiply_expressions(
    left: LinearExpression,
    right: LinearExpression,
) -> LinearExpression:
    result: LinearExpression = {}
    for left_word, left_coefficient in left.items():
        for right_word, right_coefficient in right.items():
            _add_term(
                result,
                left_coefficient * right_coefficient,
                left_word + right_word,
            )
    return _normalise_expression(result)


def _expression_record(expression: LinearExpression) -> list[dict[str, Any]]:
    return [
        {"coefficient": coefficient, "word": list(word)}
        for word, coefficient in sorted(expression.items())
    ]


def _relation_from_selected_vertices(
    relation: Relation,
    selected_vertices: tuple[int, ...],
) -> Relation:
    old_to_new = {old_vertex: new_vertex for new_vertex, old_vertex in enumerate(selected_vertices)}
    rows = [0] * len(selected_vertices)
    for old_lower in selected_vertices:
        for old_upper in selected_vertices:
            if has_relation(relation, old_lower, old_upper):
                rows[old_to_new[old_lower]] |= 1 << old_to_new[old_upper]
    return canonicalize(tuple(rows))


def _precursor_relation(relation: Relation, precursor_code: int) -> Relation:
    selected = tuple(vertex for vertex in range(len(relation)) if precursor_code & (1 << vertex))
    return _relation_from_selected_vertices(relation, selected)


def _maximal_vertices(relation: Relation) -> tuple[int, ...]:
    return tuple(
        vertex
        for vertex in range(len(relation))
        if not any(
            has_relation(relation, vertex, possible_upper)
            for possible_upper in range(len(relation))
        )
    )


def _generator_token(relation: Relation) -> str | None:
    if not relation:
        return None
    if all(row == 0 for row in relation):
        return f"Q_{len(relation)}"
    return f"G_{causet_id(relation)}"


def _generator_word(relation: Relation, *, inverse: bool = False) -> Word:
    token = _generator_token(relation)
    if token is None:
        return ()
    return (_inverse_token(token) if inverse else token,)


def timid_generator_expression(relation: Relation) -> LinearExpression:
    """Expand paper Eq. (108) as an exact noncommutative linear expression."""

    if not relation:
        return {(): 1}
    source_generator = _generator_word(relation)
    expression: LinearExpression = {(): 1, source_generator: -1}
    maximal = _maximal_vertices(relation)
    all_vertices = set(range(len(relation)))
    for subset_size in range(1, len(maximal) + 1):
        for deleted in itertools.combinations(maximal, subset_size):
            remaining = tuple(sorted(all_vertices - set(deleted)))
            lower_relation = _relation_from_selected_vertices(
                relation,
                remaining,
            )
            lower = _generator_word(lower_relation)
            lower_inverse = _generator_word(lower_relation, inverse=True)
            first_coefficient = (-1) ** subset_size
            second_coefficient = (-1) ** (subset_size - 1)
            _add_term(
                expression,
                first_coefficient,
                source_generator + lower_inverse,
            )
            _add_term(
                expression,
                second_coefficient,
                lower + source_generator + lower_inverse,
            )
    return _normalise_expression(expression)


def _occurrence_expression(
    relation: Relation,
    precursor_code: int,
) -> tuple[str, LinearExpression, str]:
    full_precursor = (1 << len(relation)) - 1
    if precursor_code == 0:
        return (
            "GREGARIOUS",
            {_generator_word(relation): 1},
            "definition of the source-causet gregarious transition",
        )
    if precursor_code == full_precursor:
        return (
            "TIMID",
            timid_generator_expression(relation),
            "paper Eq.(108), PDF page 27; Lemma 3.2 specialised to CPOBC",
        )
    precursor = _precursor_relation(relation, precursor_code)
    timid_precursor = timid_generator_expression(precursor)
    suffix = {_generator_word(relation) + _generator_word(precursor, inverse=True): 1}
    return (
        "NON_TIMID",
        _multiply_expressions(timid_precursor, suffix),
        "paper Eq.(107), PDF page 27, followed by Eq.(108)",
    )


def _occurrence_catalog(
    base: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for pair in base["bell_pairs"]:
        relation = tuple(pair["source_relation_rows"])
        for label in ("A", "A_prime"):
            transition = pair["transition_pair"][label]
            occurrence_id = transition["id"]
            precursor_code = int(transition["precursor_code"])
            candidate = {
                "occurrence_id": occurrence_id,
                "transition_hash": transition["hash"],
                "operator_variable": f"X_{transition['hash'][:16]}",
                "orbit_id": transition["orbit_id"],
                "source_id": transition["source_id"],
                "source_relation_rows": list(relation),
                "target_id": transition["target_id"],
                "precursor_code": precursor_code,
                "precursor": list(transition["precursor"]),
                "stage": int(transition["stage"]),
            }
            previous = records.get(occurrence_id)
            if previous is not None and previous != candidate:
                raise AssertionError(f"inconsistent transition occurrence {occurrence_id}")
            records[occurrence_id] = candidate
    return records


def _build_occurrence_reduction(
    base: dict[str, Any],
) -> tuple[dict[str, LinearExpression], list[dict[str, Any]]]:
    catalog = _occurrence_catalog(base)
    expressions: dict[str, LinearExpression] = {}
    records = []
    for occurrence_id, occurrence in sorted(catalog.items()):
        relation = tuple(occurrence["source_relation_rows"])
        kind, expression, derivation = _occurrence_expression(
            relation,
            int(occurrence["precursor_code"]),
        )
        expressions[occurrence_id] = expression
        dependencies = sorted({token.removesuffix("^-1") for word in expression for token in word})
        records.append(
            {
                **occurrence,
                "transition_kind": kind,
                "derivation": derivation,
                "reduced_expression": _expression_record(expression),
                "reduced_expression_sha256": _stable_hash(_expression_record(expression)),
                "generator_dependencies": dependencies,
                "exact": True,
            }
        )
    return expressions, records


def _rewrite_local_word(
    word: list[str],
    aliases: dict[str, str],
    occurrence_expressions: dict[str, LinearExpression],
) -> LinearExpression:
    expression: LinearExpression = {(): 1}
    for alias in word:
        occurrence_id = aliases[alias]
        expression = _multiply_expressions(
            expression,
            occurrence_expressions[occurrence_id],
        )
    return expression


def _rewritten_relation_inventory(
    compiled: dict[str, Any],
    occurrence_expressions: dict[str, LinearExpression],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for relation in compiled["relations"]:
        aliases = {
            alias: record["occurrence_id"] for alias, record in relation["transition_orbit"].items()
        }
        for equation in relation["denominator_cleared_form"]["noncommutative_polynomial_equations"]:
            lhs = _rewrite_local_word(
                list(equation["lhs_word"]),
                aliases,
                occurrence_expressions,
            )
            rhs = _rewrite_local_word(
                list(equation["rhs_word"]),
                aliases,
                occurrence_expressions,
            )
            residual = _add_expressions(lhs, _scale_expression(rhs, -1))
            residual_record = _expression_record(residual)
            records.append(
                {
                    "relation_id": relation["relation_id"],
                    "equation_id": equation["equation_id"],
                    "branch": relation["branch"],
                    "reduced_term_count": len(residual_record),
                    "reduced_residual_sha256": _stable_hash(residual_record),
                    "identity_after_reduction": not residual,
                }
            )
    return records


def _rewritten_msr_inventory(
    compiled: dict[str, Any],
    occurrence_expressions: dict[str, LinearExpression],
) -> list[dict[str, Any]]:
    records = []
    for constraint in compiled["MSR_operator_constraints"]:
        residual: LinearExpression = {(): -1}
        missing: list[str] = []
        for term in constraint["terms"]:
            occurrence_id = term["transition_id"]
            occurrence_expression = occurrence_expressions.get(occurrence_id)
            if occurrence_expression is None:
                missing.append(occurrence_id)
                continue
            residual = _add_expressions(
                residual,
                _scale_expression(
                    occurrence_expression,
                    int(term["coefficient"]),
                ),
            )
        residual_record = _expression_record(residual)
        records.append(
            {
                "constraint_id": constraint["constraint_id"],
                "source_id": constraint["source_id"],
                "missing_occurrences": sorted(missing),
                "reduced_residual": residual_record,
                "reduced_residual_sha256": _stable_hash(residual_record),
                "identity_after_reduction": not residual and not missing,
            }
        )
    return records


def _generator_inventory() -> list[dict[str, Any]]:
    levels = enumerate_unlabeled_posets(COMPILER_MAX_STAGE)
    generators = []
    for stage in range(1, COMPILER_MAX_STAGE + 1):
        for relation in levels[stage]:
            token = _generator_token(relation)
            assert token is not None
            antichain = all(row == 0 for row in relation)
            generators.append(
                {
                    "generator": token,
                    "source_id": causet_id(relation),
                    "stage": stage,
                    "source_relation_rows": list(relation),
                    "kind": ("ANTICHAIN_Q" if antichain else "CAUSET_GREGARIOUS"),
                    "eq112_status": (
                        "EXACT_Q_IDENTITY_TRIVIAL_AT_ANTICHAIN"
                        if antichain
                        else "UNREDUCED_ATOMISATION_PATH_NOT_COMPILED"
                    ),
                    "d2_scalar_entry_variables": 4,
                }
            )
    return generators


def generator_reduction_v032(
    compiled: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Reduce all occurrence variables through Eqs. (107) and (108).

    The function also rewrites every denominator-cleared Bell equation and
    every MSR operator constraint.  It intentionally stops before Eq. (112)
    because the atomisation path operators and operator-level GC identities
    are absent from the frozen compiler.
    """

    compiled_result = compiled or compile_cpobc_relations_v031()
    base = compile_cpobc_relations(COMPILER_MAX_STAGE)
    occurrence_expressions, occurrence_records = _build_occurrence_reduction(base)
    rewritten_relations = _rewritten_relation_inventory(
        compiled_result,
        occurrence_expressions,
    )
    rewritten_msr = _rewritten_msr_inventory(
        compiled_result,
        occurrence_expressions,
    )
    generators = _generator_inventory()
    unresolved_generators = [
        item["generator"]
        for item in generators
        if item["eq112_status"] == "UNREDUCED_ATOMISATION_PATH_NOT_COMPILED"
    ]
    transition_kind_counts = Counter(record["transition_kind"] for record in occurrence_records)
    all_occurrences_mapped = len(occurrence_records) == EXPECTED_FROZEN_COUNTS[
        "transition_occurrence_variables"
    ] and len(occurrence_expressions) == len(occurrence_records)
    all_relations_rewritten = (
        len(rewritten_relations) == EXPECTED_FROZEN_COUNTS["denominator_cleared_word_equations"]
    )
    all_msr_rewritten = len(rewritten_msr) == EXPECTED_FROZEN_COUNTS[
        "MSR_operator_constraints"
    ] and all(not item["missing_occurrences"] for item in rewritten_msr)
    all_msr_identities = all(item["identity_after_reduction"] for item in rewritten_msr)
    relation_identity_count = sum(item["identity_after_reduction"] for item in rewritten_relations)
    msr_identity_count = sum(item["identity_after_reduction"] for item in rewritten_msr)
    scalar_unknown_count = sum(int(item["d2_scalar_entry_variables"]) for item in generators)

    return {
        "schema_version": "final-theory-cpobc-generator-reduction-v0.3.2",
        "branch": BRANCH,
        "source_commit": SOURCE_COMMIT,
        "code_commit": "UNCOMMITTED_WORKTREE",
        "paper_versions": [
            {
                "id": PAPER_ID,
                "version": "v1",
                "local_file": PAPER_PDF,
                "source_hash_sha256": PAPER_SHA256,
            }
        ],
        "assumptions": [
            "finite maximal-element sequential growth through source stage 4",
            "CPOBC transition operators are nonsingular",
            "paper Eqs.(107) and (108) apply to every compiled occurrence",
            "noncommutative multiplication order is preserved",
        ],
        "completeness_scope": (
            "all 165 occurrence variables are reduced through Eqs.(107),(108) "
            "and all 783 finite Bell word equations plus 24 MSR constraints "
            "are rewritten; Eq.(112) and operator-level GC are incomplete"
        ),
        "exact_numeric_distinction": {
            "exact": (
                "integer noncommutative word coefficients, finite-causet "
                "combinatorics, canonical SHA-256 digests"
            ),
            "numeric": "none accepted as certificate",
        },
        "counts": {
            "occurrence_variables": len(occurrence_records),
            "transition_kind_counts": dict(sorted(transition_kind_counts.items())),
            "independent_matrix_generators_after_eq107_eq108": len(generators),
            "antichain_Q_generators": sum(item["kind"] == "ANTICHAIN_Q" for item in generators),
            "eq112_unreduced_gregarious_generators": len(unresolved_generators),
            "d2_scalar_unknowns_before_inverse_saturation_and_gauge": (scalar_unknown_count),
            "rewritten_word_equations": len(rewritten_relations),
            "Bell_free_word_identities_after_reduction": relation_identity_count,
            "Bell_residual_constraints_after_reduction": (
                len(rewritten_relations) - relation_identity_count
            ),
            "rewritten_MSR_constraints": len(rewritten_msr),
            "MSR_free_word_identities_after_reduction": msr_identity_count,
            "MSR_residual_constraints_after_reduction": (len(rewritten_msr) - msr_identity_count),
        },
        "reduction_map": occurrence_records,
        "generator_inventory": generators,
        "still_unreduced_occurrences": [],
        "still_unreduced_generators": unresolved_generators,
        "rewritten_relation_inventory": rewritten_relations,
        "rewritten_MSR_inventory": rewritten_msr,
        "equivalence_obligations": {
            "all_occurrences_mapped": all_occurrences_mapped,
            "all_denominator_cleared_relations_rewritten": (all_relations_rewritten),
            "all_MSR_constraints_rewritten": all_msr_rewritten,
            "all_MSR_constraints_reduce_to_word_identities": (all_msr_identities),
            "MSR_reduction_interpretation": (
                "An MSR residual need not vanish in the free word algebra; "
                "nonzero residuals remain exact constraints among the reduced "
                "gregarious generators and may vanish modulo Bell/GC ideals."
            ),
            "forward_direction": (
                "Any nonsingular CPOBC assignment obeying the paper hypotheses "
                "satisfies the Eq.(107)/(108) occurrence substitutions."
            ),
            "reverse_direction": (
                "A generator assignment defines all occurrences by the map, "
                "but is a finite CPOBC assignment only after every rewritten "
                "Bell relation, MSR, GC, and invertibility predicate is checked."
            ),
            "full_equivalence_status": (
                "PARTIAL_EQ107_EQ108_ONLY; EQ112_ATOMISATION_AND_GC_UNPROVED"
            ),
        },
        "phase3_strategy_gate": {
            "threshold_d2_scalar_unknowns": 40,
            "observed_d2_scalar_unknowns": scalar_unknown_count,
            "inverse_encoding_if_executed": (
                "adjugate plus determinant saturation, retaining 96 matrix "
                "entries; explicit inverse matrices would add 96 entries"
            ),
            "threshold_exceeded": scalar_unknown_count > 40,
            "decision": (
                "DO_NOT_RUN_DENSE_FULL_SYSTEM_GROEBNER; first compile Eq.(112) "
                "atomisation paths and operator GC, then reassess per stratum"
            ),
        },
        "unresolved_components": [
            "Eq.(112) atomisation-path reduction for 20 non-antichain G_c",
            "operator-level GC path identities are absent from v0.3.1 compiler",
            "full d=2 stratum polynomial ideals and determinant saturations",
            "independent full Phase-3 oracle",
        ],
        "certificate_hashes": [],
        "verdict": VERDICT_PARTIAL,
        "passed": (all_occurrences_mapped and all_relations_rewritten and all_msr_rewritten),
    }


def phase0_exact_audit_v032(root: Path) -> dict[str, Any]:
    """Re-check the frozen inventory and the exact F4 necessary-relation witness."""

    frozen_relations = root / FROZEN_RELATIONS_PATH
    frozen_d3 = root / FROZEN_D3_PATH
    paper = root / PAPER_PDF
    compiled = compile_cpobc_relations_v031()
    frozen_counts = {key: compiled["counts"][key] for key in EXPECTED_FROZEN_COUNTS}

    q11, q12, q21, q22 = sp.symbols("q11 q12 q21 q22")
    n11, n12, n21, n22 = sp.symbols("n11 n12 n21 n22")
    m11, m12, m21, m22 = sp.symbols("m11 m12 m21 m22")
    qn = sp.Matrix([[n11, n12], [n21, n22]])
    qm = sp.Matrix([[m11, m12], [m21, m22]])
    adj_q1 = sp.Matrix([[q22, -q12], [-q21, q11]])
    cleared_eq120 = qn * adj_q1 * qm - qm * adj_q1 * qn
    r_commutator_numerator = adj_q1 * qn * adj_q1 * qm - adj_q1 * qm * adj_q1 * qn
    implication_residual = sp.expand(r_commutator_numerator - adj_q1 * cleared_eq120)

    q1_scale, a2, b2, a3, b3, a4, b4 = sp.symbols(
        "q1 a2 b2 a3 b3 a4 b4",
        nonzero=True,
    )
    sigma_x = sp.Matrix([[0, 1], [1, 0]])
    matrices = {
        1: q1_scale * sigma_x,
        2: sigma_x * sp.diag(a2, b2),
        3: sigma_x * sp.diag(a3, b3),
        4: sigma_x * sp.diag(a4, b4),
    }
    inverses = {index: matrix.inv() for index, matrix in matrices.items()}
    eq120_indices = sorted(
        (n, k, m)
        for n, k, m in itertools.product(range(1, 5), repeat=3)
        if m != n and k < min(m, n)
    )
    eq120_zero = all(
        _zero_matrix(
            matrices[n] * inverses[k] * matrices[m] - matrices[m] * inverses[k] * matrices[n]
        )
        for n, k, m in eq120_indices
    )
    eq129_indices = sorted(itertools.permutations(range(1, 5), 4))
    eq129_zero = all(
        _zero_matrix(
            (matrices[m] * inverses[n] * matrices[ell] * inverses[k])
            - (matrices[ell] * inverses[k] * matrices[m] * inverses[n])
        )
        for m, n, ell, k in eq129_indices
    )
    left130 = matrices[1] * inverses[2]
    right130 = inverses[1] * matrices[2]
    eq130_zero = _zero_matrix(left130 * right130 - right130 * left130)
    witness12 = matrices[1] * matrices[2] - matrices[2] * matrices[1]
    witness23 = matrices[2] * matrices[3] - matrices[3] * matrices[2]

    equations = {
        "107": {
            "pdf_page": 27,
            "content": "A_n = T_m G_n G_m^-1 for a non-timid transition",
        },
        "108": {
            "pdf_page": 27,
            "content": "timid transition inclusion-exclusion in gregarious operators",
        },
        "112": {
            "pdf_page": 27,
            "content": "G_n^(0) = S_alpha Q_n S_alpha^-1",
        },
        "114": {
            "pdf_page": 27,
            "content": "G_n G_k^-1 G_m = G_m G_k^-1 G_n",
        },
        "120": {
            "pdf_page": 28,
            "content": "Q_n Q_k^-1 Q_m = Q_m Q_k^-1 Q_n",
        },
        "129": {
            "pdf_page": 29,
            "content": "[Q_m Q_n^-1, Q_l Q_k^-1] = 0",
        },
        "130": {
            "pdf_page": 29,
            "content": "[Q_1 Q_2^-1, Q_1^-1 Q_2] = 0",
        },
        "165": {
            "pdf_page": 35,
            "content": ("Q_1=a_1 sigma_1, Q_2=a_2 sigma_2, Q_3=a_3 sigma_1, Q_4=a_4 sigma_2"),
        },
    }
    restriction_lemma = {
        "statement": (
            "If an infinite CPOBC representation satisfies CPOBC, MSR, GC, "
            "and two-sided nonsingularity at every finite stage, its operators "
            "on sources of cardinality <=4 satisfy every corresponding finite "
            "axiom instance."
        ),
        "mechanical_checks": {
            "all_compiled_relation_stages_at_most_4": all(
                max(relation["stage"].values()) <= 4 for relation in compiled["relations"]
            ),
            "compiled_relation_count": len(compiled["relations"]),
            "MSR_source_count": len(compiled["MSR_operator_constraints"]),
            "relation_dependencies_record_nonsingularity": all(
                relation["invertibility_dependency"]["inverse_encoding"]
                == "METHOD_A_EXPLICIT_TWO_SIDED_INVERSE_VARIABLES"
                for relation in compiled["relations"]
            ),
        },
        "assumptions": [
            "the infinite representation uses the same finite-stage CPOBC semantics",
            "all transition operators needed by the restriction are nonsingular",
            "MSR and operator-level GC hold before restriction",
            "the compiled 641 records are finite instances, not a presentation of GC",
        ],
        "logical_status": ("CONDITIONAL_UNIVERSAL_INSTANTIATION_FOR_COMPILED_AXIOMS"),
        "no_go_lifting_status": (
            "NOT_AVAILABLE: no finite d=2 no-go was obtained and operator GC was not compiled"
        ),
    }

    return {
        "schema_version": "final-theory-cpobc-d2-phase0-v0.3.2",
        "paper": {
            "id": PAPER_ID,
            "local_file": PAPER_PDF,
            "expected_sha256": PAPER_SHA256,
            "observed_sha256": _sha256_file(paper),
            "hash_match": _sha256_file(paper) == PAPER_SHA256,
        },
        "pdf_visual_verification": {
            "method": (
                "Poppler 140 dpi page render followed by visual inspection; "
                "extracted text used only to locate pages"
            ),
            "pages_inspected": [16, 26, 27, 28, 29, 31, 35],
            "equations": equations,
            "inspection_status": "VISUALLY_CONFIRMED_THIS_RELEASE",
            "claim_boundary": (
                "The PDF confirms the displayed relations and Pauli ansatz "
                "scope; it does not prove the new project reductions."
            ),
        },
        "frozen_artifacts": {
            FROZEN_RELATIONS_PATH: {
                "expected_sha256": FROZEN_RELATIONS_SHA256,
                "observed_sha256": _sha256_file(frozen_relations),
                "hash_match": (_sha256_file(frozen_relations) == FROZEN_RELATIONS_SHA256),
            },
            FROZEN_D3_PATH: {
                "expected_sha256": FROZEN_D3_SHA256,
                "observed_sha256": _sha256_file(frozen_d3),
                "hash_match": (_sha256_file(frozen_d3) == FROZEN_D3_SHA256),
                "required_status": "UNRESOLVED strata frozen from v0.3.1",
            },
        },
        "F1_counts": {
            "expected": EXPECTED_FROZEN_COUNTS,
            "observed": frozen_counts,
            "exact_match": frozen_counts == EXPECTED_FROZEN_COUNTS,
        },
        "F4_R_commutation": {
            "identity": ("numerator([Q_1^-1 Q_n,Q_1^-1 Q_m]) = adj(Q_1)*cleared_Eq120(k=1)"),
            "assumption": "det(Q_1) != 0",
            "certificate_residual": _matrix_record(implication_residual),
            "verified": _zero_matrix(implication_residual),
        },
        "F4_monomial_family": {
            "definition": {
                "Q_1": "q1*sigma_x",
                "Q_n": "sigma_x*diag(a_n,b_n), n=2,3,4",
            },
            "eq120": {
                "admissible_index_count": len(eq120_indices),
                "all_residuals_zero": eq120_zero,
            },
            "eq129": {
                "admissible_index_count": len(eq129_indices),
                "all_residuals_zero": eq129_zero,
            },
            "eq130": {"all_residuals_zero": eq130_zero},
            "noncommutativity_witnesses": {
                "[Q_1,Q_2]": _matrix_record(witness12),
                "[Q_2,Q_3]": _matrix_record(witness23),
            },
            "full_641_relation_status": "UNASSESSED_NOT_A_REPRESENTATION",
        },
        "restriction_lemma": restriction_lemma,
        "source_classification": {
            "primary_literature": ("paper equations and the Pauli-proportional ansatz boundary"),
            "independent_project_derivation": (
                "R-family commutation identity and monomial necessary-relation witness"
            ),
            "unresolved": ("full finite d=2 representation and any infinite-system no-go"),
        },
        "passed": (
            _sha256_file(paper) == PAPER_SHA256
            and _sha256_file(frozen_relations) == FROZEN_RELATIONS_SHA256
            and _sha256_file(frozen_d3) == FROZEN_D3_SHA256
            and frozen_counts == EXPECTED_FROZEN_COUNTS
            and _zero_matrix(implication_residual)
            and eq120_zero
            and eq129_zero
            and eq130_zero
        ),
    }


def _production_s3_descriptor() -> dict[str, Any]:
    return {
        "stratum": "S3_SCALAR",
        "substitution": {
            "Q_2": "lambda_2*Q_1",
            "Q_3": "lambda_3*Q_1",
            "Q_4": "lambda_4*Q_1",
        },
        "checked_claim": "ANTICHAIN_Q_COMMUTATORS_ZERO_ONLY",
        "commutator_pairs": [
            [1, 2],
            [1, 3],
            [1, 4],
            [2, 3],
            [2, 4],
            [3, 4],
        ],
        "full_transition_system_status": ("UNASSESSED_GENERATOR_REDUCTION_INCOMPLETE"),
    }


def d2_strata_manifest_v032() -> dict[str, Any]:
    """Certify the S1/S2/S3 cover without claiming stratum elimination."""

    alpha, beta, x, y, z, w = sp.symbols("alpha beta x y z w")
    pivot = sp.diag(alpha, beta)
    candidate = sp.Matrix([[x, y], [z, w]])
    s1_commutator = pivot * candidate - candidate * pivot
    nilpotent = sp.Matrix([[0, 1], [0, 0]])
    s2_commutator = nilpotent * candidate - candidate * nilpotent
    s2_normal = x * sp.eye(2) + y * nilpotent

    q11, q12, q21, q22 = sp.symbols("q11 q12 q21 q22")
    lambda2, lambda3, lambda4 = sp.symbols("lambda_2 lambda_3 lambda_4")
    q1 = sp.Matrix([[q11, q12], [q21, q22]])
    q_values = {
        1: q1,
        2: lambda2 * q1,
        3: lambda3 * q1,
        4: lambda4 * q1,
    }
    s3_commutators_zero = all(
        _zero_matrix(q_values[left] * q_values[right] - q_values[right] * q_values[left])
        for left, right in itertools.combinations(range(1, 5), 2)
    )
    descriptor = _production_s3_descriptor()
    strata = [
        {
            "stratum": "S1_DISTINCT_EIGENVALUE",
            "cover_condition": ("some R_n has nonzero characteristic discriminant"),
            "normal_form": "all R_n diagonal in an eigenbasis of the pivot",
            "symbolic_centralizer_commutator": _matrix_record(s1_commutator),
            "proof_obligation_status": ("PASS_ON_OPEN_CHART_alpha_minus_beta_NONZERO"),
            "residual_gauge_group": ("invertible diagonal torus, with eigenline swap if unordered"),
            "gauge_completeness": (
                "follows from the two one-dimensional pivot eigenspaces; "
                "no Phase-3 gauge fixing was executed"
            ),
            "elimination_status": "NOT_EXECUTED_PHASE1_EQ112_GC_BLOCKED",
        },
        {
            "stratum": "S2_COMMON_NILPOTENT",
            "cover_condition": ("all R_n have repeated eigenvalue and at least one is nonscalar"),
            "normal_form": "R_n=lambda_n*I+mu_n*N, N=E12, N^2=0",
            "symbolic_centralizer_commutator": _matrix_record(s2_commutator),
            "centralizer_solution": _matrix_record(s2_normal),
            "proof_obligation_status": "PASS_EXACT_2X2_CENTRALIZER",
            "residual_gauge_group": ("N stabilizer {a*I+b*N | a != 0}"),
            "gauge_completeness": (
                "a nonzero square-zero 2x2 map has one Jordan block; "
                "no Phase-3 gauge fixing was executed"
            ),
            "elimination_status": "NOT_EXECUTED_PHASE1_EQ112_GC_BLOCKED",
        },
        {
            "stratum": "S3_SCALAR",
            "cover_condition": "every R_n is scalar",
            "normal_form": "R_n=lambda_n*I and Q_n=lambda_n*Q_1",
            "antichain_commutators_zero": s3_commutators_zero,
            "semantic_descriptor": descriptor,
            "semantic_descriptor_sha256": _stable_hash(descriptor),
            "proof_obligation_status": ("PASS_FOR_ANTICHAIN_Q_COMMUTATORS_ONLY"),
            "residual_gauge_group": "GL(2)",
            "gauge_completeness": (
                "scalar ratios are similarity-invariant; no Phase-3 gauge fixing was executed"
            ),
            "full_transition_commutativity": ("UNRESOLVED_OTHER_TRANSITIONS_MAY_BE_NONCOMMUTATIVE"),
            "elimination_status": "NOT_EXECUTED_PHASE1_EQ112_GC_BLOCKED",
        },
    ]
    return {
        "schema_version": "final-theory-cpobc-d2-strata-v0.3.2",
        "field": "algebraically closed characteristic-zero field (target C)",
        "family": ["R_2", "R_3", "R_4"],
        "assumptions": [
            "Q_1 is invertible",
            "R_n=Q_1^-1 Q_n",
            "the k=1 Eq.(120) instances imply pairwise commutation",
        ],
        "exhaustiveness_proof": {
            "predicate_partition": (
                "some discriminant is nonzero (S1); otherwise some R is "
                "nonscalar (S2); otherwise all R are scalar (S3)"
            ),
            "single_matrix_identity": ("(A-tr(A)/2 I)^2=(tr(A)^2-4 det(A))/4 I"),
            "commuting_nilpotents_proportional_in_d2": (
                "after a nonzero nilpotent is conjugated to E12, its "
                "centralizer consists of xI+yE12"
            ),
            "strata_are_exhaustive": True,
            "strata_are_disjoint_by_predicate": True,
        },
        "strata": strata,
        "coverage": {
            "declared_strata": 3,
            "exhaustiveness_lemma_passed": True,
            "fully_eliminated_strata": 0,
            "representation_witness_strata": 0,
        },
        "unresolved_components": [
            "full transition-system noncommutativity in S3",
            "S1 polynomial elimination",
            "S2 polynomial elimination",
            "S3 full-transition elimination",
            "similarity deduplication of any future solutions",
        ],
        "verdict": VERDICT_PARTIAL,
    }


def _load_independent_oracle(root: Path) -> dict[str, Any]:
    oracle_path = root / "oracle" / "cpobc_d2_v032_oracle.py"
    spec = importlib.util.spec_from_file_location(
        "cpobc_d2_v032_independent_oracle_release",
        oracle_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load independent oracle: {oracle_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    payload: dict[str, Any] = module.build_oracle_certificate()
    return payload


def classification_result_v032(
    root: Path,
    *,
    reduction: dict[str, Any] | None = None,
    phase0: dict[str, Any] | None = None,
    oracle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    reduction_result = reduction or generator_reduction_v032()
    phase0_result = phase0 or phase0_exact_audit_v032(root)
    strata = d2_strata_manifest_v032()
    oracle_result = oracle or _load_independent_oracle(root)
    production_s3_digest = strata["strata"][2]["semantic_descriptor_sha256"]
    oracle_s3_digest = oracle_result["independent_s3_digest_certificate"][
        "semantic_descriptor_sha256"
    ]
    limited_digest_match = production_s3_digest == oracle_s3_digest
    phase3_strata = [
        {
            "stratum": item["stratum"],
            "status": item["elimination_status"],
            "solution_found": False,
            "no_go_certificate": False,
            "timeout": False,
            "reason": (
                "20 Eq.(112) generator reductions and operator-level GC "
                "identities remain unavailable"
            ),
        }
        for item in strata["strata"]
    ]
    unresolved = [
        "20 non-antichain gregarious generators lack Eq.(112) path certificates",
        "operator-level GC constraints are not compiled",
        "96 d=2 scalar generator entries exceed the declared 40-variable redesign gate",
        "S1, S2, and S3 full polynomial eliminations were not executed",
        "determinant saturation for every reduced transition expression",
        "exact noncommutativity branches for the full transition assignment",
        "full independent Phase-3 oracle (only an S3 antichain digest was matched)",
        "n<=4 vector measure construction",
        "any infinite-system representation or no-go",
    ]
    found_requirements = {
        "641_relations_exact": False,
        "all_required_transitions_invertible": False,
        "exact_noncommutativity": False,
        "similarity_nonduplicate": False,
        "outside_Pauli_proportional_ansatz": False,
        "n_le_4_vector_measure_constructible": False,
    }
    no_go_requirements = {
        "general_invertible_2x2_cover": False,
        "S1_S2_S3_all_processed": False,
        "similarity_gauge_complete": False,
        "exact_elimination_certificate_each_stratum": False,
        "not_Pauli_limited": True,
        "conditional_infinite_restriction_lemma_available": True,
        "finite_no_go_available_for_lifting": False,
    }
    verdict = VERDICT_PARTIAL
    assert verdict in ALLOWED_VERDICTS
    assert unresolved
    return {
        "schema_version": "final-theory-cpobc-d2-classification-v0.3.2",
        "branch": BRANCH,
        "source_commit": SOURCE_COMMIT,
        "code_commit": "UNCOMMITTED_WORKTREE",
        "paper_versions": [
            {
                "id": PAPER_ID,
                "version": "v1",
                "local_file": PAPER_PDF,
                "source_hash_sha256": PAPER_SHA256,
            }
        ],
        "source_hashes": [
            {"path": PAPER_PDF, "sha256": PAPER_SHA256},
            {
                "path": FROZEN_RELATIONS_PATH,
                "sha256": FROZEN_RELATIONS_SHA256,
            },
            {"path": FROZEN_D3_PATH, "sha256": FROZEN_D3_SHA256},
        ],
        "literature_classification": {
            "paper_equations_107_130": "LITERATURE_LOCKED",
            "paper_d2_Pauli_proportional_ansatz": "LITERATURE_LOCKED_BOUNDARY",
            "general_d2_CPOBC_classification": "OPEN_TARGET",
        },
        "assumptions": [
            "finite maximal-element sequential growth",
            "CPOBC transition operators are nonsingular",
            "noncommutative multiplication order is preserved",
            "all exact claims use characteristic zero",
            "S1/S2/S3 spectral cover is stated over an algebraically closed field",
        ],
        "dimension": 2,
        "field": "C / characteristic-zero symbolic extension",
        "Jordan_stratum": "S1_S2_S3_DECLARED_EXHAUSTIVE_NOT_ELIMINATED",
        "jordan_stratum": "S1_S2_S3_DECLARED_EXHAUSTIVE_NOT_ELIMINATED",
        "ansatz": "GENERAL_Q1_RESERVED; FULL_TRANSITION_SYSTEM_NOT_REDUCED",
        "relation_count": EXPECTED_FROZEN_COUNTS["compiled_cross_stage_relations"],
        "solver": (
            "deterministic finite-causet reduction and SymPy exact identities; "
            "no dense full-system Groebner elimination"
        ),
        "solver_version": {
            "python": sys.version.split()[0],
            "sympy": sp.__version__,
            "platform": platform.platform(),
        },
        "random_seed": None,
        "exact_numeric_distinction": {
            "exact": (
                "integer word algebra, rational-function matrix identities, "
                "SHA-256 artifact and semantic digests"
            ),
            "numeric": "none accepted as proof",
        },
        "completeness_scope": (
            "Phase 0, Eq.(107)/(108) occurrence reduction, and S1/S2/S3 "
            "coverage are exact; Eq.(112), operator GC, and every Phase-3 "
            "stratum elimination remain incomplete"
        ),
        "time_limit": {
            "finite_reduction": "deterministic n<=4 cardinality cap",
            "symbolic_elimination": ("not launched after the explicit >40-variable strategy gate"),
        },
        "memory_limit": {
            "policy": ("word-digest inventory only; no dense 96-entry full ideal"),
            "os_enforced": False,
        },
        "phase0": phase0_result,
        "generator_reduction_summary": {
            "counts": reduction_result["counts"],
            "equivalence_obligations": reduction_result["equivalence_obligations"],
            "phase3_strategy_gate": reduction_result["phase3_strategy_gate"],
            "verdict": reduction_result["verdict"],
        },
        "d2_strata": strata,
        "phase3_elimination": {
            "strata": phase3_strata,
            "full_polynomial_inventory": {
                "Bell_word_equations": 783,
                "d2_Bell_entry_equations_before_reduction": 783 * 4,
                "Bell_operator_residuals_after_reduction": (
                    reduction_result["counts"]["Bell_residual_constraints_after_reduction"]
                ),
                "d2_Bell_entry_residuals_after_reduction": (
                    reduction_result["counts"]["Bell_residual_constraints_after_reduction"] * 4
                ),
                "MSR_operator_constraints": 24,
                "d2_MSR_entry_equations": 24 * 4,
                "generator_matrix_count_after_eq107_eq108": 24,
                "generator_scalar_entry_count_d2": 96,
                "inverse_matrix_entry_variables": (
                    "0 planned under adjugate/determinant saturation; "
                    "96 additional if explicit inverses are introduced"
                ),
                "determinant_saturation_status": "NOT_CONSTRUCTED",
                "GC_operator_equations": "NOT_COMPILED",
                "transition_determinant_predicates": 165,
            },
            "groebner_or_primary_decomposition_runs": 0,
            "numerical_candidate_runs": 0,
            "reason": (
                "The declared strategy gate requires redesign above 40 d=2 "
                "scalar unknowns, and the GC/Eq.(112) system is incomplete."
            ),
        },
        "independent_oracle_gate": {
            "oracle_role": oracle_result["implementation_role"],
            "oracle_passed_within_scope": oracle_result["passed"],
            "production_s3_semantic_digest": production_s3_digest,
            "oracle_s3_semantic_digest": oracle_s3_digest,
            "limited_digest_match": limited_digest_match,
            "G1_status": (
                "PARTIAL_ONLY: S3 antichain-Q digest reproduced; no full "
                "Phase-3 decision exists to reproduce"
            ),
        },
        "verdict_requirements": {
            VERDICT_FOUND: found_requirements,
            VERDICT_NO_GO: no_go_requirements,
            VERDICT_PARTIAL: {
                "triggered": True,
                "reason": (
                    "At least one mandatory Phase-4 condition is unmet; in "
                    "fact the full Phase-3 eliminations were not executed."
                ),
            },
        },
        "frozen_v031_d3": {
            "path": FROZEN_D3_PATH,
            "sha256": FROZEN_D3_SHA256,
            "status": "FROZEN_UNRESOLVED_NOT_MODIFIED",
        },
        "claim_separation": {
            "primary_literature_known": [
                "paper Eqs.(107),(108),(112),(114),(120),(129),(130)",
                "paper Eq.(165) is a Pauli-proportional d=2 ansatz",
            ],
            "independent_project_derivations": [
                "exact F4 monomial necessary-relation witness",
                "165-to-24 Eq.(107)/(108) occurrence reduction",
                "all 783 Bell words and 24 MSR constraints rewritten",
                "S1/S2/S3 antichain-ratio cover",
            ],
            "unresolved": unresolved,
        },
        "unresolved_components": unresolved,
        "certificate_hashes": [],
        "verdict": verdict,
        "passed": (
            phase0_result["passed"]
            and reduction_result["passed"]
            and strata["coverage"]["exhaustiveness_lemma_passed"]
            and limited_digest_match
            and verdict == VERDICT_PARTIAL
        ),
    }


def _classification_report(
    classification: dict[str, Any],
    reduction: dict[str, Any],
) -> str:
    counts = reduction["counts"]
    unresolved = "\n".join(f"- {item}" for item in classification["unresolved_components"])
    return f"""# Final-Theory Bench v0.3.2 - general d=2 CPOBC classification

Status: **`{classification["verdict"]}`**

## Result

This release does not establish either a noncommutative d=2 representation or
a complete d=2 no-go.  The mandatory verdict is therefore
`CPOBC_D2_PARTIAL`; it is not rounded up from a necessary-relation witness.

Phase 0 rechecked the source PDF and the frozen v0.3.1 inventory.  Paper
Eqs. (107), (108), (112), (114), (120), (129), (130), and the ansatz in
Eq. (165) were inspected on PDF pages 27-29 and 35.  The Pauli result is
ansatz-limited.  Independently, the monomial family passes every admissible
n<=4 instance of Eqs. (120), (129), and (130), but it has not passed the 641
compiled Bell relations, MSR, or GC and is not called a representation.

## Generator reduction

All {counts["occurrence_variables"]} transition occurrences were mapped
through Eqs. (107) and (108).  The map rewrites all
{counts["rewritten_word_equations"]} denominator-cleared Bell equations and
all {counts["rewritten_MSR_constraints"]} MSR constraints.  The MSR residuals
are retained exactly: {counts["MSR_free_word_identities_after_reduction"]}
become free-word identities, while
{counts["MSR_residual_constraints_after_reduction"]} remain constraints among
the reduced generators and are not silently discarded.
Of the {counts["rewritten_word_equations"]} Bell word equations,
{counts["Bell_free_word_identities_after_reduction"]} become free-word
identities and {counts["Bell_residual_constraints_after_reduction"]} remain
noncommutative constraints.

The safe reduced presentation still contains
{counts["independent_matrix_generators_after_eq107_eq108"]} causet-indexed
gregarious matrices, including {counts["antichain_Q_generators"]} antichain
Q generators.  Eq. (112) would have to reduce
{counts["eq112_unreduced_gregarious_generators"]} non-antichain generators
using atomisation paths.  Those paths and operator-level GC equations are not
encoded in the frozen compiler.  At d=2 the retained matrices contain
{counts["d2_scalar_unknowns_before_inverse_saturation_and_gauge"]} scalar
entries before determinant saturation and gauge, above the declared
40-variable redesign gate.  No dense full-system Gröbner basis was launched.

## d=2 strata

The commuting ratio family `R_n=Q_1^-1 Q_n` is exhaustively divided into:

- S1: a member has two distinct eigenvalues, hence the family is simultaneously
  diagonal in that member's eigenbasis;
- S2: every member has one eigenvalue and some member is nonscalar, hence all
  are `lambda_n I + mu_n N` for one common `N` with `N^2=0`;
- S3: every member is scalar, so `Q_n=lambda_n Q_1`.

The residual groups are respectively the diagonal torus with possible
eigenline swap, the stabilizer of `N=E12`, and `GL(2)`.  This proves the
coverage lemma only.  No stratum was eliminated, and S3 antichain
commutativity is not promoted to commutativity of all transition operators.

## Independent oracle

An implementation that imports none of the Phase-1 production code reproduced
the exact matrix identities, the monomial-family residuals, and the limited S3
antichain semantic digest.  This is a limited honesty check, not the requested
full Phase-3 oracle, because there is no completed Phase-3 decision to
reproduce.

## Restriction boundary

An infinite nonsingular representation satisfying CPOBC, MSR, and GC at every
stage necessarily restricts to the corresponding finite n<=4 axiom instances.
That conditional restriction lemma cannot lift a no-go here: no finite d=2
no-go was obtained, and the compiled artifact does not contain operator-level
GC.

## Unresolved

{unresolved}

The v0.3.1 d=3 strata manifest remains frozen with its unresolved status.
"""


def _research_note() -> str:
    return """# Final-Theory v0.3.2 d=2 frontier note - 2026-07-28

## Primary-literature facts

The local PDF for Srivastava and Surya, arXiv:2603.25503v1, was checked
visually rather than relying on extracted text.  Equations (107), (108),
(112), and (114) occur on PDF page 27; Eq. (120) on page 28; Eqs. (129) and
(130) on page 29; and the Pauli-proportional choice Eq. (165) on page 35.
Equation (165) fixes each Q_n to one of two individual Pauli directions.  It
does not classify a general invertible 2x2 representation.

The paper assumes nonsingular transition operators in the algebraic
development used here.  All project statements and the finite-restriction
lemma retain that assumption.

## Independent project derivations

With R_n=Q_1^-1 Q_n, the k=1 instance of Eq. (120) gives pairwise commuting
R_2, R_3, R_4.  A symbolic adjugate identity certifies this without floating
point arithmetic.  The monomial family

`Q_1=q_1 sigma_x`, `Q_n=sigma_x diag(a_n,b_n)`

passes every admissible n<=4 instance of Eqs. (120), (129), and (130) and has
exact nonzero commutator branches.  This is evidence that the general d=2
frontier is not closed by the paper's Pauli-proportional ansatz.  It is only a
necessary-relation witness.

Paper Eqs. (107) and (108) reduce every one of the 165 finite transition
occurrences to 24 causet-indexed gregarious matrices.  All MSR constraints are
rewritten; three become free-word identities and twenty-one remain exact
constraints among the reduced generators.  This is a project derivation, not
a statement quoted from the paper.

## Unresolved boundary

Twenty of the 24 gregarious matrices are attached to non-antichain causets.
Reducing them further by Eq. (112) requires explicit atomisation paths and
operator-level GC identities.  The frozen v0.3.1 compiler records only
combinatorial GC endpoint provenance, not those operator equations.
Consequently the current reduced d=2 presentation has 96 scalar matrix-entry
variables before determinant saturation and gauge.  No S1, S2, or S3
elimination was executed, no representation or no-go was certified, and no
vector measure was constructed.

The defensible release token is `CPOBC_D2_PARTIAL`.
"""


def write_cpobc_d2_v032_artifacts(
    root: Path,
    *,
    production_commit: str | None = None,
) -> dict[str, Path]:
    """Write the v0.3.2 results, certificates, report, and research note."""

    code_commit = production_commit or _git_head(root)
    if len(code_commit) != 40:
        raise ValueError("production_commit must be a full 40-character hash")
    phase0 = phase0_exact_audit_v032(root)
    reduction = generator_reduction_v032()
    oracle = _load_independent_oracle(root)
    classification = classification_result_v032(
        root,
        reduction=reduction,
        phase0=phase0,
        oracle=oracle,
    )
    freeze_pointer = (
        "artifact set is the child freeze commit of code_commit; "
        "the annotated release tag records both hashes"
    )
    for payload in (phase0, reduction, oracle, classification):
        payload["code_commit"] = code_commit
        payload["artifact_freeze_commit"] = freeze_pointer

    result_dir = root / "results"
    certificate_dir = root / "certificates" / "cpobc_d2"
    report_dir = root / "Final-Theory-Program" / "reports"
    note_dir = root / "references" / "notes"
    for directory in (result_dir, certificate_dir, report_dir, note_dir):
        directory.mkdir(parents=True, exist_ok=True)

    certificates = {
        certificate_dir / "v0.3.2_phase0_exact.json": phase0,
        certificate_dir / "v0.3.2_independent_oracle.json": oracle,
        certificate_dir / "v0.3.2_limited_s3_digest.json": {
            "code_commit": code_commit,
            "artifact_freeze_commit": freeze_pointer,
            "production": classification["independent_oracle_gate"][
                "production_s3_semantic_digest"
            ],
            "oracle": classification["independent_oracle_gate"]["oracle_s3_semantic_digest"],
            "match": classification["independent_oracle_gate"]["limited_digest_match"],
            "scope": "S3_ANTICHAIN_Q_COMMUTATORS_ONLY",
            "G1_status": classification["independent_oracle_gate"]["G1_status"],
        },
    }
    written: dict[str, Path] = {}
    for path, payload in certificates.items():
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written[path.name] = path

    certificate_hashes = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": _sha256_file(path),
        }
        for path in certificates
    ]
    reduction["certificate_hashes"] = certificate_hashes
    classification["certificate_hashes"] = certificate_hashes
    results = {
        result_dir / "v0.3.2_cpobc_generator_reduction.json": reduction,
        result_dir / "v0.3.2_cpobc_d2_classification.json": classification,
    }
    for path, payload in results.items():
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written[path.name] = path

    report_path = report_dir / "v0.3.2_cpobc_d2_classification.md"
    report_path.write_text(
        _classification_report(classification, reduction),
        encoding="utf-8",
    )
    written[report_path.name] = report_path

    note_path = note_dir / "final_theory_v0.3.2_d2_frontier_2026-07-28.md"
    note_path.write_text(_research_note(), encoding="utf-8")
    written[note_path.name] = note_path
    return written


# Stable public aliases following the v0.3.1 naming convention.
generator_reduction_v0_3_2 = generator_reduction_v032
d2_classification_v0_3_2 = classification_result_v032
