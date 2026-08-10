"""Eq. (120) collapses the 955 upper-stratum commutativity question to one scalar.

The commutator-span gates decided, pointwise, whether six independent linear
forms lie in a row space.  This module proves an exact algebraic reason those
six forms are never independent questions in the first place.

The already-certified source-native Eq. (120) provenance
(``results/v0.4.2_eq120_source_provenance.json``) gives, for ``1=k<m<n<=4``
and wherever ``Q_1`` is invertible,

    Q_n Q_1^{-1} Q_m = Q_m Q_1^{-1} Q_n.

On the upper stratum every ``Q_i`` is upper triangular, ``[[a_i,b_i],[0,d_i]]``.
Expanding the ``(0,1)`` entry of Eq. (120)'s identity for the star anchored at
``k=1`` gives, for each pair ``(m,n)`` from ``{2,3,4}``, a polynomial that this
module identifies exactly with the ``3x3`` minor

    E_mn = det [[a_1,d_1,b_1],[a_m,d_m,b_m],[a_n,d_n,b_n]].

Only two of the three minors ``E_23, E_24, E_34`` are independent: given
``a_1 d_4 - a_4 d_1 != 0``, solving ``E_23 = E_24 = 0`` for ``b_2, b_3`` in
terms of ``b_1, b_4`` makes ``E_34`` vanish identically as a polynomial
consequence, not an extra assumption.

The central lemma, proved here as an exact polynomial identity rather than
sampled at points, is that under that same substitution all six pairwise
commutators collapse to scalar multiples of one of them:

    c_ij = kappa_ij * Lambda,      Lambda := c_14 = (a_1-d_1) b_4 - (a_4-d_4) b_1,

with ``kappa_ij`` an explicit rational function of ``a,d`` alone (no ``b``).
Consequently, on the locus where Eq. (120)'s star holds and
``a_1 d_4 - a_4 d_1 != 0``, full pairwise commutativity of ``Q_1,...,Q_4`` is
equivalent to the single scalar condition ``Lambda = 0`` -- not to six
separate row-span decisions.

This does not decide whether ``Lambda`` is forced to vanish; it only proves
that the six-way question is one question.  It is cross-checked against the
already-certified numeric points of ``results/v0.4.2_955_second_diagonal_span.json``,
where every point had all six escapes equal to zero, exactly as this lemma
requires for ``Lambda=0`` at those points.

No Groebner, saturation, finite-field or numerical computation is performed;
the verification is exact polynomial algebra over ``QQ`` with symbolic
coefficients.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import sympy

from universe_lab.final_theory import source_native_955_commutator_span_v042 as span
from universe_lab.final_theory import source_native_955_second_diagonal_span_v042 as diag
from universe_lab.final_theory import source_native_955_slack_csg_tangent_v042 as tangent
from universe_lab.final_theory import source_native_955_slack_term_preflight_v042 as terms

EQ120_PATH = "results/v0.4.2_eq120_source_provenance.json"
SECOND_DIAGONAL_SPAN_PATH = diag.RESULT_PATH
SLACK_INVENTORY_PATH = span.SLACK_INVENTORY_PATH
MIXED_MANIFEST_PATH = span.MIXED_MANIFEST_PATH
RESULT_PATH = "results/v0.4.2_955_eq120_commutator_collapse.json"

SCHEMA = "final-theory-v042-955-eq120-commutator-collapse-v1"
VERDICT = "V042_955_EQ120_SIX_COMMUTATORS_COLLAPSE_TO_ONE_SCALAR_CERTIFIED"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON object required: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Part A: the symbolic collapse identity, proved once and for all
# ---------------------------------------------------------------------------


def _symbolic_matrix(a: sympy.Symbol, b: sympy.Symbol, d: sympy.Symbol) -> sympy.Matrix:
    return sympy.Matrix([[a, b], [0, d]])


def _eq120_star_entry(
    a: dict[int, sympy.Symbol],
    b: dict[int, sympy.Symbol],
    d: dict[int, sympy.Symbol],
    left: int,
    right: int,
) -> sympy.Expr:
    """The exact numerator of Eq. (120)'s (0,1) entry for the pair (left,right)."""

    q1_inverse = _symbolic_matrix(a[1], b[1], d[1]).inv()
    qm = _symbolic_matrix(a[left], b[left], d[left])
    qn = _symbolic_matrix(a[right], b[right], d[right])
    difference = (qn * q1_inverse * qm - qm * q1_inverse * qn)[0, 1]
    numerator, _denominator = sympy.fraction(sympy.cancel(difference))
    return sympy.expand(numerator)


