"""SR2-V transverse determinant-zero loci: commutator kernel and nested loci.

`sr2v_transverse_cocycle_principal_open_v042` certifies four separate nonempty
principal opens ``Delta[branch]!=0`` on which the actual transverse cocycle
vanishes and ``Q1,...,Q4`` commute.  Its declared next gate is the analysis of
the four branch-specific determinant-zero boundaries.  This module opens that
gate from the inside and analyses explicit nested boundary loci carrying no
reachable-visible witness.

Four exact facts drive everything here.

1.  **Commutator template.**  The six upper-triangular ``Q`` commutator
    coefficients are universally

    ```text
    [Q_i,Q_j]_(12) = x_j*(a_i-b_i) - x_i*(a_j-b_j),
    ```

    Write ``C(delta)`` for these six linear forms and
    ``K_delta=ker C(delta)``.  A cocycle leaves ``Q1,...,Q4`` commuting exactly
    when its four ``Q`` coordinates lie in ``K_delta``.  If ``delta!=0``, then
    ``K_delta=span(delta)``; if ``delta=0``, then ``K_delta=Q^4``, not the zero
    span.  A reachable-visible witness exists at a base point if and only if the
    six commutator rows leave the row space there, that is
    ``rank[M;C(delta)]>rank M``.  Vanishing of a determinant is by itself **not**
    sufficient: the determinant-zero locus is where the principal-open argument
    stops, not where a witness appears.

2.  **Coboundary direction.**  Substituting ``x_e=beta_e:=a_e-b_e`` gives

    ```text
    [[a_e,a_e-b_e],[0,b_e]] = C*diag(a_e,b_e)*C^-1,   C=[[1,-1],[0,1]],
    ```

    so every word, inverses included, becomes ``C*diag(A_W,B_W)*C^-1`` and its
    upper-right entry is ``A_W-B_W``.  Hence ``beta`` satisfies every CPOBC,
    Eq. (113) and Eq. (139) row at *every* base point, and the six commutator
    forms annihilate it identically because its ``Q`` coordinates are ``delta``
    itself.  The fixed-vector GC and reachable-state MSR rows involve
    ``Omega=e_2``, are not conjugation invariant, and evaluate on ``beta`` to
    ``A_lhs-A_rhs`` and to ``(identity+sum coeff*a_e)*A_state``.  Therefore

    ```text
    beta in ker M  <=>  the upper character a also lies on the bottom scalar locus.
    ```

3.  **Full diagonal locus.**  ``E={a_e=b_e}`` is nonempty of dimension five,
    because the bottom scalar locus satisfies the 843-row operator monomial
    lattice and therefore sits inside the upper torus ``G_m^49``.  It lies in
    the larger equal-``Q``-spectrum locus ``Z_Q={delta_Q=0}``.  All six
    commutator rows vanish identically on the whole of ``Z_Q``, so that larger
    locus -- and hence ``E`` -- is witness-free independently of rank.  At three
    exact rational points of ``E`` the rank is 127 in all four branches and the
    five-dimensional kernel is exactly the tangent space of the bottom scalar
    locus, realised as the scalar deformations ``x_e=d b_e/d p``.  Those rank
    and kernel statements are certified pointwise, not proved stratum-wide.

4.  **Two scalar characters.**  ``S={a lies on the bottom scalar locus}`` is
    nonempty of dimension ten and meets ``delta_Q!=0``.  ``E`` is its full
    diagonal, but it is *not* all of the ``delta_Q=0`` part: the six-dimensional
    subfamily ``T`` in which the two characters have the same four couplings and
    differ only in external ``Q5`` also has ``delta_Q=0``.  By fact 2, ``beta``
    lies in the kernel at every point of ``S``, so the nullity is at least one on
    ``S\\E``.  At four exact rational samples in ``S`` with ``delta_Q!=0``, the
    rank is 130 in all four branches and the kernel is exactly
    ``span(beta,e_Q5)``; both directions commute.  At one exact point of
    ``T\\E``, all four ranks are instead 127 and the kernel is the
    five-dimensional tangent space of the upper bottom-character locus.  The
    whole of ``T`` is witness-free because ``delta_Q=0``.  Rank constancy and
    witness freedom on the remaining ``delta_Q!=0`` part of ``S`` are not
    claimed.

The module also repairs a reuse limitation.  The shipped ``_eq139_row``
hardcodes the normalized ``torus._csg`` bottom character, so the printed-strict
branches could not be evaluated away from ``t=(1,1,1,1)``.  A general-bottom
builder is supplied and pinned to the shipped one at the normalized point.  That
repair is what lets the four splitting principal opens be certified over
non-normalized bottom characters for the first time.

One further point is recorded deliberately as a warning.  At an explicit
degenerate point off the two-scalar locus, ``beta`` is not in the kernel at all,
the kernel is *not* contained in ``span(beta,e_Q5)``, and yet every commutator
form still vanishes on the whole kernel.  At that point ``delta_Q!=0`` and the
kernel's ``Q`` coordinates land on ``span(delta_Q)``.  So the invariant a
successor search must decide is whether the ``Q``-projection of ``ker M`` lies
in ``K_delta=ker C(delta_Q)``, not the coboundary span.

This is a classification of the universal commutator kernel together with exact
results on nested loci and a bounded deterministic scan.  It does not solve the
four determinant-zero loci, does not stratify the whole degeneracy locus, does
not obstruct the transverse chart, does not touch the pair/triple-irreducible or
aligned branches or the state-native D12 manifest, and does not issue an SR2-V
terminal.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from fractions import Fraction
from math import comb
from pathlib import Path
from typing import Any

import sympy as sp

from universe_lab.final_theory import sr2v_bottom_msr_global_csg_v042 as bottom_global
from universe_lab.final_theory import sr2v_scalar_lattice_v042 as lattice
from universe_lab.final_theory import sr2v_transverse_cocycle_principal_open_v042 as transverse
from universe_lab.final_theory import weak_d2_visible_torus_scout_v042 as torus
from universe_lab.final_theory.weak_d2_visible_torus_scout_v042 import (
    maximal_elements_in_subset,
)

RESULT_PATH = "results/v0.4.2_sr2v_transverse_determinant_zero_locus.json"

SCHEMA = "final-theory-v042-sr2v-transverse-determinant-zero-locus-v3"
VERDICT = (
    "SR2V_TRANSVERSE_COMMUTATOR_KERNEL_COBOUNDARY_AND_NESTED_DEGENERACY_LOCI_CERTIFIED_NONTERMINAL"
)
SEARCH_TERMINAL = "NOT_A_SEARCH_TERMINAL_NESTED_DEGENERACY_LOCI_AND_BOUNDED_SCAN_ONLY"

BRANCH_SPECS = {
    transverse.DERIVED_STRICT: (torus.EQ113_DERIVED, torus.EQ139_STRICT),
    transverse.DERIVED_COMPLETED: (torus.EQ113_DERIVED, torus.EQ139_COMPLETED),
    transverse.LITERAL_STRICT: (torus.EQ113_LITERAL, torus.EQ139_STRICT),
    transverse.LITERAL_COMPLETED: (torus.EQ113_LITERAL, torus.EQ139_COMPLETED),
}

#: Row blocks of the 1,187-row joint inventory, in build order.
ROW_BLOCKS = (
    ("CPOBC", 0, 783),
    ("Eq113_derived", 783, 808),
    ("Eq113_literal", 808, 833),
    ("Eq139_completed", 833, 843),
    ("fixed_vector_GC_basis", 843, 1163),
    ("reachable_state_MSR", 1163, 1187),
)
CONJUGATION_INVARIANT_BLOCKS = ("CPOBC", "Eq113_derived", "Eq113_literal", "Eq139_completed")

BOTTOM_PARAMETERS = ("t1", "t2", "t3", "t4", "q5")

NORMALIZED_COUPLINGS = (Fraction(1), Fraction(1), Fraction(1), Fraction(1))
NORMALIZED_Q5 = Fraction(1, 32)

#: Exact rational points of the bottom scalar locus sampling the stratum ``a=b``.
EQUAL_EIGENVALUE_SAMPLES = (
    (NORMALIZED_COUPLINGS, NORMALIZED_Q5),
    ((Fraction(3), Fraction(5), Fraction(7), Fraction(11)), Fraction(13, 4)),
    ((Fraction(2, 3), Fraction(5, 7), Fraction(9, 4), Fraction(1, 6)), Fraction(7, 5)),
)

#: Reference bottom character for the two-scalar stratum and the scan.
REFERENCE_BOTTOM = ((Fraction(3), Fraction(5), Fraction(7), Fraction(11)), Fraction(13, 4))
Q5_ONLY_UPPER_Q5 = Fraction(17, 5)

#: Upper characters that are themselves bottom-locus characters, all different
#: from the reference bottom point.
BI_SCALAR_SAMPLES = (
    ((Fraction(2), Fraction(4), Fraction(6), Fraction(10)), Fraction(1, 3)),
    (NORMALIZED_COUPLINGS, NORMALIZED_Q5),
    ((Fraction(5), Fraction(2), Fraction(9), Fraction(4)), Fraction(3)),
    ((Fraction(1, 2), Fraction(1, 3), Fraction(1, 5), Fraction(1, 7)), Fraction(2)),
)

#: Exact non-normalized bottom characters carrying a full-rank upper torus point.
OFF_NORMALIZED_OPENS = (
    (
        "generic-upper-A",
        (Fraction(3), Fraction(5), Fraction(7), Fraction(11)),
        Fraction(13, 4),
        tuple(Fraction(2 + (index % 5), 1 + (index % 3)) for index in range(49)),
    ),
    (
        "generic-upper-B",
        (Fraction(2, 3), Fraction(5, 7), Fraction(9, 4), Fraction(1, 6)),
        Fraction(7, 5),
        tuple(Fraction(1 + (index % 7), 2 + (index % 4)) for index in range(49)),
    ),
)

#: Deterministic one-parameter families ``a=b*s^K[j]`` through the stratum ``a=b``.
SCAN_DIRECTIONS = (0, 7, 12, 13, 18, 20, 25, 26, 28, 33, 35, 42, 44, 45, 48)
SCAN_SCALARS = (Fraction(-2), Fraction(2), Fraction(3), Fraction(5))

#: The scan point used to show that ``span(beta,e_Q5)`` is not the right invariant.
COUNTEREXAMPLE_DIRECTION = 13
COUNTEREXAMPLE_SCALAR = Fraction(3)

EXPECTED_EQUAL_EIGENVALUE_RANK = 127
EXPECTED_BI_SCALAR_RANK = 130
EXPECTED_GENERIC_RANKS = {
    transverse.DERIVED_STRICT: 131,
    transverse.DERIVED_COMPLETED: 131,
    transverse.LITERAL_STRICT: 132,
    transverse.LITERAL_COMPLETED: 132,
}

SparseRow = dict[str, Fraction]
LowerCharacter = Callable[[int, Any, int], Fraction]


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


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return _digest(semantic)


# --------------------------------------------------------------------------- #
# the five-dimensional bottom scalar character, in closed form                  #
# --------------------------------------------------------------------------- #


def _lam(width: int, maximal: int, couplings: tuple[Fraction, ...]) -> Fraction:
    """``lam(width,maximal)=sum_k binomial(width-maximal,k-maximal)*t_k`` with ``t0=1``."""

    values = (Fraction(1), *couplings)
    return sum(
        (
            comb(width - maximal, index - maximal) * values[index]
            for index in range(maximal, width + 1)
        ),
        start=Fraction(0),
    )


def _lam_derivative(width: int, maximal: int, index: int) -> Fraction:
    """``d lam(width,maximal)/d t_index`` for ``index`` in ``1..4``."""

    if not maximal <= index <= width:
        return Fraction(0)
    return Fraction(comb(width - maximal, index - maximal))


def _shape(stage: int, relation: Any, precursor: int) -> tuple[int, int]:
    rows = tuple(int(row) for row in relation)
    return precursor.bit_count(), len(maximal_elements_in_subset(rows, precursor))


def bottom_character(couplings: tuple[Fraction, ...], q5: Fraction) -> LowerCharacter:
    """The finite-CSG bottom character ``b_e=lam(width,maximal)/lam(stage,0)``."""

    def lower(stage: int, relation: Any, precursor: int) -> Fraction:
        if stage == 5:
            return q5
        width, maximal = _shape(stage, relation, precursor)
        return _lam(width, maximal, couplings) / _lam(stage, 0, couplings)

    return lower


def bottom_point(
    context: torus.ScoutContext,
    lower: LowerCharacter,
) -> dict[str, Fraction]:
    """The 132 coordinates of one point of the bottom scalar locus."""

    point: dict[str, Fraction] = {}
    for occurrence, record in context.occurrence_records.items():
        variable = context.occurrence_variables[occurrence]
        value = lower(
            int(record["stage"]),
            record["source_relation_rows"],
            int(record["precursor_code"]),
        )
        if point.setdefault(variable, value) != value:
            raise AssertionError("the bottom character is not constant on an ON orbit")
    point[torus.Q5] = lower(5, (0,) * 5, 0)
    if len(point) != len(context.variables) or not all(point.values()):
        raise AssertionError("the bottom character left the scalar torus")
    return point


def _variable_signatures(context: torus.ScoutContext) -> dict[str, tuple[int, tuple, int]]:
    signatures: dict[str, tuple[int, tuple, int]] = {}
    for occurrence, record in context.occurrence_records.items():
        variable = context.occurrence_variables[occurrence]
        signatures.setdefault(
            variable,
            (
                int(record["stage"]),
                tuple(int(row) for row in record["source_relation_rows"]),
                int(record["precursor_code"]),
            ),
        )
    signatures[torus.Q5] = (5, (0,) * 5, 0)
    return signatures


def bottom_tangent_vectors(
    context: torus.ScoutContext,
    couplings: tuple[Fraction, ...],
    q5: Fraction,
) -> dict[str, tuple[Fraction, ...]]:
    """``d b_e/d p`` for ``p`` in ``{t1,t2,t3,t4,q5}``, in declared variable order."""

    signatures = _variable_signatures(context)
    tangents: dict[str, tuple[Fraction, ...]] = {}
    for index, name in enumerate(BOTTOM_PARAMETERS[:4], start=1):
        vector = []
        for variable in context.variables:
            stage, relation, precursor = signatures[variable]
            if stage == 5:
                vector.append(Fraction(0))
                continue
            width, maximal = _shape(stage, relation, precursor)
            numerator = _lam(width, maximal, couplings)
            denominator = _lam(stage, 0, couplings)
            vector.append(
                (
                    _lam_derivative(width, maximal, index) * denominator
                    - numerator * _lam_derivative(stage, 0, index)
                )
                / denominator**2
            )
        tangents[name] = tuple(vector)
    tangents["q5"] = tuple(
        Fraction(1) if variable == torus.Q5 else Fraction(0) for variable in context.variables
    )
    return tangents


# --------------------------------------------------------------------------- #
# general-bottom branch matrices                                                #
# --------------------------------------------------------------------------- #


def eq139_row(
    context: torus.ScoutContext,
    upper: dict[str, Fraction],
    lower: LowerCharacter,
    instance: tuple[int, int, int],
) -> SparseRow:
    """``transverse._eq139_row`` with the bottom character supplied, not hardcoded."""

    def transition(stage: int, relation_code: int, precursor: int) -> torus.TriangularLinear:
        variable = context.signature_variables[(stage, relation_code, precursor)]
        relation = torus._decode_relation(stage, relation_code)
        return torus._linear_matrix(
            upper[variable],
            lower(stage, relation, precursor),
            variable,
        )

    def q(stage: int) -> torus.TriangularLinear:
        variable = torus._q_variable(context, stage)
        return torus._linear_matrix(
            upper[variable],
            lower(stage, (0,) * stage, 0),
            variable,
        )

    stage, left_index, right_index = instance
    left_transition = transition(stage, 0, (1 << left_index) - 1)
    right_transition = transition(stage, 0, (1 << right_index) - 1)
    current_q = q(stage)
    next_q = q(stage + 1)
    left = torus._linear_word(
        (
            left_transition,
            right_transition,
            next_q,
            torus._linear_inverse(right_transition),
            torus._linear_inverse(current_q),
            right_transition,
        )
    )
    right = torus._linear_word(
        (
            right_transition,
            left_transition,
            next_q,
            torus._linear_inverse(left_transition),
            torus._linear_inverse(current_q),
            left_transition,
        )
    )
    return torus._operator_residual(left, right)


def branch_matrix(
    context: torus.ScoutContext,
    upper: dict[str, Fraction],
    lower: LowerCharacter,
    joint_rows: list[SparseRow],
    eq113_branch: str,
    eq139_domain: str,
) -> list[SparseRow]:
    """The shipped branch row inventory, rebuilt over an arbitrary bottom point."""

    rows = list(joint_rows[:783])
    eq113_range = range(783, 808) if eq113_branch == torus.EQ113_DERIVED else range(808, 833)
    rows.extend(joint_rows[index] for index in eq113_range)
    if eq139_domain not in (torus.EQ139_STRICT, torus.EQ139_COMPLETED):
        raise ValueError(f"unknown Eq139 domain: {eq139_domain}")
    # Both readings use the same general-bottom word builder.  Since the four
    # strict instances are a literal subset of the ten completed instances,
    # this makes Row(M_strict) <= Row(M_completed) transparent for each fixed
    # Eq. (113) reading instead of relying on the normalized joint inventory.
    for instance in torus._eq139_instances(eq139_domain):
        rows.append(eq139_row(context, upper, lower, instance))
    rows.extend(joint_rows[843:1187])
    expected = 1156 if eq139_domain == torus.EQ139_STRICT else 1162
    if len(rows) != expected:
        raise AssertionError("a general-bottom branch matrix has the wrong shape")
    return rows


def _rank(rows: list[SparseRow], variables: tuple[str, ...]) -> int:
    return int(transverse._tracked_row_echelon(rows, variables)["rank"])


def _apply(row: SparseRow, vector: dict[str, Fraction]) -> Fraction:
    return sum(
        (coefficient * vector.get(variable, Fraction(0)) for variable, coefficient in row.items()),
        start=Fraction(0),
    )


def _as_row(vector: dict[str, Fraction]) -> SparseRow:
    return {variable: value for variable, value in vector.items() if value}


def sample_point(
    context: torus.ScoutContext,
    upper: dict[str, Fraction],
    lower: LowerCharacter,
) -> dict[str, Any]:
    """Exact rank, commutator-augmented rank and ``delta`` data of one base point."""

    joint_rows, _counts, commutators, _paths = torus._linear_system(context, upper, lower)
    commutator_rows = list(commutators.values())
    delta = {
        stage: upper[torus._q_variable(context, stage)] - lower(stage, (0,) * stage, 0)
        for stage in (1, 2, 3, 4)
    }
    branches: dict[str, Any] = {}
    for branch_id, (eq113_branch, eq139_domain) in BRANCH_SPECS.items():
        rows = branch_matrix(context, upper, lower, joint_rows, eq113_branch, eq139_domain)
        rank = _rank(rows, context.variables)
        augmented = _rank(rows + commutator_rows, context.variables)
        branches[branch_id] = {
            "rank": rank,
            "nullity": len(context.variables) - rank,
            "rank_with_commutator_rows": augmented,
            "commutator_rows_leave_the_row_space": augmented > rank,
        }
    return {
        "joint_rows": joint_rows,
        "commutators": commutators,
        "delta_Q": {str(stage): str(value) for stage, value in delta.items()},
        "delta_Q_is_zero": not any(delta.values()),
        "all_six_commutator_rows_vanish_identically": not any(commutators.values()),
        "branches": branches,
        "any_branch_admits_a_visible_witness": any(
            branch["commutator_rows_leave_the_row_space"] for branch in branches.values()
        ),
    }


# --------------------------------------------------------------------------- #
# universal symbolic identities                                                 #
# --------------------------------------------------------------------------- #


def universal_commutator_identity() -> dict[str, Any]:
    """``[Q_i,Q_j]_(12)=x_j*(a_i-b_i)-x_i*(a_j-b_j)`` as a generic 2x2 identity."""

    a_i, b_i, x_i, a_j, b_j, x_j = sp.symbols("a_i b_i x_i a_j b_j x_j", nonzero=True)

    def matrix(upper_left: Any, coordinate: Any, lower_right: Any) -> sp.Matrix:
        return sp.Matrix(((upper_left, coordinate), (0, lower_right)))

    q_i = matrix(a_i, x_i, b_i)
    q_j = matrix(a_j, x_j, b_j)
    commutator = q_i * q_j - q_j * q_i
    upper_right = sp.expand(commutator[0, 1])
    template = sp.expand(x_j * (a_i - b_i) - x_i * (a_j - b_j))
    if (
        sp.simplify(upper_right - template) != 0
        or sp.simplify(commutator[0, 0]) != 0
        or sp.simplify(commutator[1, 0]) != 0
        or sp.simplify(commutator[1, 1]) != 0
    ):
        raise AssertionError("the universal Q commutator template changed")
    if sp.expand(upper_right.subs({a_i: b_i, a_j: b_j})) != 0:
        raise AssertionError("equal eigenvalues no longer force commuting Q operators")
    on_beta = sp.expand(upper_right.subs({x_i: a_i - b_i, x_j: a_j - b_j}))
    if on_beta != 0:
        raise AssertionError("the coboundary direction no longer commutes")
    return {
        "chart": "Q_i=[[a_i,x_i],[0,b_i]]",
        "commutator_upper_right": str(upper_right),
        "template": "x_j*(a_i - b_i) - x_i*(a_j - b_j)",
        "difference": "0",
        "other_commutator_entries_are_zero": True,
        "commuting_subspace": "K_delta=ker C(delta) in QQ^4",
        "commuting_criterion": (
            "the four Q coordinates lie in K_delta; when delta!=0 this is "
            "span(delta), while when delta=0 it is all of QQ^4"
        ),
        "nonzero_delta_commuting_subspace": "K_delta=span(delta)",
        "zero_delta_commuting_subspace": "K_0=QQ^4",
        "equal_eigenvalue_specialisation_is_identically_zero": True,
        "coboundary_specialisation_is_identically_zero": True,
        "witness_criterion": (
            "a reachable-visible noncommutative witness exists at a base point exactly "
            "when the six commutator rows leave the row space there, that is when "
            "rank[M;C]>rank M with C=C(delta); vanishing of a determinant alone is not "
            "sufficient"
        ),
    }


def universal_coboundary_identity() -> dict[str, Any]:
    """``[[a,a-b],[0,b]]=C*diag(a,b)*C^-1`` with ``C=[[1,-1],[0,1]]``."""

    conjugator = sp.Matrix(((1, -1), (0, 1)))
    symbols = sp.symbols("a0:4 b0:4", nonzero=True)
    uppers, lowers = symbols[:4], symbols[4:]

    def substituted(index: int) -> sp.Matrix:
        return sp.Matrix(((uppers[index], uppers[index] - lowers[index]), (0, lowers[index])))

    generator_failures = []
    for index in range(4):
        conjugated = conjugator * sp.diag(uppers[index], lowers[index]) * conjugator.inv()
        if sp.simplify(substituted(index) - conjugated) != sp.zeros(2, 2):
            generator_failures.append(index)

    word_reports = []
    words = (
        ((0, 1), (1, 0)),
        ((0, 1, 2), (2, 1, 0)),
        ((0, 1, 2, 3), (3, 2, 1, 0)),
    )
    for word, reversed_word in words:
        for letters in (word, reversed_word):
            product = sp.eye(2)
            for index in letters:
                product = product * substituted(index)
            upper_product = sp.prod([uppers[index] for index in letters])
            lower_product = sp.prod([lowers[index] for index in letters])
            residual = sp.simplify(product[0, 1] - (upper_product - lower_product))
            word_reports.append(
                {"letters": list(letters), "upper_right_minus_A_minus_B": str(residual)}
            )
            if residual != 0:
                raise AssertionError("the telescoping coboundary identity changed")

    inverse_product = sp.eye(2)
    inverse_letters = (0, 1, 2, 1, 0)
    inverse_flags = (False, False, True, True, False)
    upper_product = sp.Integer(1)
    lower_product = sp.Integer(1)
    for index, inverted in zip(inverse_letters, inverse_flags, strict=True):
        factor = substituted(index)
        if inverted:
            factor = factor.inv()
            upper_product /= uppers[index]
            lower_product /= lowers[index]
        else:
            upper_product *= uppers[index]
            lower_product *= lowers[index]
        inverse_product = inverse_product * factor
    inverse_residual = sp.simplify(
        sp.together(inverse_product[0, 1] - (upper_product - lower_product))
    )
    if generator_failures or inverse_residual != 0:
        raise AssertionError("the coboundary identity failed on an inverted word")

    return {
        "substitution": "x_e = beta_e = a_e - b_e",
        "conjugator": "C=[[1,-1],[0,1]]",
        "generator_identity": "[[a_e,a_e-b_e],[0,b_e]] = C*diag(a_e,b_e)*C^-1",
        "generator_failures": generator_failures,
        "word_identity": "upper_right(W) = A_W - B_W for every word, inverses included",
        "checked_words": word_reports,
        "inverted_word_letters": list(inverse_letters),
        "inverted_word_residual": str(inverse_residual),
        "operator_row_consequence": (
            "an operator relation forces A_lhs=A_rhs and B_lhs=B_rhs, so its residual on "
            "beta is (A_lhs-B_lhs)-(A_rhs-B_rhs)=0 at every base point"
        ),
        "fixed_vector_GC_consequence": (
            "a fixed-vector GC relation only forces B_lhs=B_rhs, so its residual on beta "
            "is A_lhs-A_rhs and vanishes exactly when the upper character satisfies that "
            "monomial row"
        ),
        "reachable_state_MSR_consequence": (
            "an MSR row evaluates on beta to (identity_coefficient+sum coeff*a_e)*A_state "
            "and vanishes exactly when the upper character satisfies that additive equation"
        ),
        "membership_criterion": (
            "beta lies in ker M exactly when the upper character also lies on the bottom "
            "scalar locus"
        ),
    }


def general_bottom_faithfulness(
    context: torus.ScoutContext,
    upper: dict[str, Fraction],
) -> dict[str, Any]:
    """Pin the closed-form bottom character and Eq139 builder to the shipped ones."""

    lower = bottom_character(NORMALIZED_COUPLINGS, NORMALIZED_Q5)
    signature_failures = []
    for occurrence, record in context.occurrence_records.items():
        stage = int(record["stage"])
        relation = tuple(int(row) for row in record["source_relation_rows"])
        precursor = int(record["precursor_code"])
        if lower(stage, relation, precursor) != torus._csg(stage, relation, precursor):
            signature_failures.append(str(occurrence))
    q_failures = [
        str(stage)
        for stage in (1, 2, 3, 4, 5)
        if lower(stage, (0,) * stage, 0) != torus._csg(stage, (0,) * stage, 0)
    ]
    mismatches = [
        list(instance)
        for instance in torus._eq139_instances(torus.EQ139_STRICT)
        if eq139_row(context, upper, lower, instance)
        != transverse._eq139_row(context, upper, instance)
    ]
    return {
        "closed_form": "b_e=lam(width,maximal)/lam(stage,0), lam=sum binomial*t_k, t0=1",
        "cutoff_external_coordinate": "b_Q5=q5, free and independent of t",
        "normalized_specialisation": "t1=t2=t3=t4=1, q5=1/32",
        "occurrence_signature_failures": signature_failures,
        "Q_stage_failures": q_failures,
        "agrees_with_the_shipped_csg_at_the_normalized_point": not signature_failures
        and not q_failures,
        "shipped_eq139_row_hardcodes_the_normalized_bottom": True,
        "eq139_instances_compared": [
            list(instance) for instance in torus._eq139_instances(torus.EQ139_STRICT)
        ],
        "eq139_row_mismatches_at_the_normalized_point": mismatches,
        "general_bottom_eq139_builder_reproduces_the_shipped_rows": not mismatches,
    }


def _monomial_failures(
    point: dict[str, Fraction],
    rows: list[tuple[str, Any]],
) -> list[str]:
    failures = []
    for label, row in rows:
        product = Fraction(1)
        for variable, exponent in row.items():
            product *= point[variable] ** exponent
        if product != 1:
            failures.append(label)
    return failures


def _beta_block_report(
    joint_rows: list[SparseRow],
    beta: dict[str, Fraction],
) -> dict[str, dict[str, int]]:
    report: dict[str, dict[str, int]] = {}
    for name, start, stop in ROW_BLOCKS:
        violations = sum(1 for row in joint_rows[start:stop] if _apply(row, beta))
        report[name] = {"rows": stop - start, "violations": violations}
    return report


# --------------------------------------------------------------------------- #
# strata                                                                        #
# --------------------------------------------------------------------------- #


def equal_eigenvalue_stratum(
    context: torus.ScoutContext,
    operator_rows: list[tuple[str, Any]],
) -> dict[str, Any]:
    """Stratum I: ``E={a_e=b_e}``, rank 127, kernel = bottom tangent space."""

    positions = {variable: index for index, variable in enumerate(context.variables)}
    samples = []
    for couplings, q5 in EQUAL_EIGENVALUE_SAMPLES:
        lower = bottom_character(couplings, q5)
        point = bottom_point(context, lower)
        operator_failures = _monomial_failures(point, operator_rows)
        if operator_failures:
            raise AssertionError("a bottom point left the 843-row operator lattice torus")

        sampled = sample_point(context, dict(point), lower)
        if not sampled["delta_Q_is_zero"]:
            raise AssertionError("an equal-eigenvalue sample has a nonzero delta")
        if not sampled["all_six_commutator_rows_vanish_identically"]:
            raise AssertionError("an equal-eigenvalue sample has a nonzero commutator row")
        if sampled["any_branch_admits_a_visible_witness"]:
            raise AssertionError("an equal-eigenvalue sample produced a witness")
        ranks = {branch: data["rank"] for branch, data in sampled["branches"].items()}
        if set(ranks.values()) != {EXPECTED_EQUAL_EIGENVALUE_RANK}:
            raise AssertionError(f"the equal-eigenvalue rank changed: {ranks}")

        tangents = bottom_tangent_vectors(context, couplings, q5)
        violations: dict[str, dict[str, int]] = {}
        for branch_id, (eq113_branch, eq139_domain) in BRANCH_SPECS.items():
            rows = branch_matrix(
                context, dict(point), lower, sampled["joint_rows"], eq113_branch, eq139_domain
            )
            violations[branch_id] = {
                name: sum(
                    1
                    for row in rows
                    if sum(
                        (
                            coefficient * vector[positions[variable]]
                            for variable, coefficient in row.items()
                        ),
                        start=Fraction(0),
                    )
                )
                for name, vector in tangents.items()
            }
        tangent_rank = _rank(
            [
                {context.variables[index]: value for index, value in enumerate(vector) if value}
                for vector in tangents.values()
            ],
            context.variables,
        )
        if tangent_rank != 5 or any(
            count for report in violations.values() for count in report.values()
        ):
            raise AssertionError("the bottom tangent space is no longer the exact kernel")

        samples.append(
            {
                "couplings": [str(value) for value in couplings],
                "cutoff_external_q5": str(q5),
                "all_843_operator_monomial_rows_hold": not operator_failures,
                "point_digest_sha256": _digest(
                    [str(point[variable]) for variable in context.variables]
                ),
                "delta_Q": sampled["delta_Q"],
                "delta_Q_is_zero": True,
                "all_six_commutator_rows_vanish_identically": True,
                "branches": sampled["branches"],
                "bottom_tangent_row_violations": violations,
                "bottom_tangent_rank": tangent_rank,
                "tangent_digest_sha256": _digest(
                    {name: [str(value) for value in vector] for name, vector in tangents.items()}
                ),
            }
        )

    return {
        "name": "full-diagonal locus",
        "definition": "E={a_e=b_e for all 132 coordinates}",
        "why_nonempty": (
            "the bottom scalar locus satisfies the 843-row operator monomial lattice and "
            "therefore lies inside the upper torus G_m^49; E is its diagonal copy"
        ),
        "dimension": 5,
        "codimension_in_the_transverse_scalar_base": 49,
        "relation_to_equal_Q_spectrum_locus": (
            "E is contained in the generally larger locus Z_Q={delta_Q=0}; all of "
            "Z_Q is witness-free by the universal commutator identity"
        ),
        "contained_in_every_branch_determinant_zero_locus": True,
        "exact_rank_at_every_certified_sample": EXPECTED_EQUAL_EIGENVALUE_RANK,
        "exact_nullity_at_every_certified_sample": 132 - EXPECTED_EQUAL_EIGENVALUE_RANK,
        "rank_drop_from_the_generic_derived_rank": 131 - EXPECTED_EQUAL_EIGENVALUE_RANK,
        "stratum_wide_rank_constancy_proved": False,
        "kernel_identification_at_every_certified_sample": (
            "ker M is the tangent space of the five-dimensional bottom scalar locus, "
            "realised as the scalar deformations x_e=d b_e/d p for p in {t1,t2,t3,t4,q5}"
        ),
        "kernel_argument": (
            "the five tangent vectors annihilate every row of every branch matrix, they "
            "are linearly independent, and the exact nullity is five, so they span the "
            "kernel exactly at that point"
        ),
        "commutator_conclusion": (
            "a=b forces delta_Q=0 everywhere on E, so the universal template makes all six "
            "commutator rows vanish identically on E, whatever the rank and kernel are"
        ),
        "witness_conclusion": (
            "no reachable-visible noncommutative witness anywhere on E, in any of the "
            "four semantic branches"
        ),
        "witness_conclusion_is_stratum_wide": True,
        "witness_conclusion_argument": (
            "delta_Q=0 on all of E and the commutator template is identically zero when "
            "delta_Q=0, so rank[M;C]=rank M at every point of E independently of the "
            "pointwise rank certificates"
        ),
        "samples": samples,
    }


def bi_scalar_stratum(
    context: torus.ScoutContext,
    operator_rows: list[tuple[str, Any]],
    fixed_gc_rows: list[tuple[str, Any]],
) -> dict[str, Any]:
    """Stratum II: the upper character is itself a bottom-locus character."""

    couplings, q5 = REFERENCE_BOTTOM
    lower = bottom_character(couplings, q5)
    reference = bottom_point(context, lower)
    samples = []
    for upper_couplings, upper_q5 in BI_SCALAR_SAMPLES:
        if (upper_couplings, upper_q5) == (couplings, q5):
            raise AssertionError("a two-scalar sample coincides with the bottom point")
        upper = bottom_point(context, bottom_character(upper_couplings, upper_q5))
        beta = {variable: upper[variable] - reference[variable] for variable in upper}
        if not any(beta.values()):
            raise AssertionError("a two-scalar sample landed on the equal-eigenvalue stratum")
        operator_failures = _monomial_failures(upper, operator_rows)
        gc_failures = _monomial_failures(upper, fixed_gc_rows)
        if operator_failures or gc_failures:
            raise AssertionError("a two-scalar upper character left the combined lattice")

        sampled = sample_point(context, dict(upper), lower)
        if sampled["delta_Q_is_zero"]:
            raise AssertionError("a two-scalar sample has delta zero")
        if sampled["any_branch_admits_a_visible_witness"]:
            raise AssertionError("a two-scalar sample produced a witness")
        ranks = {branch: data["rank"] for branch, data in sampled["branches"].items()}
        if set(ranks.values()) != {EXPECTED_BI_SCALAR_RANK}:
            raise AssertionError(f"the two-scalar rank changed: {ranks}")

        blocks = _beta_block_report(sampled["joint_rows"], beta)
        if any(blocks[name]["violations"] for name, _start, _stop in ROW_BLOCKS):
            raise AssertionError("beta left the row inventory on the two-scalar stratum")

        beta_row = _as_row(beta)
        q5_row = {torus.Q5: Fraction(1)}
        kernel_reports = {}
        for branch_id, (eq113_branch, eq139_domain) in BRANCH_SPECS.items():
            rows = branch_matrix(
                context, dict(upper), lower, sampled["joint_rows"], eq113_branch, eq139_domain
            )
            beta_violations = sum(1 for row in rows if _apply(row, beta))
            q5_violations = sum(1 for row in rows if row.get(torus.Q5, Fraction(0)))
            spanned = _rank([beta_row, q5_row], context.variables)
            appended = _rank([*rows, beta_row, q5_row], context.variables)
            if (
                beta_violations
                or q5_violations
                or spanned != 2
                or appended != sampled["branches"][branch_id]["rank"] + 2
            ):
                raise AssertionError("the two-scalar kernel is not span(beta,e_Q5)")
            kernel_reports[branch_id] = {
                "beta_row_violations": beta_violations,
                "rows_with_a_nonzero_Q5_column": q5_violations,
                "dimension_of_span_beta_e_Q5": spanned,
                "rank_after_appending_both_directions": appended,
            }

        commutators_on_beta = {
            pair: str(_apply(row, beta)) for pair, row in sorted(sampled["commutators"].items())
        }
        if any(value != "0" for value in commutators_on_beta.values()):
            raise AssertionError("a commutator form no longer annihilates beta")

        samples.append(
            {
                "upper_couplings": [str(value) for value in upper_couplings],
                "upper_cutoff_external_q5": str(upper_q5),
                "all_843_operator_monomial_rows_hold": not operator_failures,
                "all_320_fixed_vector_GC_monomial_rows_hold": not gc_failures,
                "delta_Q": sampled["delta_Q"],
                "delta_Q_is_zero": False,
                "beta_violations_per_row_block": blocks,
                "six_commutator_forms_on_beta": commutators_on_beta,
                "branches": sampled["branches"],
                "kernel_reports": kernel_reports,
                "point_digest_sha256": _digest(
                    [str(upper[variable]) for variable in context.variables]
                ),
            }
        )

    # The external Q5 coordinate is not part of delta_Q.  Consequently S minus E
    # contains a six-dimensional delta_Q=0 subfamily: keep the four couplings
    # equal and vary the two independent Q5 coordinates.  Freeze one exact
    # off-diagonal point so this distinction cannot regress.
    q5_only_upper = bottom_point(
        context,
        bottom_character(couplings, Q5_ONLY_UPPER_Q5),
    )
    q5_only_beta = {
        variable: q5_only_upper[variable] - reference[variable] for variable in q5_only_upper
    }
    differing_coordinates = [variable for variable, value in q5_only_beta.items() if value]
    if differing_coordinates != [torus.Q5]:
        raise AssertionError("the Q5-only two-scalar sample changed coordinates")
    q5_only_operator_failures = _monomial_failures(q5_only_upper, operator_rows)
    q5_only_gc_failures = _monomial_failures(q5_only_upper, fixed_gc_rows)
    if q5_only_operator_failures or q5_only_gc_failures:
        raise AssertionError("the Q5-only upper character left the combined lattice")

    q5_only_sampled = sample_point(context, q5_only_upper, lower)
    if (
        not q5_only_sampled["delta_Q_is_zero"]
        or not q5_only_sampled["all_six_commutator_rows_vanish_identically"]
        or q5_only_sampled["any_branch_admits_a_visible_witness"]
    ):
        raise AssertionError("the Q5-only two-scalar sample left the delta_Q=0 locus")
    q5_only_ranks = {branch: data["rank"] for branch, data in q5_only_sampled["branches"].items()}
    if set(q5_only_ranks.values()) != {EXPECTED_EQUAL_EIGENVALUE_RANK}:
        raise AssertionError(f"the Q5-only two-scalar rank changed: {q5_only_ranks}")

    positions = {variable: index for index, variable in enumerate(context.variables)}
    q5_only_tangents = bottom_tangent_vectors(context, couplings, Q5_ONLY_UPPER_Q5)
    q5_only_tangent_violations: dict[str, dict[str, int]] = {}
    for branch_id, (eq113_branch, eq139_domain) in BRANCH_SPECS.items():
        rows = branch_matrix(
            context,
            q5_only_upper,
            lower,
            q5_only_sampled["joint_rows"],
            eq113_branch,
            eq139_domain,
        )
        q5_only_tangent_violations[branch_id] = {
            name: sum(
                1
                for row in rows
                if sum(
                    (
                        coefficient * vector[positions[variable]]
                        for variable, coefficient in row.items()
                    ),
                    start=Fraction(0),
                )
            )
            for name, vector in q5_only_tangents.items()
        }
    q5_only_tangent_rank = _rank(
        [
            {context.variables[index]: value for index, value in enumerate(vector) if value}
            for vector in q5_only_tangents.values()
        ],
        context.variables,
    )
    if q5_only_tangent_rank != 5 or any(
        count for report in q5_only_tangent_violations.values() for count in report.values()
    ):
        raise AssertionError("the Q5-only tangent kernel changed")
    q5_only_blocks = _beta_block_report(q5_only_sampled["joint_rows"], q5_only_beta)
    if any(block["violations"] for block in q5_only_blocks.values()):
        raise AssertionError("the Q5-only coboundary left the kernel")

    q5_only_subfamily = {
        "name": "same-couplings independent-Q5 subfamily",
        "symbol": "T",
        "definition": (
            "the upper and lower bottom characters share t1,t2,t3,t4 while their "
            "external Q5 coordinates vary independently"
        ),
        "dimension": 6,
        "relation_to_E": "E is the q5_upper=q5_lower diagonal inside T",
        "relation_to_S": "E is a proper subset of T and T is a subset of S",
        "delta_Q_zero_part_of_S": (
            "exactly T: Q_n=1/lambda(n,0) for n=1..4, and equality recursively "
            "forces equality of t1,t2,t3,t4; Q5 is not in delta_Q"
        ),
        "witness_conclusion": (
            "all six commutator rows vanish identically on T, so T is witness-free "
            "subfamily-wide independently of branch rank"
        ),
        "witness_conclusion_is_subfamily_wide": True,
        "rank_constancy_proved": False,
        "sample": {
            "shared_couplings": [str(value) for value in couplings],
            "lower_cutoff_external_q5": str(q5),
            "upper_cutoff_external_q5": str(Q5_ONLY_UPPER_Q5),
            "differing_coordinates": differing_coordinates,
            "all_843_operator_monomial_rows_hold": not q5_only_operator_failures,
            "all_320_fixed_vector_GC_monomial_rows_hold": not q5_only_gc_failures,
            "delta_Q": q5_only_sampled["delta_Q"],
            "delta_Q_is_zero": True,
            "all_six_commutator_rows_vanish_identically": True,
            "beta_violations_per_row_block": q5_only_blocks,
            "branches": q5_only_sampled["branches"],
            "upper_bottom_tangent_rank": q5_only_tangent_rank,
            "upper_bottom_tangent_row_violations": q5_only_tangent_violations,
            "kernel_identification": (
                "ker M is the five-dimensional tangent space of the upper "
                "bottom-character locus at this exact point"
            ),
        },
    }

    return {
        "name": "two-scalar locus",
        "definition": "S={the upper character a is itself a bottom scalar locus point}",
        "reference_bottom_couplings": [str(value) for value in couplings],
        "reference_cutoff_external_q5": str(q5),
        "dimension": 10,
        "codimension_in_the_transverse_scalar_base": 44,
        "meets_delta_nonzero": True,
        "also_contains_delta_zero_points_outside_E": True,
        "exact_rank_at_every_certified_nonzero_delta_sample": EXPECTED_BI_SCALAR_RANK,
        "exact_nullity_at_every_certified_nonzero_delta_sample": (132 - EXPECTED_BI_SCALAR_RANK),
        "stratum_wide_rank_constancy_proved": False,
        "universal_nullity_lower_bound_on_S_minus_E": 1,
        "universal_nullity_argument": (
            "by the coboundary membership criterion beta lies in ker M at every point "
            "of S, and beta is nonzero away from the equal-eigenvalue stratum, so the "
            "nullity is at least one everywhere on S minus E"
        ),
        "kernel_identification_at_every_certified_nonzero_delta_sample": (
            "ker M = span(beta, e_Q5)"
        ),
        "kernel_argument": (
            "beta and e_Q5 annihilate every row, they are independent, and the exact "
            "nullity is two at that point"
        ),
        "commutator_conclusion": (
            "beta is a global conjugation coboundary and the six commutator forms "
            "annihilate it identically at every base point; e_Q5 has no Q1,...,Q4 "
            "component; so at the four certified samples, where delta_Q!=0 and the "
            "kernel is span(beta,e_Q5), Q1,...,Q4 commute"
        ),
        "witness_conclusion": (
            "no reachable-visible noncommutative witness at any certified sample of S, "
            "in any of the four semantic branches"
        ),
        "witness_conclusion_is_stratum_wide": False,
        "witness_conclusion_argument": (
            "the subfamily T is witness-free because delta_Q=0; on the remaining "
            "delta_Q!=0 part of S, only the beta direction is universally harmless, "
            "and witness freedom is certified at four points rather than proved "
            "stratum-wide"
        ),
        "same_couplings_independent_Q5_subfamily": q5_only_subfamily,
        "samples": samples,
    }


def off_normalized_principal_opens(
    context: torus.ScoutContext,
    kernel_columns: list[list[int]],
    operator_rows: list[tuple[str, Any]],
) -> list[dict[str, Any]]:
    """Full-rank splitting opens over bottom characters other than ``t=(1,1,1,1)``."""

    records = []
    for label, couplings, q5, torus_point in OFF_NORMALIZED_OPENS:
        if (couplings, q5) == (NORMALIZED_COUPLINGS, NORMALIZED_Q5):
            raise AssertionError("an off-normalized sample is the normalized point")
        lower = bottom_character(couplings, q5)
        upper: dict[str, Fraction] = {}
        for index, variable in enumerate(context.variables):
            value = Fraction(1)
            for column, coordinate in enumerate(torus_point):
                exponent = kernel_columns[column][index]
                if exponent:
                    value *= coordinate**exponent
            upper[variable] = value
        if not all(upper.values()):
            raise AssertionError("an off-normalized upper point left the torus")
        operator_failures = _monomial_failures(upper, operator_rows)
        if operator_failures:
            raise AssertionError("an off-normalized upper point left the operator lattice")
        sampled = sample_point(context, upper, lower)
        ranks = {branch: data["rank"] for branch, data in sampled["branches"].items()}
        if ranks != EXPECTED_GENERIC_RANKS:
            raise AssertionError(f"an off-normalized open lost full rank: {ranks}")
        if sampled["any_branch_admits_a_visible_witness"]:
            raise AssertionError("an off-normalized open produced a witness")

        # The coboundary dichotomy, exhibited where the upper character is NOT a
        # bottom character: beta still satisfies every conjugation-invariant row
        # and must fail the fixed-vector GC and reachable-state MSR rows.
        reference = bottom_point(context, lower)
        beta = {variable: upper[variable] - reference[variable] for variable in upper}
        blocks = _beta_block_report(sampled["joint_rows"], beta)
        invariant_clean = all(
            blocks[name]["violations"] == 0 for name in CONJUGATION_INVARIANT_BLOCKS
        )
        omega_blocks_broken = all(
            blocks[name]["violations"] > 0
            for name in ("fixed_vector_GC_basis", "reachable_state_MSR")
        )
        if not invariant_clean or not omega_blocks_broken:
            raise AssertionError(f"the coboundary dichotomy failed at {label}: {blocks}")

        records.append(
            {
                "label": label,
                "couplings": [str(value) for value in couplings],
                "cutoff_external_q5": str(q5),
                "upper_torus_coordinates": [str(value) for value in torus_point],
                "all_843_operator_monomial_rows_hold": not operator_failures,
                "delta_Q": sampled["delta_Q"],
                "delta_Q_is_zero": False,
                "branches": sampled["branches"],
                "beta_violations_per_row_block": blocks,
                "coboundary_dichotomy": {
                    "conjugation_invariant_blocks_are_satisfied": invariant_clean,
                    "omega_dependent_blocks_are_violated": omega_blocks_broken,
                    "interpretation": (
                        "the upper character is not a bottom scalar locus point here, so "
                        "beta leaves the kernel exactly through the fixed-vector GC and "
                        "reachable-state MSR rows, as the universal identity predicts"
                    ),
                },
                "conclusion": (
                    "a new nonempty splitting principal open in each of the four semantic "
                    "branches, over a non-normalized bottom character"
                ),
            }
        )
    return records


def _kernel_basis(
    rows: list[SparseRow],
    variables: tuple[str, ...],
) -> tuple[int, list[tuple[Fraction, ...]]]:
    """Exact rank and a full kernel basis from the tracked elimination."""

    elimination = transverse._tracked_row_echelon(rows, variables)
    basis = elimination["basis"]
    width = len(variables)
    vectors = []
    for free in (column for column in range(width) if column not in basis):
        coordinates: dict[int, Fraction] = {free: Fraction(1)}
        for pivot in sorted(basis, reverse=True):
            coordinates[pivot] = -sum(
                (
                    coefficient * coordinates.get(column, Fraction(0))
                    for column, coefficient in basis[pivot].items()
                    if column != pivot
                ),
                start=Fraction(0),
            )
        vectors.append(tuple(coordinates.get(column, Fraction(0)) for column in range(width)))
    return int(elimination["rank"]), vectors


def span_beta_q5_is_not_the_right_invariant(
    context: torus.ScoutContext,
    kernel_columns: list[list[int]],
) -> dict[str, Any]:
    """One exact point where the kernel leaves ``span(beta,e_Q5)`` and still commutes.

    A future search must not use "the kernel stays inside ``span(beta,e_Q5)``" as
    the invariant to defend.  At the point below the upper character is not a
    bottom character, ``beta`` is not even in the kernel, the kernel is not
    contained in ``span(beta,e_Q5)`` -- and every commutator form still vanishes
    on all of it.  Here ``delta_Q!=0`` and the kernel's ``Q`` coordinates land
    on ``span(delta_Q)=K_delta``.  The correct invariant is containment of the
    ``Q``-projection in ``K_delta=ker C(delta_Q)``, not the coboundary span.
    """

    couplings, q5 = REFERENCE_BOTTOM
    lower = bottom_character(couplings, q5)
    base = bottom_point(context, lower)
    exponents = kernel_columns[COUNTEREXAMPLE_DIRECTION]
    upper = {
        variable: (
            base[variable] * COUNTEREXAMPLE_SCALAR ** exponents[index]
            if exponents[index]
            else base[variable]
        )
        for index, variable in enumerate(context.variables)
    }
    beta = {variable: upper[variable] - base[variable] for variable in upper}
    positions = {variable: index for index, variable in enumerate(context.variables)}
    q_columns = [positions[torus._q_variable(context, stage)] for stage in (1, 2, 3, 4)]

    joint_rows, _counts, commutators, _paths = torus._linear_system(context, upper, lower)
    delta = [
        upper[torus._q_variable(context, stage)] - lower(stage, (0,) * stage, 0)
        for stage in (1, 2, 3, 4)
    ]
    rows = branch_matrix(context, upper, lower, joint_rows, torus.EQ113_DERIVED, torus.EQ139_STRICT)
    rank, kernel = _kernel_basis(rows, context.variables)
    beta_violations = sum(1 for row in rows if _apply(row, beta))
    beta_row = _as_row(beta)
    q5_row = {torus.Q5: Fraction(1)}
    inside = _rank([beta_row, q5_row], context.variables)
    escaping = []
    commutator_values = []
    for index, vector in enumerate(kernel):
        as_row = {context.variables[column]: value for column, value in enumerate(vector) if value}
        if _rank([beta_row, q5_row, as_row], context.variables) > inside:
            escaping.append(index)
        commutator_values.append(
            {pair: str(_apply(row, as_row)) for pair, row in sorted(commutators.items())}
        )
    all_commutators_vanish = all(
        value == "0" for record in commutator_values for value in record.values()
    )
    if not (beta_violations and escaping and all_commutators_vanish):
        raise AssertionError(
            "the span(beta,e_Q5) counterexample changed: "
            f"beta_violations={beta_violations} escaping={escaping} "
            f"commutators_vanish={all_commutators_vanish}"
        )
    return {
        "direction": COUNTEREXAMPLE_DIRECTION,
        "scalar": str(COUNTEREXAMPLE_SCALAR),
        "Q_column_exponents": [exponents[column] for column in q_columns],
        "delta_Q": [str(value) for value in delta],
        "upper_is_a_bottom_character": False,
        "beta_row_violations": beta_violations,
        "rank": rank,
        "nullity": len(kernel),
        "kernel_indices_outside_span_beta_e_Q5": escaping,
        "kernel_Q_coordinates": [
            [str(vector[column]) for column in q_columns] for vector in kernel
        ],
        "six_commutator_forms_on_each_kernel_vector": commutator_values,
        "all_commutator_forms_vanish_on_the_whole_kernel": all_commutators_vanish,
        "lesson": (
            "the kernel can leave span(beta,e_Q5) at a degenerate point and still "
            "commute; at this nonzero-delta_Q point its Q coordinates land on "
            "span(delta_Q)=K_delta.  The invariant a future search must decide is "
            "whether the Q-projection of ker M lies in K_delta=ker C(delta_Q), not "
            "whether ker M lies in the coboundary span"
        ),
    }


def degeneracy_scan(
    context: torus.ScoutContext,
    kernel_columns: list[list[int]],
) -> dict[str, Any]:
    """Deterministic exact scan of one-parameter families through stratum I."""

    couplings, q5 = REFERENCE_BOTTOM
    lower = bottom_character(couplings, q5)
    base = bottom_point(context, lower)
    q_columns = {
        stage: context.variables.index(torus._q_variable(context, stage)) for stage in (1, 2, 3, 4)
    }
    records = []
    census: dict[str, int] = {}
    witnesses = []
    for direction in SCAN_DIRECTIONS:
        exponents = kernel_columns[direction]
        q_exponents = [exponents[q_columns[stage]] for stage in (1, 2, 3, 4)]
        for scalar in SCAN_SCALARS:
            upper = {
                variable: (
                    base[variable] * scalar ** exponents[index]
                    if exponents[index]
                    else base[variable]
                )
                for index, variable in enumerate(context.variables)
            }
            if not all(upper.values()):
                raise AssertionError("a scan point left the torus")
            sampled = sample_point(context, upper, lower)
            profile = "/".join(str(sampled["branches"][branch]["rank"]) for branch in BRANCH_SPECS)
            census[profile] = census.get(profile, 0) + 1
            record = {
                "direction": direction,
                "scalar": str(scalar),
                "Q_column_exponents": q_exponents,
                "delta_Q_is_zero": sampled["delta_Q_is_zero"],
                "rank_profile": profile,
                "augmented_rank_profile": "/".join(
                    str(sampled["branches"][branch]["rank_with_commutator_rows"])
                    for branch in BRANCH_SPECS
                ),
                "any_branch_admits_a_visible_witness": sampled[
                    "any_branch_admits_a_visible_witness"
                ],
            }
            records.append(record)
            if record["any_branch_admits_a_visible_witness"]:
                witnesses.append(record)
    if witnesses:
        raise AssertionError(f"the deterministic scan produced witnesses: {witnesses}")
    return {
        "family": "a_e=b_e*s^K[j][e] through the equal-eigenvalue point",
        "base_bottom_couplings": [str(value) for value in couplings],
        "base_cutoff_external_q5": str(q5),
        "directions": list(SCAN_DIRECTIONS),
        "scalars": [str(value) for value in SCAN_SCALARS],
        "point_count": len(records),
        "rank_profile_census": census,
        "rank_profile_agrees_at_all_four_recorded_scalars_for_each_direction": all(
            len({record["rank_profile"] for record in records if record["direction"] == direction})
            == 1
            for direction in SCAN_DIRECTIONS
        ),
        "records": records,
        "records_digest_sha256": _digest(records),
        "witnesses": witnesses,
        "commutator_rows_stay_inside_the_row_space_at_every_scanned_point": True,
        "scan_status": "BOUNDED_DETERMINISTIC_SCAN_NOT_A_GLOBAL_OBSTRUCTION",
    }


def build_payload(root: Path) -> dict[str, Any]:
    """Classify the commutator kernel and exact nested degeneracy loci."""

    root = root.resolve()
    frozen_lattice = _load(root / lattice.RESULT_PATH)
    frozen_bottom = _load(root / bottom_global.RESULT_PATH)
    frozen_transverse = _load(root / transverse.RESULT_PATH)
    for frozen, module in (
        (frozen_lattice, lattice),
        (frozen_bottom, bottom_global),
        (frozen_transverse, transverse),
    ):
        if frozen.get("verdict") != module.VERDICT or frozen.get(
            "semantic_digest_sha256"
        ) != module.semantic_digest(frozen):
            raise AssertionError(f"the frozen binding failed for {module.RESULT_PATH}")

    context = torus._build_context(root)
    lattice_context = lattice._build_context(root)
    operator_rows, _ = lattice._operator_lattice_rows(lattice_context)
    fixed_gc_rows = lattice._fixed_gc_rows(lattice_context)
    kernel_columns = transverse._operator_kernel(frozen_lattice)
    reference_upper, _exponents = transverse._upper_point(context, kernel_columns)

    commutator = universal_commutator_identity()
    coboundary = universal_coboundary_identity()
    faithfulness = general_bottom_faithfulness(context, reference_upper)
    stratum_one = equal_eigenvalue_stratum(context, operator_rows)
    stratum_two = bi_scalar_stratum(context, operator_rows, fixed_gc_rows)
    off_normalized = off_normalized_principal_opens(context, kernel_columns, operator_rows)
    scan = degeneracy_scan(context, kernel_columns)
    span_note = span_beta_q5_is_not_the_right_invariant(context, kernel_columns)

    gates = {
        "prerequisite_certificates_bind_by_verdict_and_semantic_digest": True,
        "universal_commutator_template_is_exact": commutator[
            "equal_eigenvalue_specialisation_is_identically_zero"
        ],
        "zero_delta_commuting_subspace_is_all_QQ4": (
            commutator["zero_delta_commuting_subspace"] == "K_0=QQ^4"
        ),
        "commutator_forms_annihilate_the_coboundary_symbolically": commutator[
            "coboundary_specialisation_is_identically_zero"
        ],
        "coboundary_conjugation_identity_holds_on_words_and_inverses": not coboundary[
            "generator_failures"
        ]
        and coboundary["inverted_word_residual"] == "0",
        "general_bottom_character_matches_the_shipped_csg_when_normalized": faithfulness[
            "agrees_with_the_shipped_csg_at_the_normalized_point"
        ],
        "general_bottom_eq139_builder_matches_the_shipped_rows_when_normalized": (
            faithfulness["general_bottom_eq139_builder_reproduces_the_shipped_rows"]
        ),
        "full_diagonal_locus_is_nonempty_and_on_the_operator_lattice": all(
            sample["all_843_operator_monomial_rows_hold"] for sample in stratum_one["samples"]
        ),
        "full_diagonal_rank_is_127_in_all_four_branches_at_every_sample": all(
            branch["rank"] == EXPECTED_EQUAL_EIGENVALUE_RANK
            for sample in stratum_one["samples"]
            for branch in sample["branches"].values()
        ),
        "bottom_tangent_space_is_the_exact_kernel_at_full_diagonal_samples": all(
            sample["bottom_tangent_rank"] == 5
            and not any(
                count
                for report in sample["bottom_tangent_row_violations"].values()
                for count in report.values()
            )
            for sample in stratum_one["samples"]
        ),
        "two_scalar_rank_is_130_at_every_certified_nonzero_delta_sample": all(
            branch["rank"] == EXPECTED_BI_SCALAR_RANK
            for sample in stratum_two["samples"]
            for branch in sample["branches"].values()
        ),
        "two_scalar_nonzero_delta_sample_kernel_is_span_beta_and_e_Q5": all(
            report["dimension_of_span_beta_e_Q5"] == 2
            and not report["beta_row_violations"]
            and not report["rows_with_a_nonzero_Q5_column"]
            for sample in stratum_two["samples"]
            for report in sample["kernel_reports"].values()
        ),
        "two_scalar_certified_rank130_samples_have_nonzero_delta": all(
            not sample["delta_Q_is_zero"] for sample in stratum_two["samples"]
        ),
        "two_scalar_locus_also_has_a_Q5_only_delta_zero_subfamily": (
            stratum_two["also_contains_delta_zero_points_outside_E"]
            and stratum_two["same_couplings_independent_Q5_subfamily"][
                "witness_conclusion_is_subfamily_wide"
            ]
            and stratum_two["same_couplings_independent_Q5_subfamily"]["sample"]["delta_Q_is_zero"]
        ),
        "no_witness_at_any_certified_nested_locus_sample": all(
            not branch["commutator_rows_leave_the_row_space"]
            for stratum in (stratum_one, stratum_two)
            for sample in stratum["samples"]
            for branch in sample["branches"].values()
        )
        and all(
            not branch["commutator_rows_leave_the_row_space"]
            for branch in stratum_two["same_couplings_independent_Q5_subfamily"]["sample"][
                "branches"
            ].values()
        ),
        "off_normalized_bottom_characters_carry_full_rank_opens": all(
            record["branches"][branch]["rank"] == EXPECTED_GENERIC_RANKS[branch]
            for record in off_normalized
            for branch in BRANCH_SPECS
        ),
        "deterministic_scan_found_no_witness": not scan["witnesses"],
        "deterministic_scan_rank_profiles_agree_at_the_recorded_samples": scan[
            "rank_profile_agrees_at_all_four_recorded_scalars_for_each_direction"
        ],
        "span_beta_e_Q5_is_certified_not_to_be_the_right_invariant": bool(
            span_note["kernel_indices_outside_span_beta_e_Q5"]
        )
        and span_note["all_commutator_forms_vanish_on_the_whole_kernel"],
        "coboundary_dichotomy_exhibited_off_the_bottom_locus": all(
            record["coboundary_dichotomy"]["conjugation_invariant_blocks_are_satisfied"]
            and record["coboundary_dichotomy"]["omega_dependent_blocks_are_violated"]
            for record in off_normalized
        ),
    }
    if not all(gates.values()):
        raise AssertionError(f"determinant-zero locus gate failed: {gates}")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "date": "2026-08-02",
        "finite_scope": "n<=4",
        "dimension": 2,
        "profile": "fixed_vector_GC__reachable_state_MSR__occurrence_identification_ON",
        "semantic_branch_rule": {
            "Eq113": "derived and literal readings are alternative branches, never simultaneous",
            "Eq139": "printed-strict and Eq145-completed domains are alternative branches",
            "matrix_count": 4,
            "joint_all_readings_inference_forbidden": True,
        },
        "declared_chart": {
            "matrix_form": "A_e=[[a_e,x_e],[0,b_e]]",
            "initial_vector": "e_2",
            "interpretation": "globally reducible line transverse to the initial vector",
            "scalar_base": "G_m^49(a) x BottomMSR(b), dimension 54",
            "upper_right_coordinates": 132,
        },
        "field": {
            "base_points_and_matrices": "QQ",
            "universal_identities": "generic symbolic 2x2 over QQ",
            "floating_point_used": False,
            "finite_field_used": False,
            "groebner_used": False,
            "sage_used": False,
        },
        "input_artifacts": {
            relative: {
                "raw_sha256": _sha256(root / relative),
                "semantic_digest_sha256": frozen["semantic_digest_sha256"],
            }
            for relative, frozen in (
                (lattice.RESULT_PATH, frozen_lattice),
                (bottom_global.RESULT_PATH, frozen_bottom),
                (transverse.RESULT_PATH, frozen_transverse),
            )
        },
        "bound_transverse_conclusion": {
            "verdict": frozen_transverse["verdict"],
            "next_exact_gate_it_declared": frozen_transverse["resource_and_claim_boundaries"][
                "next_exact_gate"
            ],
            "its_rebuild_is_guarded_by_its_own_regression": True,
        },
        "universal_commutator_identity": commutator,
        "universal_coboundary_identity": coboundary,
        "general_bottom_character": faithfulness,
        "full_diagonal_locus": stratum_one,
        "two_scalar_locus": stratum_two,
        "off_normalized_principal_opens": off_normalized,
        "deterministic_degeneracy_scan": scan,
        "span_beta_e_Q5_is_not_the_right_invariant": span_note,
        "resource_and_claim_boundaries": {
            "solver_status": "NOT_RUN",
            "groebner_status": "NOT_RUN",
            "determinants_expanded_over_54_base_parameters": False,
            "four_determinant_zero_loci_solved": False,
            "degeneracy_locus_fully_stratified": False,
            "transverse_chart_globally_obstructed": False,
            "pair_or_triple_irreducible_branch_touched": False,
            "aligned_branch_or_Delta_align_touched": False,
            "state_native_D12_manifest_touched": False,
            "global_weak_weak_obstruction_claimed": False,
            "next_exact_gate": (
                "decide globally whether the Q-projection of ker M lies in "
                "K_delta=ker C(delta_Q), equivalently whether rank[M;C]=rank M; on "
                "delta_Q!=0 this reduces to containment in span(delta_Q), while on "
                "delta_Q=0 it is automatic because K_0=QQ^4.  Do not defend "
                "span(beta,e_Q5): the kernel provably leaves it and still commutes"
            ),
        },
        "gates": gates,
        "passed": True,
        "witness": None,
        "search_terminal": SEARCH_TERMINAL,
        "verdict": VERDICT,
        "claim_boundary": (
            "This exact certificate proves two universal identities and gives exact "
            "results on nested loci of the transverse scalar base.  Universal, over the "
            "whole base: the six Q commutator coefficients are "
            "x_j*(a_i-b_i)-x_i*(a_j-b_j), so a witness needs rank[M;C]>rank M rather "
            "than a vanishing determinant.  The commuting subspace is "
            "K_delta=ker C(delta_Q): it equals span(delta_Q) only when delta_Q is "
            "nonzero, and equals all of QQ^4 when delta_Q=0.  Beta=a-b is a global "
            "conjugation "
            "coboundary, so it satisfies every operator relation row everywhere and "
            "every commutator form annihilates it.  Consequently the entire equal-Q "
            "spectrum locus delta_Q=0 is witness-free.  Its five-dimensional full "
            "diagonal sublocus E={a_e=b_e} is therefore witness-free at every point.  "
            "The rank 127, the nullity five and the "
            "identification of the kernel with the tangent space of the bottom scalar "
            "locus are certified at three exact rational points of E, not proved "
            "locus-wide.  On the ten-dimensional two-scalar locus, where the "
            "upper character is itself a bottom scalar locus point, beta lies in the "
            "kernel everywhere, and rank 130, nullity two and ker M=span(beta,e_Q5) are "
            "certified at four exact rational points with delta_Q nonzero.  This locus "
            "also contains the six-dimensional same-couplings independent-Q5 subfamily "
            "T with delta_Q=0; T is witness-free throughout, and at one exact point of "
            "T minus E the rank is 127 and the kernel is the five-dimensional upper "
            "bottom-locus tangent space.  Witness freedom on the remaining nonzero-"
            "delta_Q part of S is pointwise, not locus-wide.  It also "
            "certifies, for the first time, full-rank splitting principal opens over "
            "non-normalized bottom characters.  It never combines alternative Eq113 or "
            "Eq139 readings.  It does not solve the four determinant-zero loci, does "
            "not stratify the whole degeneracy locus, does not obstruct the transverse "
            "chart or the weak/weak profile, does not touch the pair/triple-irreducible "
            "or aligned branches or the state-native D12 manifest, certifies no "
            "witness, and issues no SR2-V terminal.  The scan is a bounded "
            "deterministic search, not a global obstruction.  One recorded point "
            "shows that ker M can leave span(beta,e_Q5) and still commute, so that "
            "span is not the invariant a successor search should defend."
        ),
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def run(root: Path | None = None) -> dict[str, Any]:
    resolved_root = Path.cwd() if root is None else root
    payload = build_payload(resolved_root)
    target = resolved_root / RESULT_PATH
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return payload


if __name__ == "__main__":
    result = run()
    print(result["verdict"])
    print(result["semantic_digest_sha256"])
