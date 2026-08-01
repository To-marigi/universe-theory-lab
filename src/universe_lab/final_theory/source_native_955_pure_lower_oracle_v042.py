"""Fail-closed pure-lower oracle for the checked-in 955 mixed manifest.

The nonlinear source-native manifest uses ``A_e=[[p_e,x_e],[y_e,1]]``.
This independent oracle specializes *that checked-in manifest* to ``x=0``.
It does not import the tangent scout implementation or its rank routines:
the only auxiliary input is its emitted selected-row certificate, which is
rechecked against the nonlinear polynomials and by a fresh SymPy ``QQ`` rank.

The result is deliberately narrow.  It proves that the pure lower-triangular
slice of this 262-scalar mixed ansatz has only ``y=0`` solutions, hence has
diagonal commuting Q matrices.  It says nothing about mixed ``x!=0, y!=0``
points or the unrestricted source-native 955 system.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import sympy as sp

MIXED_MANIFEST_PATH = "results/v0.4.2_955_mixed_source_native_manifest.json"
TANGENT_CERTIFICATE_PATH = "results/v0.4.2_955_mixed_xy_tangent_scout.json"
RESULT_PATH = "results/v0.4.2_955_pure_lower_oracle.json"
SCHEMA = "final-theory-v042-955-pure-lower-oracle-v1"
VERDICT = "V042_955_PURE_LOWER_ORACLE_CERTIFIED"

SerializedPolynomial = list[dict[str, Any]]
SparseRow = dict[str, Fraction]


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


def semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def _normalise_polynomial(
    polynomial: SerializedPolynomial,
) -> dict[tuple[tuple[str, int], ...], Fraction]:
    """Parse the manifest's sparse QQ polynomial and collect equal monomials."""

    result: dict[tuple[tuple[str, int], ...], Fraction] = {}
    for term in polynomial:
        coefficient = Fraction(str(term["coefficient"]))
        factors = term["monomial"]
        if not isinstance(factors, list):
            raise AssertionError("polynomial monomial must be a list")
        monomial = tuple(
            sorted((str(factor["variable"]), int(factor["exponent"])) for factor in factors)
        )
        if any(exponent <= 0 for _, exponent in monomial):
            raise AssertionError("manifest monomial exponents must be positive")
        result[monomial] = result.get(monomial, Fraction()) + coefficient
    return {monomial: coefficient for monomial, coefficient in result.items() if coefficient}


def _specialise_x_zero(
    polynomial: SerializedPolynomial,
) -> dict[tuple[tuple[str, int], ...], Fraction]:
    """Set every x variable to zero, retaining and validating y-only terms."""

    specialized: dict[tuple[tuple[str, int], ...], Fraction] = {}
    for monomial, coefficient in _normalise_polynomial(polynomial).items():
        if any(variable.startswith("x:") for variable, _ in monomial):
            continue
        if any(not variable.startswith("y:") for variable, _ in monomial):
            raise AssertionError(f"unexpected non-y variable after x=0 specialization: {monomial}")
        specialized[monomial] = specialized.get(monomial, Fraction()) + coefficient
    return {monomial: coefficient for monomial, coefficient in specialized.items() if coefficient}


def _degree(monomial: tuple[tuple[str, int], ...]) -> int:
    return sum(exponent for _, exponent in monomial)


def _linear_y_row(polynomial: SerializedPolynomial) -> SparseRow:
    """Require an exactly homogeneous linear polynomial in the y orbit variables."""

    result: SparseRow = {}
    for monomial, coefficient in _specialise_x_zero(polynomial).items():
        if len(monomial) != 1 or _degree(monomial) != 1:
            raise AssertionError(f"not homogeneous linear in y: {monomial}")
        variable, exponent = monomial[0]
        if exponent != 1 or not variable.startswith("y:"):
            raise AssertionError(f"not a y variable: {monomial}")
        orbit = variable.removeprefix("y:")
        result[orbit] = result.get(orbit, Fraction()) + coefficient
    return {orbit: coefficient for orbit, coefficient in result.items() if coefficient}