def _prove_collapse() -> dict[str, Any]:
    a = {i: sympy.Symbol(f"a{i}") for i in (1, 2, 3, 4)}
    d = {i: sympy.Symbol(f"d{i}") for i in (1, 2, 3, 4)}
    b = {i: sympy.Symbol(f"b{i}") for i in (1, 2, 3, 4)}

    determinant_minor = sympy.Matrix(
        [[a[1], d[1], b[1]], [a[2], d[2], b[2]], [a[3], d[3], b[3]]]
    ).det()
    e23 = _eq120_star_entry(a, b, d, 2, 3)
    if sympy.expand(e23 - determinant_minor) != 0:
        raise AssertionError("Eq120's (0,1) entry is not the claimed 3x3 minor")

    e24 = _eq120_star_entry(a, b, d, 2, 4)
    solved = sympy.solve([e23, e24], [b[2], b[3]], dict=True)
    if len(solved) != 1:
        raise AssertionError("the Eq120 star did not have a unique linear solution for b2,b3")
    substitution = solved[0]
    if set(substitution) != {b[2], b[3]}:
        raise AssertionError("the Eq120 star solution did not determine exactly b2 and b3")

    e34 = _eq120_star_entry(a, b, d, 3, 4).subs(substitution)
    if sympy.simplify(e34) != 0:
        raise AssertionError("E_34 is not an automatic consequence of E_23 and E_24")

    values = dict(b)
    values[2] = substitution[b[2]]
    values[3] = substitution[b[3]]
    lambda_expr = sympy.simplify((a[1] - d[1]) * values[4] - (a[4] - d[4]) * values[1])
    closed_form = a[1] * values[4] - a[4] * values[1] + values[1] * d[4] - values[4] * d[1]
    if sympy.expand(lambda_expr - closed_form) != 0:
        raise AssertionError("Lambda does not match its declared closed form")

    denominator = a[1] * d[4] - a[4] * d[1]
    coefficients: dict[tuple[int, int], sympy.Expr] = {}
    for i in (1, 2, 3, 4):
        for j in range(i + 1, 5):
            c_ij = sympy.simplify((a[i] - d[i]) * values[j] - (a[j] - d[j]) * values[i])
            ratio = sympy.simplify(sympy.cancel(c_ij / lambda_expr))
            residual = sympy.expand(c_ij - ratio * lambda_expr)
            if residual != 0:
                raise AssertionError(f"c_{i}{j} is not an exact multiple of Lambda")
            cleared = sympy.expand(ratio * denominator)
            if not cleared.is_polynomial(*a.values(), *d.values()):
                raise AssertionError(f"the collapse coefficient for ({i},{j}) is not polynomial")
            coefficients[(i, j)] = cleared

    if coefficients[(1, 4)] != denominator:
        raise AssertionError("c_14 must equal Lambda exactly (unit coefficient)")

    return {
        "symbols": {"a": a, "d": d, "b": b},
        "determinant_minor_identity_confirmed": True,
        "b2_solution": sympy.simplify(substitution[b[2]]),
        "b3_solution": sympy.simplify(substitution[b[3]]),
        "e34_is_automatic": True,
        "lambda_expr": lambda_expr,
        "denominator": denominator,
        "coefficients_times_denominator": coefficients,
    }


# ---------------------------------------------------------------------------
# Part B: cross-check against the already-certified numeric points
# ---------------------------------------------------------------------------


