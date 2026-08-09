"""Close the v0.4.2 955 search inside the declared mixed ``2 x 2`` ansatz.

The predecessor gate reduced the 262 mixed coordinates to 46 exact kernel
coordinates and measured five homogeneous linear residual entries of rank three.
This gate performs that deferred elimination and then analyses the resulting
bilinear CPOBC block without a polynomial solver.

The exact rank-three quotient has 43 coordinates and sends
``s19 -> 3*s21`` and ``t19,t21 -> 0``.  In that quotient all 24 reduced Q
commutator entries vanish identically.  The 954 CPOBC diagonal entries collapse
to 84 nonzero scalar multiples of only five monomials::

    s21*t11, s21*t15, s21*t16, s21*t18, s21*t22.

The branch ``s21 != 0`` therefore sets those five ``t`` coordinates to zero.
The remaining exact linear rows then force every ``t`` coordinate to zero and
place six ``s`` coordinates on one primitive integral direction.  On
``s21 = 0`` that direction vanishes and the same family loses one parameter.
Consequently the full solution set in the declared ansatz is exactly a
17-dimensional pure-upper linear family; the ``s21 = 0`` branch is its
16-dimensional hyperplane.  All 165 source nonsingularity occurrences reduce
to their nonzero diagonal characters there.

This is terminal only for the declared mixed ansatz.  The unrestricted
source-native slack system and the full 955 profile outside that ansatz remain
open.  No Groebner basis, saturation, finite-field, numerical or Sage run is
performed.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable
from fractions import Fraction
from pathlib import Path
from typing import Any

GLOBAL_REDUCTION_PATH = "results/v0.4.2_955_global_bilinear_reduction.json"
MIXED_MANIFEST_PATH = "results/v0.4.2_955_mixed_source_native_manifest.json"
RESULT_PATH = "results/v0.4.2_955_mixed_branch_closure.json"

SCHEMA = "final-theory-v042-955-mixed-branch-closure-v1"
VERDICT = "V042_955_MIXED_ANSATZ_17D_PURE_UPPER_COMMUTATIVE_TERMINAL_CERTIFIED"

PROFILE_BLOCKS = ("CPOBC", "strong_GC", "reachable_MSR_vector")

type Monomial = tuple[str, ...]
type Polynomial = dict[Monomial, Fraction]
type SparseRow = dict[int, Fraction]


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


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _add(left: Polynomial, right: Polynomial) -> Polynomial:
    result = dict(left)
    for monomial, coefficient in right.items():
        value = result.get(monomial, Fraction(0)) + coefficient
        if value:
            result[monomial] = value
        else:
            result.pop(monomial, None)
    return result


def _multiply(left: Polynomial, right: Polynomial) -> Polynomial:
    result: Polynomial = {}
    for left_monomial, left_coefficient in left.items():
        for right_monomial, right_coefficient in right.items():
            monomial = tuple(sorted(left_monomial + right_monomial))
            value = result.get(monomial, Fraction(0)) + left_coefficient * right_coefficient
            if value:
                result[monomial] = value
            else:
                result.pop(monomial, None)
    return result


def _parse(polynomial: Iterable[dict[str, Any]]) -> Polynomial:
    result: Polynomial = {}
    for term in polynomial:
        monomial: list[str] = []
        for factor in term["monomial"]:
            monomial.extend([str(factor["variable"])] * int(factor["exponent"]))
        key = tuple(sorted(monomial))
        coefficient = Fraction(str(term["coefficient"]))
        result = _add(result, {key: coefficient})
    return result


def _substitute(polynomial: Polynomial, substitution: dict[str, Polynomial]) -> Polynomial:
    result: Polynomial = {}
    for monomial, coefficient in polynomial.items():
        accumulator: Polynomial = {(): coefficient}
        for variable in monomial:
            accumulator = _multiply(accumulator, substitution[variable])
            if not accumulator:
                break
        result = _add(result, accumulator)
    return result


def _specialise(polynomial: Polynomial, zero_variables: set[str]) -> Polynomial:
    return {
        monomial: coefficient
        for monomial, coefficient in polynomial.items()
        if not any(variable in zero_variables for variable in monomial)
    }


def _emit(polynomial: Polynomial) -> list[dict[str, Any]]:
    emitted: list[dict[str, Any]] = []
    for monomial in sorted(polynomial, key=lambda value: (len(value), value)):
        counts = Counter(monomial)
        emitted.append(
            {
                "coefficient": str(polynomial[monomial]),
                "monomial": [
                    {"variable": variable, "exponent": counts[variable]}
                    for variable in sorted(counts)
                ],
            }
        )
    return emitted


def _reduced_row_echelon(rows: Iterable[SparseRow]) -> dict[int, SparseRow]:
    basis: dict[int, SparseRow] = {}
    for source in rows:
        row = dict(source)
        while row:
            pivot = min(row)
            if pivot not in basis:
                scale = row[pivot]
                basis[pivot] = {column: value / scale for column, value in row.items()}
                break
            scale = row[pivot]
            for column, value in basis[pivot].items():
                updated = row.get(column, Fraction(0)) - scale * value
                if updated:
                    row[column] = updated
                else:
                    row.pop(column, None)
    for pivot in sorted(basis, reverse=True):
        row = basis[pivot]
        for other in sorted(basis):
            if other <= pivot:
                continue
            scale = row.get(other)
            if not scale:
                continue
            for column, value in basis[other].items():
                updated = row.get(column, Fraction(0)) - scale * value
                if updated:
                    row[column] = updated
                else:
                    row.pop(column, None)
    return basis


def _linear_row(polynomial: Polynomial, variable_index: dict[str, int]) -> SparseRow | None:
    if not polynomial or any(len(monomial) != 1 for monomial in polynomial):
        return None
    return {
        variable_index[monomial[0]]: coefficient for monomial, coefficient in polynomial.items()
    }


def _rref_payload(basis: dict[int, SparseRow], variables: list[str]) -> list[dict[str, str]]:
    return [
        {variables[column]: str(value) for column, value in sorted(basis[pivot].items())}
        for pivot in sorted(basis)
    ]


def _linear_parameterisation(
    rows: Iterable[SparseRow], variables: list[str]
) -> tuple[dict[str, Polynomial], dict[int, SparseRow], list[str]]:
    basis = _reduced_row_echelon(rows)
    free_columns = [column for column in range(len(variables)) if column not in basis]
    substitution: dict[str, Polynomial] = {
        variables[column]: {(variables[column],): Fraction(1)} for column in free_columns
    }
    for pivot, row in basis.items():
        substitution[variables[pivot]] = {
            (variables[column],): -coefficient
            for column, coefficient in row.items()
            if column != pivot and coefficient
        }
    return substitution, basis, [variables[column] for column in free_columns]


def _entry_identifier(record: dict[str, Any], entry: str) -> dict[str, Any]:
    return {
        **{
            key: record[key]
            for key in ("relation_id", "equation_id", "constraint_id", "source_id", "pair")
            if key in record
        },
        "entry": entry,
    }


def _transformed_entries(
    predecessor: dict[str, Any], substitution: dict[str, Polynomial], block: str
) -> list[tuple[dict[str, Any], Polynomial]]:
    result: list[tuple[dict[str, Any], Polynomial]] = []
    records = predecessor["reduced_system"]["blocks"][block]["records"]
    for record in records:
        for entry, emitted in sorted(record["entries"].items()):
            result.append(
                (_entry_identifier(record, entry), _substitute(_parse(emitted), substitution))
            )
    return result


def _branch_census(
    entries: list[tuple[dict[str, Any], Polynomial]], zero_variables: set[str]
) -> dict[str, Any]:
    surviving = [
        (identifier, _specialise(polynomial, zero_variables)) for identifier, polynomial in entries
    ]
    surviving = [(identifier, polynomial) for identifier, polynomial in surviving if polynomial]
    degrees = Counter(max(len(monomial) for monomial in polynomial) for _, polynomial in surviving)
    return {
        "input_entries": len(entries),
        "surviving_entries": len(surviving),
        "total_terms": sum(len(polynomial) for _, polynomial in surviving),
        "maximum_terms_per_entry": max((len(polynomial) for _, polynomial in surviving), default=0),
        "degree_histogram": {str(degree): count for degree, count in sorted(degrees.items())},
    }


def compile_mixed_branch_closure_v042(root: Path) -> dict[str, Any]:
    """Compile the exact 43-variable quotient and mixed-ansatz closure certificate."""

    paths = {
        GLOBAL_REDUCTION_PATH: root / GLOBAL_REDUCTION_PATH,
        MIXED_MANIFEST_PATH: root / MIXED_MANIFEST_PATH,
    }
    predecessor = _load(paths[GLOBAL_REDUCTION_PATH])
    manifest = _load(paths[MIXED_MANIFEST_PATH])
    for name, artifact in ((GLOBAL_REDUCTION_PATH, predecessor), (MIXED_MANIFEST_PATH, manifest)):
        if artifact.get("semantic_digest_sha256") != _semantic_digest(artifact):
            raise AssertionError(f"{name} is not at its frozen semantic digest")
    if predecessor.get("verdict") != (
        "V042_955_GLOBAL_BILINEAR_REDUCTION_262_TO_46_CERTIFIED_NONTERMINAL"
    ):
        raise AssertionError("the predecessor global-reduction verdict changed")

    variables = [str(value) for value in predecessor["reduced_system"]["variables"]]
    if variables != [f"s{axis}" for axis in range(23)] + [f"t{axis}" for axis in range(23)]:
        raise AssertionError("the 46 predecessor coordinates changed")
    variable_index = {variable: index for index, variable in enumerate(variables)}

    linear_records = predecessor["reduced_system"]["linear_part"]["rows"]
    linear_rows: list[SparseRow] = []
    for record in linear_records:
        linear_rows.append(
            {
                variable_index[str(variable)]: Fraction(str(coefficient))
                for variable, coefficient in record["coefficients"]
            }
        )
    substitution, linear_basis, free_variables = _linear_parameterisation(linear_rows, variables)
    pivot_variables = [variables[column] for column in sorted(linear_basis)]
    if pivot_variables != ["s19", "t19", "t21"]:
        raise AssertionError(f"unexpected rank-three pivots: {pivot_variables}")
    expected_substitution = {
        "s19": {("s21",): Fraction(3)},
        "t19": {},
        "t21": {},
    }
    if {variable: substitution[variable] for variable in pivot_variables} != expected_substitution:
        raise AssertionError("the deferred rank-three substitution changed")
    if len(free_variables) != 43:
        raise AssertionError("the rank-three quotient must have 43 free coordinates")

    transformed = {
        block: _transformed_entries(predecessor, substitution, block) for block in PROFILE_BLOCKS
    }

    commutator_labels: list[dict[str, Any]] = []
    commutator_remainders: list[Polynomial] = []
    for record in predecessor["reduced_Q_commutator"]["records"]:
        for entry, emitted in sorted(record["entries"].items()):
            commutator_labels.append(_entry_identifier(record, entry))
            commutator_remainders.append(_substitute(_parse(emitted), substitution))
    if len(commutator_remainders) != 24 or any(commutator_remainders):
        raise AssertionError("the Q commutator does not vanish in the exact linear quotient")

    cpobc_surviving: list[tuple[dict[str, Any], Polynomial]] = [
        (identifier, polynomial) for identifier, polynomial in transformed["CPOBC"] if polynomial
    ]
    if len(transformed["CPOBC"]) != 954 or len(cpobc_surviving) != 84:
        raise AssertionError("the 954 -> 84 CPOBC quotient census changed")
    monomial_counts: Counter[Monomial] = Counter()
    selected_monomials: dict[Monomial, dict[str, Any]] = {}
    for identifier, polynomial in cpobc_surviving:
        if len(polynomial) != 1:
            raise AssertionError("each surviving CPOBC entry must be a scalar monomial")
        monomial, coefficient = next(iter(polynomial.items()))
        if len(monomial) != 2 or monomial[0] != "s21":
            raise AssertionError(f"unexpected CPOBC quotient monomial: {monomial}")
        monomial_counts[monomial] += 1
        selected_monomials.setdefault(monomial, {**identifier, "coefficient": str(coefficient)})
    expected_monomials = {
        ("s21", "t11"),
        ("s21", "t15"),
        ("s21", "t16"),
        ("s21", "t18"),
        ("s21", "t22"),
    }
    if set(monomial_counts) != expected_monomials:
        raise AssertionError("the five CPOBC quotient monomials changed")

    # On the s21 != 0 branch CPOBC forces five t coordinates to vanish.  Every
    # remaining profile equation is linear; its closure is a 17-dimensional
    # pure-upper family with s22 as the final direction parameter.
    cpobc_forced_t = {monomial[1] for monomial in expected_monomials}
    nonzero_variables = [variable for variable in free_variables if variable not in cpobc_forced_t]
    nonzero_index = {variable: index for index, variable in enumerate(nonzero_variables)}
    nonzero_linear_rows: list[SparseRow] = []
    nonzero_linear_counts: Counter[str] = Counter()
    nonzero_branch_entries: list[tuple[str, dict[str, Any], Polynomial]] = []
    for block in PROFILE_BLOCKS:
        for identifier, polynomial in transformed[block]:
            specialised = _specialise(polynomial, cpobc_forced_t)
            if not specialised:
                continue
            nonzero_branch_entries.append((block, identifier, specialised))
            row = _linear_row(specialised, nonzero_index)
            if row is None:
                raise AssertionError("the five-t-zero branch acquired a nonlinear residual")
            nonzero_linear_rows.append(row)
            nonzero_linear_counts[block] += 1
    nonzero_substitution, nonzero_basis, nonzero_free = _linear_parameterisation(
        nonzero_linear_rows, nonzero_variables
    )
    nonzero_pivots = [nonzero_variables[column] for column in sorted(nonzero_basis)]
    expected_nonzero_pivots = ["s11", "s15", "s16", "s18", "s21"] + [
        f"t{axis}" for axis in range(23) if axis not in (11, 15, 16, 18, 19, 21, 22)
    ]
    if nonzero_pivots != expected_nonzero_pivots:
        raise AssertionError("the five-t-zero branch linear closure changed")
    expected_nonzero_free = [
        "s0",
        "s1",
        "s2",
        "s3",
        "s4",
        "s5",
        "s6",
        "s7",
        "s8",
        "s9",
        "s10",
        "s12",
        "s13",
        "s14",
        "s17",
        "s20",
        "s22",
    ]
    if nonzero_free != expected_nonzero_free:
        raise AssertionError("the 17 free coordinates on the pure-upper closure changed")
    expected_direction = {
        "s11": {("s22",): Fraction(5, 4)},
        "s15": {("s22",): Fraction(1)},
        "s16": {("s22",): Fraction(1)},
        "s18": {("s22",): Fraction(7, 6)},
        "s21": {("s22",): Fraction(1, 12)},
    }
    if {variable: nonzero_substitution[variable] for variable in expected_direction} != (
        expected_direction
    ):
        raise AssertionError("the primitive pure-upper direction changed")
    if any(
        _substitute(polynomial, nonzero_substitution)
        for _block, _identifier, polynomial in nonzero_branch_entries
    ):
        raise AssertionError("the 17-dimensional branch closure retains a residual")

    # On s21 = 0, the full profile becomes linear plus five harmless bilinear
    # reachable-MSR entries.  Its linear row space forces all t coordinates and
    # five additional s coordinates to zero.
    closed_branch_zero = {"s21"}
    closed_variables = [
        variable for variable in free_variables if variable not in closed_branch_zero
    ]
    closed_index = {variable: index for index, variable in enumerate(closed_variables)}
    closed_linear_rows: list[SparseRow] = []
    closed_linear_counts: Counter[str] = Counter()
    for block in PROFILE_BLOCKS:
        for _identifier, polynomial in transformed[block]:
            specialised = _specialise(polynomial, closed_branch_zero)
            row = _linear_row(specialised, closed_index)
            if row is not None:
                closed_linear_rows.append(row)
                closed_linear_counts[block] += 1
    closed_basis = _reduced_row_echelon(closed_linear_rows)
    closed_pivots = [closed_variables[column] for column in sorted(closed_basis)]
    expected_closed_pivots = ["s11", "s15", "s16", "s18", "s22"] + [
        f"t{axis}" for axis in range(23) if axis not in (19, 21)
    ]
    if closed_pivots != expected_closed_pivots:
        raise AssertionError("the s21=0 branch forced-coordinate set changed")
    if any(len(row) != 1 for row in closed_basis.values()):
        raise AssertionError("the closed branch no longer spans coordinate equations")

    closed_substitution, _closed_basis_check, closed_free = _linear_parameterisation(
        closed_linear_rows, closed_variables
    )
    if closed_free != expected_nonzero_free[:-1]:
        raise AssertionError("the s21=0 hyperplane coordinates changed")
    closed_family_substitution: dict[str, Polynomial] = {"s21": {}}
    closed_family_substitution.update(closed_substitution)
    if any(
        _substitute(polynomial, closed_family_substitution)
        for block in PROFILE_BLOCKS
        for _identifier, polynomial in transformed[block]
    ):
        raise AssertionError("the 16-dimensional s21=0 hyperplane retains a residual")

    # The nonzero-branch closure already contains the s21=0 branch at s22=0.
    # Lift its parameterisation back to all 43 quotient coordinates and verify
    # the complete reduced profile at a general family point.
    family_substitution: dict[str, Polynomial] = {}
    for variable in free_variables:
        if variable in cpobc_forced_t:
            family_substitution[variable] = {}
        else:
            family_substitution[variable] = nonzero_substitution[variable]
    if any(family_substitution[f"t{axis}"] for axis in range(23) if axis not in (19, 21)):
        raise AssertionError("the classified family is not pure upper")
    residual_failures: list[dict[str, Any]] = []
    entries_checked = 0
    for block in PROFILE_BLOCKS:
        for identifier, polynomial in transformed[block]:
            entries_checked += 1
            if _substitute(polynomial, family_substitution):
                residual_failures.append({"block": block, **identifier})
    if entries_checked != 1933 or residual_failures:
        raise AssertionError("the proposed 17-dimensional family does not annihilate the system")

    # Carry every determinant factor into the 43-coordinate quotient.  This is
    # deliberately performed before using the solution classification, so the
    # localisation reduction is independently visible in the artifact.
    names = manifest["variables"]["names"]
    orbits = sorted(str(name)[2:] for name in names if str(name).startswith("x:"))
    if len(orbits) != 131:
        raise AssertionError("expected 131 quotient orbits")
    x_basis = predecessor["cpobc_kernels"]["x"]["primitive_integral_basis"]
    y_basis = predecessor["cpobc_kernels"]["y"]["primitive_integral_basis"]
    diagonal = manifest["variables"]["CSG_diagonal_character"]
    determinant_records: list[dict[str, Any]] = []
    automatic_orbits: list[str] = []
    active_polynomial_keys: set[str] = set()
    for orbit_index, orbit in enumerate(orbits):
        x_polynomial: Polynomial = {
            (f"s{axis}",): Fraction(vector[orbit_index])
            for axis, vector in enumerate(x_basis)
            if vector[orbit_index]
        }
        y_polynomial: Polynomial = {
            (f"t{axis}",): Fraction(vector[orbit_index])
            for axis, vector in enumerate(y_basis)
            if vector[orbit_index]
        }
        reduced_x = _substitute(x_polynomial, substitution)
        reduced_y = _substitute(y_polynomial, substitution)
        determinant = _add(
            {(): Fraction(str(diagonal[orbit]))},
            {
                monomial: -coefficient
                for monomial, coefficient in _multiply(reduced_x, reduced_y).items()
            },
        )
        active = len(determinant) > 1
        if active:
            active_polynomial_keys.add(_canonical_json(_emit(determinant)))
        else:
            automatic_orbits.append(orbit)
        determinant_records.append(
            {
                "orbit_id": orbit,
                "active_after_linear_elimination": active,
                "factor": _emit(determinant),
            }
        )
        final_determinant = _substitute(determinant, family_substitution)
        expected_constant = {(): Fraction(str(diagonal[orbit]))}
        if final_determinant != expected_constant or not expected_constant[()]:
            raise AssertionError(f"nonsingularity did not become automatic on {orbit}")
    if len(automatic_orbits) != 88 or len(active_polynomial_keys) != 26:
        raise AssertionError("the reduced determinant census changed")
    raw_occurrences = manifest["nonsingularity_localisation"]["raw_occurrence_factors"]
    active_orbits = {
        record["orbit_id"]
        for record in determinant_records
        if record["active_after_linear_elimination"]
    }
    active_raw_occurrences = sum(
        1 for record in raw_occurrences if str(record["orbit_id"]) in active_orbits
    )
    if len(raw_occurrences) != 165 or active_raw_occurrences != 50:
        raise AssertionError("the 165-occurrence localisation binding changed")

    branch_census = {
        "s21_zero": {
            block: _branch_census(entries, closed_branch_zero)
            for block, entries in transformed.items()
        },
        "five_t_zero": {
            block: _branch_census(entries, cpobc_forced_t) for block, entries in transformed.items()
        },
    }
    diagonal_histogram = Counter(str(value) for value in diagonal.values())

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "scope": {
            "finite_stages": "n<=4",
            "dimension": 2,
            "field": "QQ",
            "identification_mode": "ON_QUOTIENT",
            "ansatz": "A_e=[[p_e,x_[e]],[y_[e],1]], p_e=CSG(t_j=1)",
        },
        "source_artifact_sha256": {path: _sha256(value) for path, value in paths.items()},
        "predecessor_binding": {
            "kind": "CANONICAL_JSON_SEMANTIC_DIGEST",
            GLOBAL_REDUCTION_PATH: predecessor["semantic_digest_sha256"],
            MIXED_MANIFEST_PATH: manifest["semantic_digest_sha256"],
        },
        "linear_rank_three_elimination": {
            "input_coordinates": 46,
            "linear_entry_count": len(linear_rows),
            "rank": len(linear_basis),
            "pivot_coordinates": pivot_variables,
            "free_coordinates": free_variables,
            "output_coordinates": len(free_variables),
            "substitution": {
                variable: _emit(substitution[variable]) for variable in pivot_variables
            },
            "rref": _rref_payload(linear_basis, variables),
            "exact_QQ": True,
        },
        "Q_commutator_after_linear_elimination": {
            "entries_before": predecessor["reduced_Q_commutator"]["surviving_entries"],
            "terms_before": predecessor["reduced_Q_commutator"]["total_terms"],
            "entries_checked": len(commutator_remainders),
            "nonzero_remainders": sum(bool(value) for value in commutator_remainders),
            "checked_labels_sha256": _digest(commutator_labels),
            "identically_zero_on_the_rank_three_linear_locus": True,
            "conclusion": (
                "Every solution of the 955 profile inside the declared mixed ansatz has "
                "pairwise commuting Q1,...,Q4; no CPOBC branch split is needed for this conclusion."
            ),
        },
        "CPOBC_after_linear_elimination": {
            "input_diagonal_entries": len(transformed["CPOBC"]),
            "identically_zero_entries": len(transformed["CPOBC"]) - len(cpobc_surviving),
            "surviving_scalar_monomial_instances": len(cpobc_surviving),
            "surviving_terms": sum(len(value) for _, value in cpobc_surviving),
            "unique_monomial_equations": [
                {
                    "monomial": "*".join(monomial),
                    "instances": monomial_counts[monomial],
                    "selected_source_equation": selected_monomials[monomial],
                }
                for monomial in sorted(monomial_counts)
            ],
            "equivalent_system": ["s21*t11", "s21*t15", "s21*t16", "s21*t18", "s21*t22"],
        },
        "exact_branch_closure": {
            "case_split": "s21=0 OR s21!=0",
            "s21_nonzero_branch": {
                "CPOBC_forces_zero": sorted(cpobc_forced_t),
                "branch_census": branch_census["five_t_zero"],
                "homogeneous_linear_entry_counts": dict(sorted(nonzero_linear_counts.items())),
                "surviving_profile_entries": len(nonzero_branch_entries),
                "combined_linear_rank": len(nonzero_basis),
                "combined_rref": _rref_payload(nonzero_basis, nonzero_variables),
                "pivot_coordinates": nonzero_pivots,
                "free_coordinates_on_closure": nonzero_free,
                "branch_restriction": "s22!=0 (equivalently s21=s22/12!=0)",
                "closure_dimension": len(nonzero_free),
                "remaining_residuals_after_linear_parameterisation": 0,
            },
            "s21_zero_branch": {
                "branch_census": branch_census["s21_zero"],
                "homogeneous_linear_entry_counts": dict(sorted(closed_linear_counts.items())),
                "combined_linear_rank": len(closed_basis),
                "combined_rref": _rref_payload(closed_basis, closed_variables),
                "forced_zero_after_s21": closed_pivots,
                "free_coordinates": closed_free,
                "dimension": len(closed_free),
                "relation_to_nonzero_branch_closure": "the s22=0 hyperplane",
                "remaining_nonlinear_entries_vanish_after_forced_zeros": True,
            },
        },
        "solution_classification": {
            "solution_set_inside_declared_mixed_ansatz": "17_DIMENSIONAL_PURE_UPPER_LINEAR_FAMILY",
            "free_coordinates": nonzero_free,
            "free_parameter_count": len(nonzero_free),
            "zero_coordinates_in_43_coordinate_quotient": [
                f"t{axis}" for axis in range(23) if axis not in (19, 21)
            ],
            "dependent_coordinates_in_43_coordinate_quotient": {
                "s11": "5/4*s22",
                "s15": "s22",
                "s16": "s22",
                "s18": "7/6*s22",
                "s21": "1/12*s22",
            },
            "primitive_integral_direction_with_u_equal_s21": {
                "s11": "15*u",
                "s15": "12*u",
                "s16": "12*u",
                "s18": "14*u",
                "s21": "u",
                "s22": "12*u",
            },
            "rank_three_dependent_coordinates": {"s19": "3*s21", "t19": "0", "t21": "0"},
            "all_y_coordinates_zero": True,
            "remote_or_disconnected_x_nonzero_y_nonzero_components": 0,
            "reduced_profile_entries_checked_at_general_family_point": entries_checked,
            "residual_failures": residual_failures,
            "every_assignment_of_the_17_free_coordinates_is_a_solution": True,
        },
        "nonsingularity_localisation": {
            "raw_source_occurrences": len(raw_occurrences),
            "distinct_ON_quotient_factors": len(determinant_records),
            "automatic_after_rank_three_elimination": len(automatic_orbits),
            "active_after_rank_three_elimination": len(active_orbits),
            "active_raw_source_occurrences": active_raw_occurrences,
            "unique_active_factor_polynomials": len(active_polynomial_keys),
            "reduced_factors": determinant_records,
            "at_classified_solution_family": {
                "all_factors_equal_nonzero_p_e": True,
                "diagonal_character_histogram": dict(sorted(diagonal_histogram.items())),
                "raw_occurrences_satisfied": len(raw_occurrences),
                "failures": 0,
            },
        },
        "solver_status": {
            "Groebner_or_saturation_runs": 0,
            "finite_field_runs": 0,
            "numerical_runs": 0,
            "Sage_runs": 0,
            "solver_run": False,
        },
        "claim_boundary": [
            "This is an exact QQ linear elimination and a two-branch field case split.",
            "It is terminal for the declared 262-coordinate mixed ansatz only.",
            (
                "It proves no theorem for the unrestricted source-native slack system outside "
                "that ansatz."
            ),
            "The full source-native 955 profile therefore remains open.",
            "The classification includes and verifies all 165 source nonsingularity occurrences.",
            "No noncommutative witness exists inside the declared mixed ansatz.",
        ],
        "commutativity_proved_for_955_profile_inside_declared_mixed_ansatz": True,
        "commutativity_proved_for_unrestricted_source_native_955_profile": False,
        "witness_certified": False,
        "mixed_ansatz_search_terminal": True,
        "full_955_search_terminal": False,
        "passed": True,
        "verdict": VERDICT,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def write_mixed_branch_closure_v042(root: Path) -> Path:
    payload = compile_mixed_branch_closure_v042(root)
    destination = root / RESULT_PATH
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_mixed_branch_closure_v042(repository_root))