def _assert_zero_after_x_zero(polynomial: SerializedPolynomial, label: str) -> None:
    if _specialise_x_zero(polynomial):
        raise AssertionError(f"{label} must vanish identically after x=0")


def _assert_zero_at_diagonal_base(polynomial: SerializedPolynomial, label: str) -> None:
    """Set both x and y to zero and reject any surviving constant."""

    normalized = _normalise_polynomial(polynomial)
    if normalized.get((), Fraction()):
        raise AssertionError(f"{label} must vanish at x=y=0")


def _all_degree_at_most_one(polynomial: SerializedPolynomial, label: str) -> int:
    specialized = _specialise_x_zero(polynomial)
    if specialized.get((), Fraction()):
        raise AssertionError(f"{label} has a nonzero constant after x=0")
    degrees = [_degree(monomial) for monomial in specialized]
    maximum = max(degrees, default=0)
    if maximum > 1:
        raise AssertionError(f"{label} has degree {maximum} after x=0")
    return maximum


def _certificate_row(record: dict[str, Any]) -> SparseRow:
    coefficients = record.get("coefficients")
    if not isinstance(coefficients, list):
        raise AssertionError("selected certificate row must have coefficients")
    row: SparseRow = {}
    for item in coefficients:
        if not isinstance(item, list) or len(item) != 2:
            raise AssertionError("certificate coefficient must be [orbit, QQ]")
        orbit, coefficient = str(item[0]), Fraction(str(item[1]))
        row[orbit] = row.get(orbit, Fraction()) + coefficient
    return {orbit: coefficient for orbit, coefficient in row.items() if coefficient}


def _row_to_json(row: SparseRow) -> list[list[str]]:
    return [[orbit, str(row[orbit])] for orbit in sorted(row)]


def _source_lower_rows(manifest: dict[str, Any]) -> dict[str, SparseRow]:
    rows: dict[str, SparseRow] = {}
    for record in manifest["residual_blocks"]["CPOBC"]["records"]:
        label = f"{record['relation_id']}:{record['equation_id']}"
        rows[label] = _linear_y_row(record["entries"]["10"])
    for record in manifest["residual_blocks"]["reachable_MSR_vector"]["records"]:
        label = f"{record['constraint_id']}:reachable-lower-linearisation"
        rows[label] = _linear_y_row(record["entries"]["1"])
    return rows


def _check_specialization(manifest: dict[str, Any]) -> dict[str, Any]:
    blocks = manifest.get("residual_blocks")
    if not isinstance(blocks, dict):
        raise AssertionError("mixed manifest residual_blocks missing")

    counts: dict[str, int] = {}
    max_degrees: dict[str, int] = {}
    for block_name, expected_count in (("CPOBC", 783), ("strong_GC", 320)):
        records = blocks[block_name]["records"]
        if len(records) != expected_count:
            raise AssertionError(f"{block_name} record count changed")
        maximum = 0
        for record in records:
            for entry in ("00", "01", "11"):
                _assert_zero_after_x_zero(record["entries"][entry], f"{block_name}:{entry}")
            maximum = max(
                maximum, _all_degree_at_most_one(record["entries"]["10"], f"{block_name}:10")
            )
        counts[block_name] = len(records)
        max_degrees[block_name] = maximum

    reachable = blocks["reachable_MSR_vector"]["records"]
    if len(reachable) != 24:
        raise AssertionError("reachable-MSR vector record count changed")
    maximum = 0
    for record in reachable:
        _assert_zero_after_x_zero(record["entries"]["0"], "reachable-MSR:0")
        maximum = max(maximum, _all_degree_at_most_one(record["entries"]["1"], "reachable-MSR:1"))
    counts["reachable_MSR_vector"] = len(reachable)
    max_degrees["reachable_MSR_vector"] = maximum

    # This is the independent strong-MSR escape gate.  It is not imposed as a
    # relation: the first source's D_p has a constant (2,2)=1 entry throughout
    # the mixed ansatz and therefore on the pure-lower slice.
    operator = blocks["reachable_MSR_operator"]["records"]
    p1 = next((record for record in operator if record["constraint_id"] == "msr:p1-0"), None)
    if p1 is None:
        raise AssertionError("p1 reachable-MSR operator record missing")
    _assert_zero_after_x_zero(p1["entries"]["00"], "p1 operator 00")
    _assert_zero_after_x_zero(p1["entries"]["01"], "p1 operator 01")
    if _specialise_x_zero(p1["entries"]["11"]) != {(): Fraction(1)}:
        raise AssertionError("p1 operator (2,2) must remain the constant one")

    return {
        "record_counts": counts,
        "max_y_degree": max_degrees,
        "zero_entries_after_x_zero": {
            "CPOBC": ["00", "01", "11"],
            "strong_GC": ["00", "01", "11"],
            "reachable_MSR_vector": ["0"],
        },
        "lower_entries_checked": {
            "CPOBC": "10",
            "strong_GC": "10",
            "reachable_MSR_vector": "1",
        },
        "p1_nonzero_operator_gate": {
            "record": "msr:p1-0",
            "entry": "11",
            "specialized_polynomial": [{"coefficient": "1", "monomial": []}],
        },
    }