def _lambda_at_point(
    root: Path,
    slack: dict[str, Any],
    mixed: dict[str, Any],
    first: dict[str, Any],
    second: dict[str, Any],
) -> tuple[Any, dict[int, Any]]:
    """Recompute Lambda=c_14 at a concrete point, reusing the diagonal-span machinery."""

    names: list[str] = []
    matrices, _states, _expansion = terms._compile_matrices(slack, names)
    index_of = {name: index for index, name in enumerate(names)}
    representative_to_orbit = {
        str(record["representative_occurrence_id"]): str(record["orbit_id"])
        for record in slack["operator_namespace"]["orbit_inventory"]
    }
    timid = {
        str(record["timid_orbit_representative"]) for record in slack["timid_slack_recurrences"]
    }
    non_timid = sorted(set(matrices) - timid)
    canonical_paths = {
        str(record["source_id"]): list(record["operator_word_later_on_left"])
        for record in slack["source_state_recurrence"]["canonical_paths"]
    }
    timid_representative = {
        str(record["source_id"]): str(record["timid_orbit_representative"])
        for record in slack["timid_slack_recurrences"]
    }
    reduction = _load(root / "results/v0.3.2_cpobc_generator_reduction.json")

    def characters(couplings: list[int]) -> dict[str, Any]:
        by_orbit = span._characters(reduction, [Fraction(value) for value in couplings])
        return {
            representative: by_orbit[orbit]
            for representative, orbit in representative_to_orbit.items()
        }

    first_characters = characters(first["couplings"])
    if "constant" in second:
        second_characters = dict.fromkeys(first_characters, Fraction(second["constant"]))
    else:
        second_characters = characters(second["couplings"])

    assignment = [Fraction(0)] * len(names)
    for representative in non_timid:
        assignment[index_of[f"A:{representative}:00"]] = first_characters[representative]
        assignment[index_of[f"A:{representative}:11"]] = second_characters[representative]
    for record in slack["timid_slack_recurrences"]:
        source_id = str(record["source_id"])
        product = Fraction(1)
        for symbol in canonical_paths[source_id]:
            product *= first_characters[terms._operator(symbol)]
        base = Fraction(1)
        for operator, coefficient in zip(
            record["non_timid_orbit_representatives"],
            record["non_timid_coefficients"],
            strict=True,
        ):
            base -= int(coefficient) * second_characters[str(operator)]
        target = second_characters[timid_representative[source_id]]
        assignment[index_of[f"u:{source_id}:0"]] = Fraction(0)
        assignment[index_of[f"u:{source_id}:1"]] = (target - base) / product

    q_representatives, _q_records = tangent._q_mapping(slack, mixed)
    ad: dict[int, tuple[Any, Any, Any]] = {}
    for stage, representative in q_representatives.items():
        a_value = assignment[index_of[f"A:{representative}:00"]]
        d_value = assignment[index_of[f"A:{representative}:11"]]
        b_value = assignment[index_of[f"A:{representative}:01"]]
        ad[stage] = (a_value, d_value, b_value)

    a1, d1, b1 = ad[1]
    a4, d4, b4 = ad[4]
    lambda_value = (a1 - d1) * b4 - (a4 - d4) * b1
    return lambda_value, ad


