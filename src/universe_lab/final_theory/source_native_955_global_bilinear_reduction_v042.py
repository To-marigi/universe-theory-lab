"""Exact global bilinear reduction of the v0.4.2 955 mixed system.

The gauge-torus grading certificate shows that every residual entry ``(i,j)`` of
the mixed ansatz ``A_e=[[p_e,x_[e]],[y_[e],1]]`` is homogeneous of grade
``j-i`` for ``deg_x - deg_y``.  Measuring the finer bidegree of the frozen mixed
manifest sharpens that into a much stronger structural fact about the CPOBC
block alone:

* every CPOBC upper-right entry carries only bidegree ``(1,0)`` monomials, so it
  is an exactly linear form in ``x`` with constant rational coefficients and no
  ``y`` dependence at all;
* every CPOBC lower-left entry carries only bidegree ``(0,1)`` monomials, so it
  is exactly linear in ``y`` and independent of ``x``;
* every CPOBC diagonal entry carries only bidegree ``(1,1)`` monomials, so the
  diagonal block is exactly bilinear.

This is a global identity on the whole mixed ansatz, not a linearisation at a
base point.  Both constant coefficient matrices have exact rank 108 on 131
columns, so the CPOBC block alone forces ``x`` into a 23-dimensional kernel
``K_x`` and ``y`` into a 23-dimensional kernel ``K_y``, globally and without any
localisation, patch decomposition or solver.  The 262-parameter mixed system
therefore reduces exactly to 46 parameters, and to 45 modulo the gauge torus.

The module emits the two primitive integral kernel bases, the substitution
self-check that all 1,566 CPOBC off-diagonal entries vanish identically, and the
fully recompiled 46-variable system with its exact census.  It runs no Groebner,
saturation, finite-field or numerical computation and decides nothing about the
955 profile.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from fractions import Fraction
from math import gcd
from pathlib import Path
from typing import Any

MIXED_MANIFEST_PATH = "results/v0.4.2_955_mixed_source_native_manifest.json"
TANGENT_SCOUT_PATH = "results/v0.4.2_955_mixed_xy_tangent_scout.json"
SYMMETRY_PATH = "results/v0.4.2_955_symmetry_orbit_reduction.json"
RESULT_PATH = "results/v0.4.2_955_global_bilinear_reduction.json"

SCHEMA = "final-theory-v042-955-global-bilinear-reduction-v1"
VERDICT = "V042_955_GLOBAL_BILINEAR_REDUCTION_262_TO_46_CERTIFIED_NONTERMINAL"

PROFILE_BLOCKS = ("CPOBC", "strong_GC", "reachable_MSR_vector")
MATRIX_ENTRIES = ("00", "01", "10", "11")

type Monomial = tuple[str, ...]
type Polynomial = dict[Monomial, Fraction]


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


def _bidegree(monomial: Iterable[dict[str, Any]]) -> tuple[int, int]:
    x_degree = y_degree = 0
    for factor in monomial:
        exponent = int(factor["exponent"])
        variable = str(factor["variable"])
        if variable.startswith("x:"):
            x_degree += exponent
        elif variable.startswith("y:"):
            y_degree += exponent
        else:
            raise AssertionError(f"the mixed manifest carries an ungraded variable: {variable}")
    return x_degree, y_degree


# ---------------------------------------------------------------------------
# Exact rational elimination
# ---------------------------------------------------------------------------


def _reduced_row_echelon(
    rows: Iterable[dict[int, Fraction]],
) -> dict[int, dict[int, Fraction]]:
    basis: dict[int, dict[int, Fraction]] = {}
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
        reduced = basis[pivot]
        for other in sorted(basis):
            if other <= pivot:
                continue
            scale = reduced.get(other)
            if not scale:
                continue
            for column, value in basis[other].items():
                updated = reduced.get(column, Fraction(0)) - scale * value
                if updated:
                    reduced[column] = updated
                else:
                    reduced.pop(column, None)
    return basis


def _primitive(vector: Sequence[Fraction]) -> list[int]:
    denominator = 1
    for value in vector:
        denominator = denominator * value.denominator // gcd(denominator, value.denominator)
    scaled = [int(value * denominator) for value in vector]
    divisor = 0
    for value in scaled:
        divisor = gcd(divisor, abs(value))
    if divisor == 0:
        raise AssertionError("a kernel basis vector is zero")
    scaled = [value // divisor for value in scaled]
    for value in scaled:
        if value:
            if value < 0:
                scaled = [-entry for entry in scaled]
            break
    return scaled


def _kernel(rows: Iterable[dict[int, Fraction]], columns: int) -> dict[str, Any]:
    basis = _reduced_row_echelon(rows)
    pivots = sorted(basis)
    free = [column for column in range(columns) if column not in basis]
    vectors: list[list[int]] = []
    for column in free:
        vector = [Fraction(0)] * columns
        vector[column] = Fraction(1)
        for pivot in pivots:
            vector[pivot] = -basis[pivot].get(column, Fraction(0))
        vectors.append(_primitive(vector))
    return {
        "rank": len(pivots),
        "nullity": len(free),
        "free_columns": free,
        "basis": vectors,
    }


# ---------------------------------------------------------------------------
# Sparse polynomial substitution
# ---------------------------------------------------------------------------


def _multiply(left: Polynomial, right: Polynomial) -> Polynomial:
    product: Polynomial = {}
    for left_monomial, left_coefficient in left.items():
        for right_monomial, right_coefficient in right.items():
            monomial = tuple(sorted(left_monomial + right_monomial))
            value = product.get(monomial, Fraction(0)) + left_coefficient * right_coefficient
            if value:
                product[monomial] = value
            else:
                product.pop(monomial, None)
    return product


def _substitute(
    polynomial: Iterable[dict[str, Any]], substitution: dict[str, Polynomial]
) -> Polynomial:
    result: Polynomial = {}
    for term in polynomial:
        accumulator: Polynomial = {(): Fraction(str(term["coefficient"]))}
        for factor in term["monomial"]:
            base = substitution[str(factor["variable"])]
            for _ in range(int(factor["exponent"])):
                accumulator = _multiply(accumulator, base)
                if not accumulator:
                    break
            if not accumulator:
                break
        for monomial, coefficient in accumulator.items():
            value = result.get(monomial, Fraction(0)) + coefficient
            if value:
                result[monomial] = value
            else:
                result.pop(monomial, None)
    return result


def _emit(polynomial: Polynomial) -> list[dict[str, Any]]:
    emitted = []
    for monomial in sorted(polynomial, key=lambda item: (len(item), item)):
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


def compile_global_bilinear_reduction_v042(root: Path) -> dict[str, Any]:
    """Compile the exact global reduction of the 955 mixed system to 46 parameters."""

    paths = {
        MIXED_MANIFEST_PATH: root / MIXED_MANIFEST_PATH,
        TANGENT_SCOUT_PATH: root / TANGENT_SCOUT_PATH,
        SYMMETRY_PATH: root / SYMMETRY_PATH,
    }
    manifest = _load(paths[MIXED_MANIFEST_PATH])
    tangent = _load(paths[TANGENT_SCOUT_PATH])
    symmetry = _load(paths[SYMMETRY_PATH])
    for name, artifact in (
        (MIXED_MANIFEST_PATH, manifest),
        (TANGENT_SCOUT_PATH, tangent),
        (SYMMETRY_PATH, symmetry),
    ):
        if artifact.get("semantic_digest_sha256") != _semantic_digest(artifact):
            raise AssertionError(f"{name} is not at its frozen semantic digest")
    if symmetry["gauge_torus"]["violations"] != 0:
        raise AssertionError("the gauge-torus grading certificate this gate builds on has changed")

    blocks = manifest["residual_blocks"]
    names = manifest["variables"]["names"]
    orbits = sorted(name[2:] for name in names if name.startswith("x:"))
    if len(orbits) != 131:
        raise AssertionError("expected 131 x coordinates")
    if orbits != sorted(name[2:] for name in names if name.startswith("y:")):
        raise AssertionError("the x and y coordinates index different orbit sets")
    position = {orbit: index for index, orbit in enumerate(orbits)}

    # --- the global exact-linearity certificate -----------------------------
    census: dict[str, dict[str, dict[str, int]]] = {}
    for entry in MATRIX_ENTRIES:
        counter: Counter[tuple[int, int]] = Counter()
        for record in blocks["CPOBC"]["records"]:
            for term in record["entries"].get(entry, []):
                counter[_bidegree(term["monomial"])] += 1
        census[entry] = {
            "bidegrees": {f"{x},{y}": count for (x, y), count in sorted(counter.items())}
        }
    expected = {"01": (1, 0), "10": (0, 1), "00": (1, 1), "11": (1, 1)}
    for entry, bidegree in expected.items():
        observed = list(census[entry]["bidegrees"])
        if observed != [f"{bidegree[0]},{bidegree[1]}"]:
            raise AssertionError(f"CPOBC entry {entry} is not purely of bidegree {bidegree}")

    def constant_rows(entry: str, prefix: str) -> list[dict[int, Fraction]]:
        rows = []
        for record in blocks["CPOBC"]["records"]:
            row: dict[int, Fraction] = defaultdict(Fraction)
            for term in record["entries"].get(entry, []):
                monomial = term["monomial"]
                if len(monomial) != 1 or int(monomial[0]["exponent"]) != 1:
                    raise AssertionError(f"CPOBC entry {entry} is not exactly linear")
                variable = str(monomial[0]["variable"])
                if not variable.startswith(prefix):
                    raise AssertionError(f"CPOBC entry {entry} depends on {variable}")
                row[position[variable[2:]]] += Fraction(str(term["coefficient"]))
            rows.append({column: value for column, value in row.items() if value})
        return rows

    x_kernel = _kernel(constant_rows("01", "x:"), 131)
    y_kernel = _kernel(constant_rows("10", "y:"), 131)
    for label, kernel in (("x", x_kernel), ("y", y_kernel)):
        if kernel["rank"] != 108 or kernel["nullity"] != 23:
            raise AssertionError(f"the CPOBC {label} block changed rank or nullity")

    # --- the reduced 46-parameter substitution ------------------------------
    substitution: dict[str, Polynomial] = {}
    for index, orbit in enumerate(orbits):
        substitution[f"x:{orbit}"] = {
            (f"s{axis}",): Fraction(vector[index])
            for axis, vector in enumerate(x_kernel["basis"])
            if vector[index]
        }
        substitution[f"y:{orbit}"] = {
            (f"t{axis}",): Fraction(vector[index])
            for axis, vector in enumerate(y_kernel["basis"])
            if vector[index]
        }

    reduced: dict[str, Any] = {}
    off_diagonal_checked = 0
    for block in PROFILE_BLOCKS:
        entries = ("0", "1") if block == "reachable_MSR_vector" else MATRIX_ENTRIES
        records: list[dict[str, Any]] = []
        identically_zero = 0
        total_entries = 0
        total_terms = 0
        largest = 0
        degrees: Counter[int] = Counter()
        for record in blocks[block]["records"]:
            emitted: dict[str, list[dict[str, Any]]] = {}
            for entry in entries:
                polynomial = record["entries"].get(entry)
                if polynomial is None:
                    continue
                total_entries += 1
                substituted = _substitute(polynomial, substitution)
                if block == "CPOBC" and entry in ("01", "10"):
                    off_diagonal_checked += 1
                    if substituted:
                        raise AssertionError(
                            f"CPOBC entry {entry} did not vanish on the certified kernel"
                        )
                if not substituted:
                    identically_zero += 1
                    continue
                total_terms += len(substituted)
                largest = max(largest, len(substituted))
                degrees[max(len(monomial) for monomial in substituted)] += 1
                emitted[entry] = _emit(substituted)
            if emitted:
                identifier = {
                    key: record[key]
                    for key in ("relation_id", "equation_id", "constraint_id", "source_id")
                    if key in record
                }
                records.append({**identifier, "entries": emitted})
        reduced[block] = {
            "entries_total": total_entries,
            "identically_zero_after_reduction": identically_zero,
            "surviving_entries": total_entries - identically_zero,
            "total_terms": total_terms,
            "largest_entry_term_count": largest,
            "degree_histogram": {str(key): value for key, value in sorted(degrees.items())},
            "records": records,
        }
    if off_diagonal_checked != 1566:
        raise AssertionError("the CPOBC off-diagonal vanishing self-check lost coverage")

    commutator_records = []
    commutator_terms = 0
    commutator_entries = 0
    for record in manifest["Q_commutator_polynomials"]["records"]:
        emitted = {}
        for entry, polynomial in sorted(record["entries"].items()):
            substituted = _substitute(polynomial, substitution)
            if substituted:
                commutator_entries += 1
                commutator_terms += len(substituted)
                emitted[entry] = _emit(substituted)
        if emitted:
            identifier = {key: value for key, value in record.items() if key != "entries"}
            commutator_records.append({**identifier, "entries": emitted})

    graded_violations = 0
    for block in PROFILE_BLOCKS:
        for record in reduced[block]["records"]:
            for entry, polynomial in record["entries"].items():
                if block == "reachable_MSR_vector":
                    expected_grade = -int(entry)
                else:
                    expected_grade = int(entry[1]) - int(entry[0])
                for term in polynomial:
                    grade = sum(
                        factor["exponent"] * (1 if factor["variable"].startswith("s") else -1)
                        for factor in term["monomial"]
                    )
                    if grade != expected_grade:
                        graded_violations += 1
    if graded_violations:
        raise AssertionError("the reduced system lost the gauge-torus grading")

    surviving_terms = sum(reduced[block]["total_terms"] for block in PROFILE_BLOCKS)
    surviving_entries = sum(reduced[block]["surviving_entries"] for block in PROFILE_BLOCKS)

    reduced_variables = [f"s{axis}" for axis in range(23)] + [f"t{axis}" for axis in range(23)]
    variable_index = {name: index for index, name in enumerate(reduced_variables)}
    linear_rows: list[dict[int, Fraction]] = []
    linear_labels: list[dict[str, Any]] = []
    for block in PROFILE_BLOCKS:
        for record in reduced[block]["records"]:
            for entry, polynomial in sorted(record["entries"].items()):
                if any(len(term["monomial"]) != 1 for term in polynomial):
                    continue
                if any(term["monomial"][0]["exponent"] != 1 for term in polynomial):
                    continue
                row = {
                    variable_index[term["monomial"][0]["variable"]]: Fraction(
                        str(term["coefficient"])
                    )
                    for term in polynomial
                }
                linear_rows.append(row)
                linear_labels.append(
                    {
                        "block": block,
                        "entry": entry,
                        "identifier": {
                            key: value for key, value in record.items() if key != "entries"
                        },
                        "coefficients": [
                            [reduced_variables[column], str(value)]
                            for column, value in sorted(row.items())
                        ],
                    }
                )
    linear_basis = _reduced_row_echelon(linear_rows)
    linear_part = {
        "role": (
            "Entries of the reduced system that are already homogeneous linear forms in the 46 "
            "coordinates.  Their exact rank is reported as a measurement; no elimination is "
            "carried out and no further reduced system is emitted."
        ),
        "row_count": len(linear_rows),
        "rank": len(linear_basis),
        "implied_upper_bound_on_remaining_parameters": 46 - len(linear_basis),
        "rows": linear_labels,
        "eliminated_here": False,
    }

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
            MIXED_MANIFEST_PATH: manifest["semantic_digest_sha256"],
            TANGENT_SCOUT_PATH: tangent["semantic_digest_sha256"],
            SYMMETRY_PATH: symmetry["semantic_digest_sha256"],
        },
        "global_exact_linearity": {
            "statement": (
                "On the whole mixed ansatz the CPOBC upper-right block is exactly linear in x "
                "with no y dependence, the lower-left block is exactly linear in y with no x "
                "dependence, and the diagonal block is exactly bilinear.  This is a global "
                "identity, not a linearisation at a base point."
            ),
            "cpobc_bidegree_census": census,
            "records": len(blocks["CPOBC"]["records"]),
        },
        "cpobc_kernels": {
            "x": {
                "matrix_shape": [len(blocks["CPOBC"]["records"]), 131],
                "rank": x_kernel["rank"],
                "nullity": x_kernel["nullity"],
                "free_columns": x_kernel["free_columns"],
                "primitive_integral_basis": x_kernel["basis"],
                "basis_sha256": _digest(x_kernel["basis"]),
            },
            "y": {
                "matrix_shape": [len(blocks["CPOBC"]["records"]), 131],
                "rank": y_kernel["rank"],
                "nullity": y_kernel["nullity"],
                "free_columns": y_kernel["free_columns"],
                "primitive_integral_basis": y_kernel["basis"],
                "basis_sha256": _digest(y_kernel["basis"]),
            },
            "agreement_with_frozen_tangent_ranks": {
                "upper_CPOBC_rank": tangent["exact_linear_blocks"]["upper"]["ranks"]["CPOBC"],
                "lower_CPOBC_rank": tangent["exact_linear_blocks"]["lower"]["ranks"]["CPOBC"],
                "matches": (
                    tangent["exact_linear_blocks"]["upper"]["ranks"]["CPOBC"] == x_kernel["rank"]
                    and tangent["exact_linear_blocks"]["lower"]["ranks"]["CPOBC"]
                    == y_kernel["rank"]
                ),
            },
        },
        "off_diagonal_vanishing_self_check": {
            "cpobc_off_diagonal_entries": off_diagonal_checked,
            "identically_zero_after_substitution": off_diagonal_checked,
            "failures": 0,
        },
        "reduction": {
            "parameters_before": 262,
            "parameters_after": 46,
            "coordinates": {"s": 23, "t": 23},
            "gauge_torus_weights": {"s": 1, "t": -1},
            "effective_parameters_modulo_gauge": 45,
            "localisation_used": False,
            "patch_decomposition_used": False,
            "solver_used": False,
            "is_a_global_identity": True,
        },
        "reduced_system": {
            "variables": reduced_variables,
            "surviving_entries": surviving_entries,
            "total_terms": surviving_terms,
            "maximum_total_degree": max(
                int(degree)
                for block in PROFILE_BLOCKS
                for degree in reduced[block]["degree_histogram"]
            ),
            "gauge_grading_preserved": True,
            "gauge_grading_violations": graded_violations,
            "linear_part": linear_part,
            "blocks": reduced,
        },
        "reduced_Q_commutator": {
            "surviving_entries": commutator_entries,
            "total_terms": commutator_terms,
            "identically_zero": commutator_entries == 0,
            "records": commutator_records,
        },
        "solver_status": {
            "Groebner_or_saturation_runs": 0,
            "finite_field_runs": 0,
            "numerical_runs": 0,
            "Sage_runs": 0,
            "solver_run": False,
        },
        "claim_boundary": [
            "This is a change of coordinates plus an exactly certified linear elimination.",
            "It proves nothing about the 955 profile and certifies no witness or obstruction.",
            "The reduced Q commutator is not identically zero, so commutativity does not follow.",
            "The mixed x/y ansatz is a declared family, not general GL_2.",
            "The unrestricted source-native slack system is outside this reduction.",
            "Nonsingularity det(A_e)=p_e-x_[e]*y_[e]!=0 is not imposed in the reduced system.",
        ],
        "commutativity_proved_for_full_profile": False,
        "witness_certified": False,
        "search_terminal": False,
        "passed": True,
        "verdict": VERDICT,
    }
    payload["semantic_digest_sha256"] = _semantic_digest(payload)
    return payload


def write_global_bilinear_reduction_v042(root: Path) -> Path:
    payload = compile_global_bilinear_reduction_v042(root)
    destination = root / RESULT_PATH
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[3]
    print(write_global_bilinear_reduction_v042(repository_root))