def build_payload(root: Path) -> dict[str, Any]:
    manifest_path = root / MIXED_MANIFEST_PATH
    tangent_path = root / TANGENT_CERTIFICATE_PATH
    manifest = _load(manifest_path)
    tangent = _load(tangent_path)
    if not (
        manifest.get("schema_version") == "final-theory-v042-955-mixed-source-native-manifest-v1"
        and manifest.get("verdict")
        == "V042_955_MIXED_SOURCE_NATIVE_SCALAR_MANIFEST_READY_NO_SOLVER_RUN"
        and manifest.get("passed") is True
        and manifest.get("semantic_digest_sha256") == semantic_digest(manifest)
    ):
        raise AssertionError("mixed manifest failed its schema/verdict/digest gate")
    if not (
        tangent.get("schema_version") == "final-theory-v042-955-mixed-xy-tangent-scout-v2"
        and tangent.get("verdict") == "V042_955_MIXED_XY_SCOUT_NO_WITNESS_OPEN"
        and tangent.get("passed") is True
        and tangent.get("semantic_digest_sha256") == semantic_digest(tangent)
    ):
        raise AssertionError("tangent certificate failed its schema/verdict/digest gate")
    if manifest.get("profile") != "strong_GC__reachable_state_MSR":
        raise AssertionError("wrong mixed manifest profile")

    specialization = _check_specialization(manifest)
    source_rows = _source_lower_rows(manifest)

    certificate = tangent["exact_linear_blocks"]["lower"]["full_column_rank_certificate"]
    variables = [str(variable) for variable in certificate["ordered_variables"]]
    selected = certificate["selected_rows"]
    if len(variables) != 131 or len(set(variables)) != 131 or len(selected) != 131:
        raise AssertionError("expected 131 independent lower variables and rows")
    if certificate.get("selected_row_kind_counts") != {"CPOBC": 108, "reachable_MSR": 23}:
        raise AssertionError("the exact 108+23 selected-row census changed")

    diagonal_character = manifest.get("variables", {}).get("CSG_diagonal_character", {})
    localisations = manifest.get("nonsingularity_localisation", {})
    if (
        not isinstance(diagonal_character, dict)
        or len(diagonal_character) != 131
        or any(Fraction(str(value)) == 0 for value in diagonal_character.values())
        or localisations.get("raw_occurrences") != 165
        or localisations.get("distinct_ON_quotient_factors") != 131
    ):
        raise AssertionError("pure-lower nonsingularity binding failed")

    selected_rows: list[SparseRow] = []
    matched_labels: list[str] = []
    for record in selected:
        label = str(record["label"])
        if label not in source_rows:
            raise AssertionError(
                f"selected tangent row absent from nonlinear source manifest: {label}"
            )
        expected = _certificate_row(record)
        actual = source_rows[label]
        if actual != expected:
            raise AssertionError(f"nonlinear pure-lower coefficient mismatch: {label}")
        if not actual:
            raise AssertionError(f"selected row cannot be zero: {label}")
        selected_rows.append(actual)
        matched_labels.append(label)

    index = {variable: column for column, variable in enumerate(variables)}
    entries: dict[tuple[int, int], sp.Rational] = {}
    for row_index, row in enumerate(selected_rows):
        for variable, coefficient in row.items():
            if variable not in index:
                raise AssertionError(
                    f"selected coefficient outside certificate variables: {variable}"
                )
            entries[row_index, index[variable]] = sp.Rational(
                coefficient.numerator, coefficient.denominator
            )
    matrix = sp.SparseMatrix(len(selected_rows), len(variables), entries)
    rank = int(matrix.rank())
    if rank != 131:
        raise AssertionError(f"independent SymPy QQ rank must be 131, got {rank}")

    # The four source Q matrices are diagonal at the forced x=y=0 point.  Verify
    # this directly by rejecting a constant term in every commutator entry.  The
    # commutators need not vanish identically for arbitrary y on x=0.
    commutators = manifest["Q_commutator_polynomials"]["records"]
    if len(commutators) != 6:
        raise AssertionError("six Q commutators required")
    for record in commutators:
        for entry, polynomial in record["entries"].items():
            _assert_zero_at_diagonal_base(polynomial, f"Q commutator {record['pair']}:{entry}")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "profile": "strong_GC__reachable_state_MSR",
        "input_artifacts": {
            MIXED_MANIFEST_PATH: _sha256(manifest_path),
            TANGENT_CERTIFICATE_PATH: _sha256(tangent_path),
        },
        "input_claim_boundary": {
            "mixed_manifest": (
                "Checked-in nonlinear source-native 262-scalar ansatz only; "
                "no Eq.(107)/(108)/(112), "
                "Q-only reconstruction, solver, Sage, Groebner, or chart proof."
            ),
            "tangent_certificate": (
                "Used solely as a list of 131 claimed independent rows; "
                "every listed row and its QQ "
                "coefficients are recomputed from the nonlinear manifest before a fresh SymPy rank."
            ),
        },
        "specialization": {
            "assignment": "x_[e]=0 for all 131 ON quotient orbits",
            "pure_lower_form": "A_e=[[p_e,0],[y_[e],1]]",
            "checks": specialization,
        },
        "selected_row_crosscheck": {
            "selected_row_count": len(selected_rows),
            "selected_row_kind_counts": certificate["selected_row_kind_counts"],
            "all_131_labels_and_QQ_coefficients_match_nonlinear_specialization": True,
            "matched_labels_sha256": hashlib.sha256(
                _canonical_json(matched_labels).encode("utf-8")
            ).hexdigest(),
            "selected_rows_sha256_from_tangent_certificate": certificate["selected_rows_sha256"],
            "independent_rank_backend": (
                "sympy.SparseMatrix.rank over exact QQ; "
                "no tangent implementation/rank function imported"
            ),
            "matrix_shape": [131, 131],
            "sympy_QQ_rank": rank,
        },
        "deduction": {
            "pure_lower_solution_set_within_mixed_ansatz": "y=0 only",
            "reason": (
                "The 131 selected equations are exact homogeneous linear equations in y after x=0, "
                "and their independently recomputed QQ coefficient matrix has rank 131."
            ),
            "nonsingularity_at_forced_solution": (
                "det(A_e)=p_e, and the mixed manifest certifies all 165 diagonal-base determinants "
                "are nonzero."
            ),
            "Q_commutativity": (
                "At y=0 and x=0 every Q_i is diagonal; all six manifest commutators vanish at that "
                "forced point."
            ),
            "N_nonzero": (
                "The p1 reachable-MSR operator residual retains constant (2,2)=1, so D_p1 is "
                "nonzero; this is a strong-MSR escape point, not an imposed reachable-MSR relation."
            ),
        },
        "open_boundary": [
            "mixed solutions with x!=0 and y!=0 in the 262-scalar ansatz",
            "nonlinear components disconnected from the pure-lower/upper loci",
            "the full source-native 955 system outside the mixed ansatz",
            "a global commutativity theorem or a noncommutative witness for the full 955 profile",
        ],
        "solver_runs": 0,
        "sage_runs": 0,
        "witness_certified": False,
        "commutativity_proved_for_full_profile": False,
        "passed": True,
        "verdict": VERDICT,
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
    print(f"{result['verdict']} {result['semantic_digest_sha256']}")