def compile_eq120_collapse_v042(root: Path) -> dict[str, Any]:
    """Prove the six-to-one collapse and cross-check it against certified points."""

    root = root.resolve()
    paths = {
        EQ120_PATH: root / EQ120_PATH,
        SECOND_DIAGONAL_SPAN_PATH: root / SECOND_DIAGONAL_SPAN_PATH,
        SLACK_INVENTORY_PATH: root / SLACK_INVENTORY_PATH,
        MIXED_MANIFEST_PATH: root / MIXED_MANIFEST_PATH,
    }
    eq120 = _load(paths[EQ120_PATH])
    second_diagonal = _load(paths[SECOND_DIAGONAL_SPAN_PATH])
    slack = _load(paths[SLACK_INVENTORY_PATH])
    mixed = _load(paths[MIXED_MANIFEST_PATH])
    for name, artifact in ((SLACK_INVENTORY_PATH, slack), (MIXED_MANIFEST_PATH, mixed)):
        if artifact.get("semantic_digest_sha256") != terms._semantic_digest(artifact):
            raise AssertionError(f"{name} is not at its frozen semantic digest")
    if eq120.get("verdict") != "V042_EQ120_SOURCE_NATIVE_PROVENANCE_PROVED":
        raise AssertionError("the Eq120 source-native provenance predecessor is not certified")
    if second_diagonal.get("semantic_digest_sha256") != terms._semantic_digest(second_diagonal):
        raise AssertionError(f"{SECOND_DIAGONAL_SPAN_PATH} is not at its frozen semantic digest")

    proof = _prove_collapse()

    cross_checks = []
    label_to_construction = {
        "constant_1_control": ({"couplings": [1, 1, 1, 1, 1]}, {"constant": "1"}),
        "constant_2": ({"couplings": [1, 1, 1, 1, 1]}, {"constant": "2"}),
        "two_character_1_2_3_5_7": (
            {"couplings": [1, 1, 1, 1, 1]},
            {"couplings": [1, 2, 3, 5, 7]},
        ),
    }
    escapes_by_label = {
        record["label"]: record["escapes"] for record in second_diagonal["evaluated_points"]
    }
    for label, (first, second) in label_to_construction.items():
        if label not in escapes_by_label:
            raise AssertionError(f"the second-diagonal span predecessor no longer has {label}")
        lambda_value, ad_values = _lambda_at_point(root, slack, mixed, first, second)
        matches_zero_escapes = (lambda_value == 0) == (escapes_by_label[label] == 0)
        if not matches_zero_escapes:
            raise AssertionError(
                f"Lambda={lambda_value} disagrees with the recorded escape count at {label}"
            )
        cross_checks.append(
            {
                "label": label,
                "lambda_value": str(lambda_value),
                "lambda_is_zero": lambda_value == 0,
                "predecessor_escapes": escapes_by_label[label],
                "consistent": True,
            }
        )
    if not all(record["lambda_is_zero"] for record in cross_checks):
        raise AssertionError("a cross-checked point has nonzero Lambda; the lemma still holds "
                              "but this would mean that point is a witness candidate")

    coefficient_table = {
        f"{i}{j}": str(sympy.factor(value))
        for (i, j), value in proof["coefficients_times_denominator"].items()
    }

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "scope": {
            "finite_source_stages": "n<=4",
            "dimension": 2,
            "field": "QQ (symbols), QQ (numeric cross-check)",
            "identification_mode": "ON_QUOTIENT",
            "locus": "upper stratum, Q_1 invertible, a_1 d_4 - a_4 d_1 != 0",
        },
        "source_artifact_sha256": {path: _sha256(value) for path, value in paths.items()},
        "predecessor_binding": {
            "kind": "CANONICAL_JSON_SEMANTIC_DIGEST_AND_VERDICT",
            EQ120_PATH: {
                "verdict": eq120["verdict"],
                "semantic_digest_sha256": eq120.get("semantic_digest_sha256"),
            },
            SECOND_DIAGONAL_SPAN_PATH: second_diagonal["semantic_digest_sha256"],
            SLACK_INVENTORY_PATH: slack["semantic_digest_sha256"],
            MIXED_MANIFEST_PATH: mixed["semantic_digest_sha256"],
        },
        "eq120_star_identity": {
            "statement": "Q_n Q_1^{-1} Q_m = Q_m Q_1^{-1} Q_n for 1=k<m<n<=4",
            "already_proved_in": EQ120_PATH,
            "matrix_0_1_entry_equals_3x3_minor": True,
            "minor_definition": "det[[a_1,d_1,b_1],[a_m,d_m,b_m],[a_n,d_n,b_n]]",
        },
        "star_rank_reduction": {
            "raw_relations": ["E_23", "E_24", "E_34"],
            "independent_relations": 2,
            "e34_is_an_automatic_consequence_of_e23_and_e24": True,
            "b2_solution": str(proof["b2_solution"]),
            "b3_solution": str(proof["b3_solution"]),
            "nonsingularity_required": "a_1*d_4 - a_4*d_1 != 0",
        },
        "collapse_lemma": {
            "statement": (
                "Given the Eq120 k=1 star and a_1*d_4-a_4*d_1!=0, every pairwise commutator "
                "c_ij is an exact scalar multiple of Lambda := c_14 = (a_1-d_1)b_4-(a_4-d_4)b_1, "
                "with a coefficient depending only on a,d (never on b)."
            ),
            "lambda_definition": "c_14 = (a_1-d_1)*b_4 - (a_4-d_4)*b_1",
            "denominator": str(sympy.factor(proof["denominator"])),
            "coefficients_times_denominator": coefficient_table,
            "consequence": (
                "Full pairwise commutativity of Q_1,...,Q_4 on this locus is equivalent to the "
                "single scalar condition Lambda=0, not to six independent row-span decisions."
            ),
            "verified_as_exact_polynomial_identity": True,
            "verification_method": "symbolic substitution and residual cancellation, sympy exact",
        },
        "numeric_cross_check": {
            "role": (
                "Independent confirmation against already-certified points: every point in "
                "results/v0.4.2_955_second_diagonal_span.json with zero escapes must have "
                "Lambda=0, and this recomputes Lambda directly from the source-native "
                "construction rather than trusting the earlier span test."
            ),
            "points_checked": len(cross_checks),
            "records": cross_checks,
            "all_consistent": True,
        },
        "reframed_next_gate": (
            "Deciding forced commutativity on the upper stratum no longer needs six row-span "
            "tests.  It needs one: is Lambda=c_14 forced to zero by the core, or does there "
            "exist a nonsingular point of S (with the star's side condition) where Lambda!=0."
        ),
        "claim_boundary": [
            "This is an algebraic identity, not a proof that Lambda vanishes everywhere on S.",
            "The identity requires a_1*d_4-a_4*d_1!=0; points where this vanishes need a "
            "different anchor (e.g. k=1 with a different fourth index, or k=2) and are not "
            "covered here.",
            "The upper stratum is not the unrestricted 955 profile, and this says nothing "
            "about mixed points.",
            "No witness and no general obstruction is certified by this lemma alone.",
        ],
        "solver_status": {
            "symbolic_polynomial_identity_checks": 1,
            "Groebner_or_saturation_runs": 0,
            "finite_field_runs": 0,
            "numerical_runs": 0,
            "Sage_runs": 0,
            "solver_run": False,
        },
        "unrestricted_source_native_955_status": "OPEN",
        "commutativity_proved_for_full_profile": False,
        "witness_certified": False,
        "search_terminal": False,
        "passed": True,
        "verdict": VERDICT,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def write_eq120_collapse_v042(root: Path) -> Path:
    payload = compile_eq120_collapse_v042(root)
    destination = root / RESULT_PATH
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_eq120_collapse_v042(repository_root))
