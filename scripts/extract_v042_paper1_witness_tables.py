"""Extract the compact Paper I witness tables from frozen v0.4 authorities.

The default ``--check`` mode is read-only.  It authenticates all three input
authorities before parsing the ledgers, regenerates the complete compact
payload in memory, and compares both its canonical semantics and exact bytes
with the tracked result.  Only an explicit ``--write`` performs an atomic
replacement of the tracked result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from fractions import Fraction
from pathlib import Path
from typing import Any

WEAK_PATH = "results/v0.4_weak_d2_classification.json"
OBSERVABILITY_PATH = "results/v0.4.2_sr2v_baseline_observability.json"
ORACLE_PATH = "tests/final_theory/test_weak_d2_v04_oracle.py"
OUTPUT_PATH = "results/v0.4.2_paper1_witness_tables.json"

SOURCE_SPECS: dict[str, dict[str, str]] = {
    WEAK_PATH: {
        "raw_sha256": "18e71f439913896fb370944c6479fc358d4d6d0d127162809ba46822ccd2fe65",
        "role": (
            "complete electronic-ledger authority for the rational witness, transition "
            "assignment, and all finite substitution families"
        ),
    },
    OBSERVABILITY_PATH: {
        "raw_sha256": "4f57805e871c0589560669c5aa65181c29ca41cdf722420729279945770710de",
        "semantic_sha256": ("73508f8ad94d97a3147cbd913d687f0b779c740b80a84a4836854053f6f01c62"),
        "role": (
            "independent exact-rational reconstruction of paths, reachable rank, residual "
            "visibility, and commutator action"
        ),
    },
    ORACLE_PATH: {
        "raw_sha256": "54c5ec91fd3af0c824b153e451caa4695036e39d3915e68e76618ee2f455b324",
        "role": (
            "independent SymPy exact-arithmetic oracle; bound as code and not assigned an "
            "invented semantic digest"
        ),
    },
}

WEAK_SCHEMA = "final-theory-weak-d2-v0.4"
WEAK_VERDICT = "WEAK_D2_NONCOMMUTATIVE_WITNESS_CERTIFIED"
OBSERVABILITY_SCHEMA = "final-theory-v042-sr2v-baseline-observability-v1"
OBSERVABILITY_VERDICT = "SR2V_BASELINE_OBSERVABILITY_AUDIT_CERTIFIED"
OUTPUT_SCHEMA = "final-theory-v042-paper1-witness-tables-v1"
OUTPUT_VERDICT = "PAPER1_WITNESS_TABLES_EXTRACTED_FROM_BOUND_AUTHORITIES"

EXPECTED_WEAK_GATES = {
    "all_783_CPOBC_word_equations": True,
    "all_712_CPOBC_inverse_containing_rewrites": True,
    "all_1529_fixed_vector_GC_path_pairs": True,
    "all_24_reachable_state_MSR_constraints": True,
    "Eq113_derived_branch_operator_equalities": True,
    "Eq113_literal_branch_operator_equalities": True,
    "Eq139_printed_strict_operator_equalities": True,
    "Eq139_eq145_completed_operator_equalities": True,
    "all_165_transition_determinants_nonzero": True,
    "all_330_two_sided_transition_inverse_equations": True,
    "Q1_through_Q5_determinants_nonzero": True,
    "all_six_Q1_through_Q4_commutators_nonzero": True,
    "strong_GC_is_not_accidentally_satisfied": True,
    "strong_MSR_is_not_accidentally_satisfied": True,
}
EXPECTED_OBSERVABILITY_GATES = {
    "frozen_weak_witness_valid": True,
    "independent_Q_formula_matches_frozen_inventory": True,
    "all_407_paths_reconstructed": True,
    "all_87_endpoint_states_reconstructed": True,
    "fixed_vector_GC_holds_on_all_1529_pairs": True,
    "reachable_state_MSR_holds_at_all_24_sources": True,
    "reachable_span_rank_is_exactly_one": True,
    "all_six_Q_commutators_are_operator_nonzero": True,
    "no_Q_commutator_is_detected_on_any_compiled_cylinder_state": True,
}
EXPECTED_WITNESS_DEFINITION = {
    "initial_vector": ["1", "0"],
    "transition_formula": ("A_e=[[2^(w_e-m_e)/2^n, (4/2^n if precursor is empty else 0)],[0,1]]"),
    "w_e": "precursor cardinality",
    "m_e": "number of maximal precursor elements",
    "Q_n_formula": "[[2^-n,4*2^-n],[0,1]]",
    "reachable_states": "nonzero rational multiples of omega=(1,0)^T",
    "exactness": "all calculations use fractions.Fraction; no floating point",
}
EXPECTED_FAMILY_COUNTS = {
    "transition_occurrences": 165,
    "CPOBC": 783,
    "CPOBC_inverse_rewrites": 712,
    "GC": 1529,
    "MSR": 24,
    "Eq113_QN": 25,
    "Eq113_QN_PLUS_1": 25,
    "Eq139_PRINTED_STRICT": 4,
    "Eq139_EQ145_COMPLETED": 10,
    "Q_commutators": 6,
}
EXPECTED_TOTAL_RECORDS = 3283
ZERO_MATRIX = [["0", "0"], ["0", "0"]]
ZERO_VECTOR = ["0", "0"]


class ExtractionError(RuntimeError):
    """A fail-closed witness-table extraction error."""


def canonical_json_bytes(value: object) -> bytes:
    """Return the repository's canonical JSON encoding without a trailing LF."""

    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def semantic_digest(payload: dict[str, Any]) -> str:
    """Hash canonical JSON after excluding the top-level self-digest field."""

    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return _sha256_bytes(canonical_json_bytes(semantic))


def output_bytes(payload: dict[str, Any]) -> bytes:
    return canonical_json_bytes(payload) + b"\n"


def _mapping(value: object, context: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ExtractionError(f"{context} must be a string-keyed object")
    return value


def _sequence(value: object, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise ExtractionError(f"{context} must be an array")
    return value


def _string(value: object, context: str) -> str:
    if not isinstance(value, str):
        raise ExtractionError(f"{context} must be a string")
    return value


def _integer(value: object, context: str) -> int:
    if type(value) is not int:
        raise ExtractionError(f"{context} must be an integer")
    return value


def _fraction(value: object, context: str) -> Fraction:
    text = _string(value, context)
    try:
        return Fraction(text)
    except (ValueError, ZeroDivisionError) as error:
        raise ExtractionError(f"{context} is not an exact rational") from error


def _fraction_text(value: Fraction) -> str:
    return str(value)


def _require_equal(actual: object, expected: object, context: str) -> None:
    if actual != expected:
        raise ExtractionError(f"{context} mismatch")


def _read_authenticated_inputs(repository_root: Path) -> dict[str, bytes]:
    """Authenticate every input byte stream before any JSON is parsed."""

    raw_inputs: dict[str, bytes] = {}
    for relative_path, specification in SOURCE_SPECS.items():
        path = repository_root / relative_path
        if not path.is_file():
            raise ExtractionError(f"missing bound input: {relative_path}")
        raw = path.read_bytes()
        digest = _sha256_bytes(raw)
        if digest != specification["raw_sha256"]:
            raise ExtractionError(f"raw SHA-256 drift for {relative_path}: {digest}")
        raw_inputs[relative_path] = raw
    return raw_inputs


def _parse_json(raw: bytes, relative_path: str) -> dict[str, Any]:
    try:
        decoded = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ExtractionError(f"invalid UTF-8 JSON in {relative_path}") from error
    return _mapping(decoded, relative_path)


def _validate_authority_headers(weak: dict[str, Any], observability: dict[str, Any]) -> None:
    _require_equal(weak.get("schema_version"), WEAK_SCHEMA, "weak schema_version")
    _require_equal(weak.get("field"), "Q", "weak field")
    _require_equal(weak.get("dimension"), 2, "weak dimension")
    _require_equal(weak.get("passed"), True, "weak passed")
    _require_equal(weak.get("verdict"), WEAK_VERDICT, "weak verdict")
    _require_equal(weak.get("gates"), EXPECTED_WEAK_GATES, "weak gates")

    _require_equal(
        observability.get("schema_version"),
        OBSERVABILITY_SCHEMA,
        "observability schema_version",
    )
    _require_equal(observability.get("field"), "Q", "observability field")
    _require_equal(observability.get("dimension"), 2, "observability dimension")
    _require_equal(observability.get("passed"), True, "observability passed")
    _require_equal(observability.get("verdict"), OBSERVABILITY_VERDICT, "observability verdict")
    _require_equal(
        observability.get("gates"),
        EXPECTED_OBSERVABILITY_GATES,
        "observability gates",
    )

    expected_semantic = SOURCE_SPECS[OBSERVABILITY_PATH]["semantic_sha256"]
    _require_equal(
        observability.get("semantic_digest_sha256"),
        expected_semantic,
        "observability recorded semantic digest",
    )
    _require_equal(
        semantic_digest(observability),
        expected_semantic,
        "observability recomputed semantic digest",
    )
    input_artifacts = _mapping(
        observability.get("input_artifacts"), "observability input_artifacts"
    )
    _require_equal(
        input_artifacts.get(WEAK_PATH),
        SOURCE_SPECS[WEAK_PATH]["raw_sha256"],
        "observability binding to weak witness",
    )
    independence = _mapping(observability.get("independence"), "observability independence")
    _require_equal(independence.get("imports_weak_d2_v04"), False, "independent module import")
    _require_equal(
        independence.get("arithmetic"),
        "fractions.Fraction only; no float or finite field",
        "independent arithmetic",
    )
    _require_equal(
        independence.get("transition_formula_reconstructed_from_source_metadata"),
        True,
        "independent transition reconstruction",
    )
    _require_equal(
        independence.get("path_products_reconstructed_from_all_407_path_records"),
        True,
        "independent path reconstruction",
    )


def _expected_q(stage: int) -> dict[str, Any]:
    diagonal = Fraction(1, 2**stage)
    return {
        "stage": stage,
        "matrix": [
            [_fraction_text(diagonal), _fraction_text(4 * diagonal)],
            ["0", "1"],
        ],
        "determinant": _fraction_text(diagonal),
        "nonsingular": True,
    }


def _extract_formulas_and_q(weak: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    witness_definition = _mapping(weak.get("witness_definition"), "witness_definition")
    _require_equal(
        witness_definition,
        EXPECTED_WITNESS_DEFINITION,
        "witness_definition",
    )
    q_inventory = _sequence(weak.get("Q_inventory"), "Q_inventory")
    expected_q = [_expected_q(stage) for stage in range(1, 6)]
    _require_equal(q_inventory, expected_q, "Q1..Q5 inventory")
    formulas = {
        "transition_matrix": "A_e=[[2^(w_e-m_e)/2^n,b_e],[0,1]]",
        "diagonal_entry": "2^(w_e-m_e)/2^n",
        "b_e": "4/2^n if the precursor is empty; 0 otherwise",
        "gregarious_transition_definition": "precursor_code=0",
        "w_e": witness_definition["w_e"],
        "m_e": witness_definition["m_e"],
        "Q_n": witness_definition["Q_n_formula"],
        "source_transition_formula": witness_definition["transition_formula"],
    }
    return formulas, expected_q


def _transition_invariant(record: dict[str, Any], index: int) -> dict[str, Any]:
    context = f"transition_assignment.records[{index}]"
    expected_keys = {
        "occurrence_id",
        "orbit_id",
        "stage",
        "source_id",
        "source_relation_rows",
        "precursor_code",
        "matrix",
        "determinant",
        "nonsingular",
    }
    _require_equal(set(record), expected_keys, f"{context} keys")
    stage = _integer(record["stage"], f"{context}.stage")
    if stage < 1 or stage > 4:
        raise ExtractionError(f"{context}.stage is outside 1..4")
    rows_raw = _sequence(record["source_relation_rows"], f"{context}.source_relation_rows")
    rows = [_integer(value, f"{context}.source_relation_rows") for value in rows_raw]
    if len(rows) != stage or any(value < 0 or value >= 2**stage for value in rows):
        raise ExtractionError(f"{context}.source_relation_rows is invalid")
    precursor = _integer(record["precursor_code"], f"{context}.precursor_code")
    if precursor < 0 or precursor >= 2**stage:
        raise ExtractionError(f"{context}.precursor_code is invalid")
    w_e = precursor.bit_count()
    m_e = sum(
        1
        for vertex, upper_vertices in enumerate(rows)
        if precursor & (1 << vertex) and not upper_vertices & precursor
    )
    diagonal = Fraction(2 ** (w_e - m_e), 2**stage)
    b_e = Fraction(4, 2**stage) if precursor == 0 else Fraction(0)
    matrix = [
        [_fraction_text(diagonal), _fraction_text(b_e)],
        ["0", "1"],
    ]
    determinant = _fraction_text(diagonal)
    _require_equal(record["matrix"], matrix, f"{context}.matrix formula")
    _require_equal(record["determinant"], determinant, f"{context}.determinant")
    _require_equal(record["nonsingular"], True, f"{context}.nonsingular")
    return {
        "stage": stage,
        "w_e": w_e,
        "m_e": m_e,
        "precursor_empty": precursor == 0,
        "matrix": matrix,
        "determinant": determinant,
        "nonsingular": True,
    }


def _extract_transition_tables(weak: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    assignment = _mapping(weak.get("transition_assignment"), "transition_assignment")
    _require_equal(assignment.get("occurrence_count"), 165, "transition occurrence_count")
    _require_equal(assignment.get("orbit_count"), 131, "transition orbit_count")
    _require_equal(
        assignment.get("occurrence_identification_ON"), True, "occurrence identification ON"
    )
    _require_equal(
        assignment.get("occurrence_identification_OFF"),
        "also certified because an ON assignment is a valid special case of OFF",
        "occurrence identification OFF",
    )
    _require_equal(
        assignment.get("all_occurrences_nonsingular"),
        True,
        "all occurrences nonsingular",
    )

    records_raw = _sequence(assignment.get("records"), "transition_assignment.records")
    if len(records_raw) != 165:
        raise ExtractionError("transition record count mismatch")
    occurrence_map: list[dict[str, Any]] = []
    occurrence_ids: list[str] = []
    orbit_invariants: dict[str, dict[str, Any]] = {}
    orbit_occurrence_counts: dict[str, int] = {}
    for index, raw_record in enumerate(records_raw):
        record = _mapping(raw_record, f"transition_assignment.records[{index}]")
        occurrence_id = _string(record.get("occurrence_id"), f"transition record {index} ID")
        orbit_id = _string(record.get("orbit_id"), f"transition record {index} orbit")
        source_id = _string(record.get("source_id"), f"transition record {index} source")
        invariant = _transition_invariant(record, index)
        prior = orbit_invariants.setdefault(orbit_id, invariant)
        if prior != invariant:
            raise ExtractionError(
                f"orbit invariant drift for {orbit_id}: stage/w_e/m_e/empty/matrix/determinant"
            )
        orbit_occurrence_counts[orbit_id] = orbit_occurrence_counts.get(orbit_id, 0) + 1
        occurrence_ids.append(occurrence_id)
        occurrence_map.append(
            {
                "occurrence_id": occurrence_id,
                "orbit_id": orbit_id,
                "source_id": source_id,
                "source_relation_rows": record["source_relation_rows"],
                "precursor_code": record["precursor_code"],
            }
        )
    if len(set(occurrence_ids)) != 165:
        raise ExtractionError("duplicate transition occurrence_id")
    if len(orbit_invariants) != 131:
        raise ExtractionError("transition orbit cardinality mismatch")

    inverse_checks = _mapping(
        assignment.get("two_sided_inverse_checks"), "transition two_sided_inverse_checks"
    )
    _require_equal(inverse_checks.get("site_count"), 165, "inverse site_count")
    _require_equal(inverse_checks.get("matrix_equation_count"), 330, "inverse equation count")
    inverse_records = _sequence(inverse_checks.get("records"), "inverse records")
    if len(inverse_records) != 165:
        raise ExtractionError("inverse record count mismatch")
    inverse_ids: list[str] = []
    for index, raw_record in enumerate(inverse_records):
        record = _mapping(raw_record, f"inverse records[{index}]")
        _require_equal(
            set(record),
            {"occurrence_id", "left_inverse_residual", "right_inverse_residual", "both_zero"},
            f"inverse records[{index}] keys",
        )
        inverse_ids.append(_string(record["occurrence_id"], "inverse occurrence_id"))
        _require_equal(record["left_inverse_residual"], ZERO_MATRIX, "left inverse residual")
        _require_equal(record["right_inverse_residual"], ZERO_MATRIX, "right inverse residual")
        _require_equal(record["both_zero"], True, "two-sided inverse status")
    _require_equal(sorted(inverse_ids), sorted(occurrence_ids), "inverse occurrence coverage")

    occurrence_map.sort(key=lambda record: record["occurrence_id"])
    orbit_table = [
        {
            "orbit_id": orbit_id,
            **orbit_invariants[orbit_id],
            "occurrence_count": orbit_occurrence_counts[orbit_id],
        }
        for orbit_id in sorted(orbit_invariants)
    ]
    orbit_ids = [record["orbit_id"] for record in orbit_table]
    return (
        {
            "occurrence_count": len(occurrence_map),
            "orbit_count": len(orbit_table),
            "occurrence_map": occurrence_map,
            "orbit_table": orbit_table,
            "orbit_ids_sha256": _sha256_bytes(canonical_json_bytes(orbit_ids)),
            "precursor_code_location": "occurrence_map only",
            "orbit_invariant_fields": [
                "stage",
                "w_e",
                "m_e",
                "precursor_empty",
                "matrix",
                "determinant",
                "nonsingular",
            ],
        },
        occurrence_ids,
    )


def _natural_id(family: str, *components: str | int) -> str:
    return f"{family}:{canonical_json_bytes(list(components)).decode('utf-8')}"


def _unique_ids(family: str, ids: list[str], expected_count: int) -> list[str]:
    if len(ids) != expected_count:
        raise ExtractionError(f"{family} record count mismatch")
    if len(set(ids)) != expected_count:
        raise ExtractionError(f"duplicate or colliding {family} natural ID")
    return sorted(ids)


def _zero_matrix_family_ids(
    records_raw: object,
    *,
    family: str,
    expected_count: int,
    id_fields: tuple[str, ...],
) -> list[str]:
    records = _sequence(records_raw, f"{family}.records")
    identifiers: list[str] = []
    expected_keys = {*id_fields, "operator_residual", "zero"}
    if family in {"CPOBC", "CPOBC_inverse_rewrites"}:
        expected_keys = {*id_fields, "residual", "zero"}
    for index, raw_record in enumerate(records):
        record = _mapping(raw_record, f"{family}.records[{index}]")
        _require_equal(set(record), expected_keys, f"{family}.records[{index}] keys")
        components = tuple(_string(record[field], f"{family}.{field}") for field in id_fields)
        residual_key = "residual" if "residual" in record else "operator_residual"
        _require_equal(record[residual_key], ZERO_MATRIX, f"{family} residual")
        _require_equal(record["zero"], True, f"{family} zero status")
        identifiers.append(_natural_id(family, *components))
    return _unique_ids(family, identifiers, expected_count)


def _extract_substitution_ids(
    weak: dict[str, Any],
) -> tuple[dict[str, list[str]], dict[str, Any], dict[str, Any]]:
    direct = _mapping(weak.get("direct_substitution"), "direct_substitution")
    _require_equal(
        set(direct),
        {"CPOBC", "CPOBC_inverse_forms", "GC", "MSR", "Eq113", "Eq139"},
        "direct_substitution families",
    )
    families: dict[str, list[str]] = {}

    cpobc = _mapping(direct["CPOBC"], "CPOBC")
    _require_equal(cpobc.get("checked_equations"), 783, "CPOBC checked count")
    _require_equal(cpobc.get("expected_equations"), 783, "CPOBC expected count")
    _require_equal(cpobc.get("all_zero"), True, "CPOBC all_zero")
    families["CPOBC"] = _zero_matrix_family_ids(
        cpobc.get("records"),
        family="CPOBC",
        expected_count=783,
        id_fields=("relation_id", "equation_id"),
    )

    inverse = _mapping(direct["CPOBC_inverse_forms"], "CPOBC_inverse_forms")
    _require_equal(
        inverse.get("checked_inverse_containing_equations"),
        712,
        "CPOBC inverse checked count",
    )
    _require_equal(inverse.get("all_zero"), True, "CPOBC inverse all_zero")
    families["CPOBC_inverse_rewrites"] = _zero_matrix_family_ids(
        inverse.get("records"),
        family="CPOBC_inverse_rewrites",
        expected_count=712,
        id_fields=("relation_id", "equation_id"),
    )

    gc = _mapping(direct["GC"], "GC")
    _require_equal(gc.get("checked_same_endpoint_path_pairs"), 1529, "GC checked count")
    _require_equal(gc.get("all_fixed_vector_equalities_hold"), True, "GC fixed-vector gate")
    _require_equal(gc.get("all_strong_operator_equalities_hold"), False, "GC strong gate")
    _require_equal(gc.get("strong_operator_failure_count"), 986, "GC strong failure count")
    gc_records = _sequence(gc.get("records"), "GC.records")
    gc_ids: list[str] = []
    gc_representative: dict[str, Any] | None = None
    for index, raw_record in enumerate(gc_records):
        record = _mapping(raw_record, f"GC.records[{index}]")
        _require_equal(
            set(record),
            {
                "endpoint_causet_id",
                "left_path_id",
                "right_path_id",
                "operator_residual",
                "fixed_vector_residual",
                "strong_operator_zero",
                "fixed_vector_zero",
            },
            f"GC.records[{index}] keys",
        )
        endpoint = _string(record["endpoint_causet_id"], "GC endpoint")
        left = _string(record["left_path_id"], "GC left path")
        right = _string(record["right_path_id"], "GC right path")
        _require_equal(record["fixed_vector_residual"], ZERO_VECTOR, "GC fixed residual")
        _require_equal(record["fixed_vector_zero"], True, "GC fixed-vector status")
        operator_zero = record["operator_residual"] == ZERO_MATRIX
        _require_equal(record["strong_operator_zero"], operator_zero, "GC operator status")
        gc_ids.append(_natural_id("GC", endpoint, left, right))
        if (
            endpoint == "p3-002"
            and left == "lgc-path-73192a6770fa82828f12"
            and right == "lgc-path-fc1eafd06aa0360d6535"
        ):
            if gc_representative is not None:
                raise ExtractionError("duplicate representative GC record")
            gc_representative = record
    families["GC"] = _unique_ids("GC", gc_ids, 1529)
    if gc_representative is None:
        raise ExtractionError("representative GC record is missing")

    msr = _mapping(direct["MSR"], "MSR")
    _require_equal(msr.get("checked_constraints"), 24, "MSR checked count")
    _require_equal(msr.get("all_reachable_state_equalities_hold"), True, "MSR state gate")
    _require_equal(msr.get("all_strong_operator_equalities_hold"), False, "MSR strong gate")
    _require_equal(msr.get("strong_operator_failure_count"), 24, "MSR strong failure count")
    msr_records = _sequence(msr.get("records"), "MSR.records")
    msr_ids: list[str] = []
    msr_representative: dict[str, Any] | None = None
    for index, raw_record in enumerate(msr_records):
        record = _mapping(raw_record, f"MSR.records[{index}]")
        _require_equal(
            set(record),
            {
                "constraint_id",
                "source_id",
                "operator_residual",
                "reachable_state_residual_on_omega_ray",
                "strong_operator_zero",
                "reachable_state_zero",
            },
            f"MSR.records[{index}] keys",
        )
        constraint = _string(record["constraint_id"], "MSR constraint")
        source = _string(record["source_id"], "MSR source")
        _require_equal(
            record["reachable_state_residual_on_omega_ray"], ZERO_VECTOR, "MSR state residual"
        )
        _require_equal(record["reachable_state_zero"], True, "MSR state status")
        _require_equal(record["strong_operator_zero"], False, "MSR operator status")
        msr_ids.append(_natural_id("MSR", constraint))
        if constraint == "msr:p1-0" and source == "p1-0":
            if msr_representative is not None:
                raise ExtractionError("duplicate representative MSR record")
            msr_representative = record
    families["MSR"] = _unique_ids("MSR", msr_ids, 24)
    if msr_representative is None:
        raise ExtractionError("representative MSR record is missing")

    eq113 = _mapping(direct["Eq113"], "Eq113")
    _require_equal(eq113.get("branches_kept_separate"), True, "Eq113 branch separation")
    _require_equal(
        eq113.get("both_branches_hold_as_operator_equalities"), True, "Eq113 branch gate"
    )
    eq113_branches = _mapping(eq113.get("branches"), "Eq113.branches")
    eq113_specs = (
        ("EQ113_QN_BRANCH", "Eq113_QN"),
        ("EQ113_QN_PLUS_1_BRANCH", "Eq113_QN_PLUS_1"),
    )
    _require_equal(set(eq113_branches), {item[0] for item in eq113_specs}, "Eq113 branches")
    for source_name, family_name in eq113_specs:
        branch = _mapping(eq113_branches[source_name], f"Eq113.{source_name}")
        _require_equal(branch.get("checked_relations"), 25, f"{source_name} checked count")
        _require_equal(branch.get("all_zero"), True, f"{source_name} all_zero")
        families[family_name] = _zero_matrix_family_ids(
            branch.get("records"),
            family=family_name,
            expected_count=25,
            id_fields=("causet_id", "alpha_path_id", "beta_path_id", "Q_token"),
        )

    eq139 = _mapping(direct["Eq139"], "Eq139")
    _require_equal(eq139.get("both_domains_hold_as_operator_equalities"), True, "Eq139 domain gate")
    _require_equal(
        eq139.get("source_discrepancy"),
        {
            "printed_text": "m,k<n",
            "immediate_specialisation_eq145": "n=2 with A_2^(1) and A_2^(2)",
            "resolution": "PRESERVE_TWO_DOMAINS_WITHOUT_MERGING",
        },
        "Eq139 source discrepancy boundary",
    )
    eq139_branches = _mapping(eq139.get("branches"), "Eq139.branches")
    eq139_specs = (
        (
            "EQ139_PRINTED_STRICT_M_K_LT_N",
            "Eq139_PRINTED_STRICT",
            4,
            {"2": 0, "3": 1, "4": 3},
        ),
        (
            "EQ139_EQ145_COMPLETED_M_K_LE_N",
            "Eq139_EQ145_COMPLETED",
            10,
            {"2": 1, "3": 3, "4": 6},
        ),
    )
    _require_equal(set(eq139_branches), {item[0] for item in eq139_specs}, "Eq139 branches")
    for source_name, family_name, count, stage_counts in eq139_specs:
        branch = _mapping(eq139_branches[source_name], f"Eq139.{source_name}")
        _require_equal(branch.get("instance_count"), count, f"{source_name} count")
        _require_equal(branch.get("counts_by_stage"), stage_counts, f"{source_name} stages")
        _require_equal(branch.get("all_zero"), True, f"{source_name} all_zero")
        records = _sequence(branch.get("records"), f"{source_name}.records")
        identifiers: list[str] = []
        for index, raw_record in enumerate(records):
            record = _mapping(raw_record, f"{source_name}.records[{index}]")
            _require_equal(
                set(record),
                {"stage_n", "m", "k", "operator_residual", "zero"},
                f"{source_name}.records[{index}] keys",
            )
            stage = _integer(record["stage_n"], f"{source_name}.stage_n")
            m_index = _integer(record["m"], f"{source_name}.m")
            k_index = _integer(record["k"], f"{source_name}.k")
            _require_equal(record["operator_residual"], ZERO_MATRIX, f"{source_name} residual")
            _require_equal(record["zero"], True, f"{source_name} zero status")
            if not (1 <= m_index < k_index <= stage):
                raise ExtractionError(f"{source_name} index domain drift")
            if source_name == "EQ139_PRINTED_STRICT_M_K_LT_N" and k_index >= stage:
                raise ExtractionError("printed-strict Eq139 domain drift")
            identifiers.append(_natural_id(family_name, stage, m_index, k_index))
        families[family_name] = _unique_ids(family_name, identifiers, count)

    return families, gc_representative, msr_representative


def _expected_commutator(left: int, right: int) -> list[list[str]]:
    value = 4 * (Fraction(1, 2**left) - Fraction(1, 2**right))
    return [["0", _fraction_text(value)], ["0", "0"]]


def _extract_commutators(
    weak: dict[str, Any], observability: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    noncommutativity = _mapping(weak.get("noncommutativity"), "noncommutativity")
    _require_equal(
        noncommutativity.get("closed_formula"),
        "[Q_i,Q_j]=[[0,4*(2^-i-2^-j)],[0,0]] for 1<=i<j<=4",
        "commutator formula",
    )
    records = _sequence(noncommutativity.get("records"), "noncommutativity.records")
    observability_commutators = _mapping(
        observability.get("commutator_visibility"), "commutator_visibility"
    )
    _require_equal(
        observability_commutators.get("all_six_operator_commutators_nonzero"),
        True,
        "observability commutator nonzero gate",
    )
    _require_equal(
        observability_commutators.get("reachable_visible_on_any_compiled_cylinder_state"),
        False,
        "observability reachable-visible boundary",
    )
    _require_equal(
        observability_commutators.get("all_six_annihilate_full_reachable_span"),
        True,
        "observability reachable-span annihilation gate",
    )
    observable_records = _sequence(
        observability_commutators.get("records"), "commutator_visibility.records"
    )
    if len(records) != 6 or len(observable_records) != 6:
        raise ExtractionError("commutator record count mismatch")
    output_records: list[dict[str, Any]] = []
    identifiers: list[str] = []
    for index, (raw_record, raw_observable) in enumerate(
        zip(records, observable_records, strict=True)
    ):
        record = _mapping(raw_record, f"commutator record {index}")
        observable = _mapping(raw_observable, f"observable commutator record {index}")
        pair = _sequence(record.get("pair"), f"commutator record {index}.pair")
        if len(pair) != 2:
            raise ExtractionError("commutator pair must have two stages")
        left = _integer(pair[0], "commutator left stage")
        right = _integer(pair[1], "commutator right stage")
        if not (1 <= left < right <= 4):
            raise ExtractionError("commutator pair domain drift")
        expected = _expected_commutator(left, right)
        _require_equal(record.get("commutator"), expected, "commutator matrix formula")
        _require_equal(record.get("nonzero"), True, "commutator nonzero status")
        _require_equal(observable.get("pair"), pair, "observable commutator pair")
        _require_equal(observable.get("commutator"), expected, "observable commutator matrix")
        _require_equal(observable.get("operator_nonzero"), True, "observable operator status")
        _require_equal(
            observable.get("annihilates_full_reachable_span"),
            True,
            "observable span action",
        )
        domains = _mapping(observable.get("domains"), "commutator domains")
        primary = _mapping(
            domains.get("ALL_COMPILED_CYLINDER_STATES_IN_COMMON_H"),
            "primary commutator domain",
        )
        _require_equal(primary.get("tested_endpoint_count"), 87, "commutator endpoint count")
        _require_equal(primary.get("nonzero_action_count"), 0, "commutator visible actions")
        _require_equal(primary.get("first_detecting_endpoint_id"), None, "detecting endpoint")
        output_records.append(
            {
                "pair": pair,
                "commutator": expected,
                "operator_nonzero": True,
                "annihilates_full_reachable_span": True,
            }
        )
        identifiers.append(_natural_id("Q_commutators", left, right))
    identifiers = _unique_ids("Q_commutators", identifiers, 6)
    output_records.sort(key=lambda record: tuple(record["pair"]))
    return (
        {
            "closed_formula": noncommutativity["closed_formula"],
            "records": output_records,
            "operator_nonzero_count": 6,
            "reachable_visible_count": 0,
        },
        identifiers,
    )


def _extract_rank_one_evidence(observability: dict[str, Any]) -> dict[str, Any]:
    inventory = _mapping(observability.get("reachable_inventory"), "reachable_inventory")
    summary = _mapping(inventory.get("summary"), "reachable_inventory.summary")
    endpoints = _sequence(inventory.get("endpoints"), "reachable_inventory.endpoints")
    if len(endpoints) != 87:
        raise ExtractionError("reachable endpoint count mismatch")
    endpoint_ids: list[str] = []
    stage_counts: dict[str, int] = {}
    path_count = 0
    vectors: list[tuple[Fraction, Fraction]] = []
    vector_texts: set[str] = set()
    basis_endpoint: dict[str, Any] | None = None
    for index, raw_endpoint in enumerate(endpoints):
        endpoint = _mapping(raw_endpoint, f"reachable endpoint {index}")
        endpoint_id = _string(endpoint.get("endpoint_causet_id"), "endpoint ID")
        stage = _integer(endpoint.get("endpoint_stage"), "endpoint stage")
        state_raw = _sequence(endpoint.get("state"), "endpoint state")
        if len(state_raw) != 2:
            raise ExtractionError("endpoint state must have dimension two")
        state = (
            _fraction(state_raw[0], "endpoint first coordinate"),
            _fraction(state_raw[1], "endpoint second coordinate"),
        )
        if state == (Fraction(0), Fraction(0)):
            raise ExtractionError("reachable endpoint state is zero")
        if state[1] != 0:
            raise ExtractionError("reachable endpoint left the Omega ray")
        _require_equal(endpoint.get("all_paths_equal"), True, "same-endpoint path equality")
        endpoint_path_count = _integer(endpoint.get("path_count"), "endpoint path_count")
        if endpoint_path_count < 1:
            raise ExtractionError("endpoint path_count must be positive")
        endpoint_ids.append(endpoint_id)
        stage_counts[str(stage)] = stage_counts.get(str(stage), 0) + 1
        path_count += endpoint_path_count
        vectors.append(state)
        vector_texts.add(f"{_fraction_text(state[0])},{_fraction_text(state[1])}")
        if endpoint_id == "p1-0":
            if basis_endpoint is not None:
                raise ExtractionError("duplicate rank-basis endpoint")
            basis_endpoint = {
                "endpoint_causet_id": endpoint_id,
                "endpoint_stage": stage,
                "state": endpoint["state"],
                "anchor_path_id": endpoint.get("anchor_path_id"),
            }
    if len(set(endpoint_ids)) != 87:
        raise ExtractionError("duplicate reachable endpoint ID")
    if basis_endpoint is None:
        raise ExtractionError("rank-basis endpoint p1-0 is missing")
    if not any(vector != (Fraction(0), Fraction(0)) for vector in vectors):
        raise ExtractionError("reachable span has rank zero")
    for left_index, left in enumerate(vectors):
        for right in vectors[left_index + 1 :]:
            if left[0] * right[1] - left[1] * right[0] != 0:
                raise ExtractionError("reachable span has rank greater than one")
    derived_unique_states = sorted(vector_texts)
    expected_stage_counts = {"1": 1, "2": 2, "3": 5, "4": 16, "5": 63}
    _require_equal(path_count, 407, "derived reachable path count")
    _require_equal(stage_counts, expected_stage_counts, "derived endpoint stage counts")
    _require_equal(summary.get("path_count"), path_count, "summary path_count")
    _require_equal(summary.get("endpoint_count"), len(endpoints), "summary endpoint_count")
    _require_equal(summary.get("stage_counts"), stage_counts, "summary stage_counts")
    _require_equal(
        summary.get("all_same_endpoint_paths_give_same_state"),
        True,
        "summary same-endpoint gate",
    )
    _require_equal(summary.get("all_states_nonzero"), True, "summary nonzero-state gate")
    _require_equal(summary.get("reachable_span_rank"), 1, "summary reachable rank")
    _require_equal(summary.get("rank_basis_endpoint_ids"), ["p1-0"], "summary rank basis")
    _require_equal(summary.get("unique_state_vectors"), derived_unique_states, "unique states")
    _require_equal(basis_endpoint["state"], ["1", "0"], "rank-basis state")
    classification = _mapping(
        observability.get("baseline_classification"), "baseline_classification"
    )
    _require_equal(
        classification,
        {
            "operator_noncommutative": True,
            "reachable_span_rank": 1,
            "reachable_visible": False,
            "label": "EXACT_OFF_REACHABLE_SECTOR_NONCOMMUTATIVITY",
        },
        "baseline classification",
    )
    return {
        "arithmetic": "fractions.Fraction exact rationals",
        "initial_vector": ["1", "0"],
        "path_count": path_count,
        "endpoint_count": len(endpoints),
        "endpoint_stage_counts": stage_counts,
        "all_same_endpoint_paths_give_same_state": True,
        "all_states_nonzero": True,
        "all_states_are_rational_multiples_of_Omega": True,
        "reachable_span_rank": 1,
        "rank_basis_endpoint": basis_endpoint,
        "unique_state_vectors": derived_unique_states,
        "operator_noncommutative": True,
        "reachable_visible": False,
    }


def _extract_representatives(
    observability: dict[str, Any],
    weak_gc: dict[str, Any],
    weak_msr: dict[str, Any],
) -> dict[str, Any]:
    residual_visibility = _mapping(observability.get("residual_visibility"), "residual_visibility")
    gc = _mapping(residual_visibility.get("fixed_vector_GC"), "fixed_vector_GC")
    _require_equal(gc.get("checked_path_pairs"), 1529, "observable GC pair count")
    _require_equal(gc.get("operator_nonzero_residual_count"), 986, "observable GC failures")
    _require_equal(gc.get("fixed_state_nonzero_action_count"), 0, "observable GC actions")
    gc_record = _mapping(gc.get("first_operator_nonzero_residual"), "first GC operator residual")
    expected_gc = {
        "endpoint_causet_id": "p3-002",
        "left_path_id": "lgc-path-73192a6770fa82828f12",
        "right_path_id": "lgc-path-fc1eafd06aa0360d6535",
        "operator_residual": [["0", "-1/2"], ["0", "0"]],
        "action_on_Omega": ["0", "0"],
    }
    _require_equal(gc_record, expected_gc, "representative observability GC residual")
    _require_equal(
        weak_gc["operator_residual"], expected_gc["operator_residual"], "weak/observable GC"
    )
    _require_equal(
        weak_gc["fixed_vector_residual"], expected_gc["action_on_Omega"], "weak GC action"
    )

    msr = _mapping(residual_visibility.get("reachable_state_MSR"), "reachable_state_MSR")
    _require_equal(msr.get("checked_source_residuals"), 24, "observable MSR count")
    _require_equal(msr.get("operator_nonzero_residual_count"), 24, "observable MSR failures")
    _require_equal(msr.get("source_state_nonzero_action_count"), 0, "observable MSR actions")
    msr_records = _sequence(msr.get("records"), "observable MSR records")
    matching = [
        _mapping(record, "observable MSR record")
        for record in msr_records
        if isinstance(record, dict) and record.get("constraint_id") == "msr:p1-0"
    ]
    if len(matching) != 1:
        raise ExtractionError("representative observability MSR record is not unique")
    expected_msr = {
        "constraint_id": "msr:p1-0",
        "source_id": "p1-0",
        "source_state": ["1", "0"],
        "operator_residual": [["0", "2"], ["0", "1"]],
        "action_on_source_state": ["0", "0"],
        "operator_nonzero": True,
        "state_action_nonzero": False,
    }
    _require_equal(matching[0], expected_msr, "representative observability MSR residual")
    _require_equal(
        weak_msr["operator_residual"], expected_msr["operator_residual"], "weak/observable MSR"
    )
    _require_equal(
        weak_msr["reachable_state_residual_on_omega_ray"],
        expected_msr["action_on_source_state"],
        "weak MSR action",
    )
    return {
        "fixed_vector_GC": expected_gc,
        "reachable_state_MSR": {
            **expected_msr,
            "reachable_state_residual_on_omega_ray": weak_msr[
                "reachable_state_residual_on_omega_ray"
            ],
        },
    }


def _family_census(family_ids: dict[str, list[str]]) -> dict[str, Any]:
    _require_equal(set(family_ids), set(EXPECTED_FAMILY_COUNTS), "census family names")
    seen: set[str] = set()
    families: list[dict[str, Any]] = []
    derived_total = 0
    for family in EXPECTED_FAMILY_COUNTS:
        identifiers = _unique_ids(family, family_ids[family], EXPECTED_FAMILY_COUNTS[family])
        collisions = seen.intersection(identifiers)
        if collisions:
            raise ExtractionError(f"cross-family natural ID collision in {family}")
        seen.update(identifiers)
        count = len(identifiers)
        derived_total += count
        families.append(
            {
                "family": family,
                "record_count": count,
                "natural_ids": identifiers,
                "natural_ids_sha256": _sha256_bytes(canonical_json_bytes(identifiers)),
            }
        )
    _require_equal(derived_total, EXPECTED_TOTAL_RECORDS, "derived top-level record total")
    return {
        "composite_id_encoding": (
            "family-name followed by ':' and the canonical JSON array of ordered natural "
            "source-ID components; this is injective and preserves component types"
        ),
        "composite_id_definitions": {
            "transition_occurrences": "TRANSITION:[occurrence_id]",
            "CPOBC": "CPOBC:[relation_id,equation_id]",
            "CPOBC_inverse_rewrites": ("CPOBC_inverse_rewrites:[relation_id,equation_id]"),
            "GC": "GC:[endpoint_causet_id,left_path_id,right_path_id]",
            "MSR": "MSR:[constraint_id]",
            "Eq113_QN": "Eq113_QN:[causet_id,alpha_path_id,beta_path_id,Q_token]",
            "Eq113_QN_PLUS_1": ("Eq113_QN_PLUS_1:[causet_id,alpha_path_id,beta_path_id,Q_token]"),
            "Eq139_PRINTED_STRICT": "Eq139_PRINTED_STRICT:[stage_n,m,k]",
            "Eq139_EQ145_COMPLETED": "Eq139_EQ145_COMPLETED:[stage_n,m,k]",
            "Q_commutators": "Q_commutators:[left_stage,right_stage]",
        },
        "natural_id_digest_method": (
            "SHA-256 of UTF-8 json.dumps(sorted_ids, ensure_ascii=True, "
            "sort_keys=True, separators=(',', ':'), allow_nan=False)"
        ),
        "families": families,
        "derived_total_top_level_records": derived_total,
        "expected_total_top_level_records": EXPECTED_TOTAL_RECORDS,
    }


def build_payload(repository_root: Path) -> dict[str, Any]:
    """Authenticate sources, validate their contracts, and build the compact payload."""

    raw_inputs = _read_authenticated_inputs(repository_root)
    weak = _parse_json(raw_inputs[WEAK_PATH], WEAK_PATH)
    observability = _parse_json(raw_inputs[OBSERVABILITY_PATH], OBSERVABILITY_PATH)
    _validate_authority_headers(weak, observability)

    formulas, q_inventory = _extract_formulas_and_q(weak)
    transition_tables, occurrence_ids = _extract_transition_tables(weak)
    substitution_ids, weak_gc, weak_msr = _extract_substitution_ids(weak)
    commutators, commutator_ids = _extract_commutators(weak, observability)
    rank_one = _extract_rank_one_evidence(observability)
    representatives = _extract_representatives(observability, weak_gc, weak_msr)

    family_ids = {
        "transition_occurrences": [
            _natural_id("TRANSITION", occurrence_id) for occurrence_id in occurrence_ids
        ],
        **substitution_ids,
        "Q_commutators": commutator_ids,
    }
    census = _family_census(family_ids)
    source_bindings = []
    for relative_path in sorted(SOURCE_SPECS):
        specification = SOURCE_SPECS[relative_path]
        binding = {
            "path": relative_path,
            "raw_sha256": specification["raw_sha256"],
            "role": specification["role"],
        }
        if relative_path == OBSERVABILITY_PATH:
            binding["semantic_digest_sha256"] = specification["semantic_sha256"]
            binding["semantic_digest_method"] = (
                "exclude top-level semantic_digest_sha256; canonical JSON; UTF-8; SHA-256"
            )
        source_bindings.append(binding)

    payload: dict[str, Any] = {
        "schema_version": OUTPUT_SCHEMA,
        "date": "2026-08-05",
        "field": "Q",
        "dimension": 2,
        "scope": {
            "purpose": "compact proof-facing Paper I witness tables",
            "complete_electronic_ledger_authority": WEAK_PATH,
            "omitted_full_record_payloads_remain_bound_by_raw_sha256": True,
            "claim_boundary": (
                "This extraction reports the frozen finite n<=4 weak witness and the "
                "independent baseline observability audit. It does not enlarge either claim."
            ),
        },
        "source_bindings": source_bindings,
        "canonicalization": {
            "tracked_bytes": (
                "json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(',', ':'), "
                "allow_nan=False), UTF-8, one trailing LF"
            ),
            "semantic_digest": (
                "exclude top-level semantic_digest_sha256, apply tracked canonical JSON "
                "encoding without trailing LF, then SHA-256"
            ),
        },
        "formulas": formulas,
        "Q_inventory": q_inventory,
        "transition_tables": transition_tables,
        "family_census": census,
        "commutators": commutators,
        "reachable_rank_one_evidence": rank_one,
        "representative_residuals": representatives,
        "gates": {
            "all_sources_raw_authenticated_before_extraction": True,
            "observability_semantic_digest_recomputed": True,
            "independent_oracle_raw_bound": True,
            "transition_orbit_invariants_verified": True,
            "all_family_counts_and_natural_ids_verified": True,
            "reachable_rank_one_recomputed_over_exact_rationals": True,
            "representative_residuals_cross_checked": True,
        },
        "passed": True,
        "verdict": OUTPUT_VERDICT,
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def _atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def run(repository_root: Path, *, write: bool) -> dict[str, Any]:
    payload = build_payload(repository_root)
    expected = output_bytes(payload)
    output_path = repository_root / OUTPUT_PATH
    if write:
        _atomic_write(output_path, expected)
        print("paper1_witness_tables=WRITTEN")
        return payload
    if not output_path.is_file():
        raise ExtractionError(f"missing tracked output: {OUTPUT_PATH}")
    tracked_raw = output_path.read_bytes()
    tracked = _parse_json(tracked_raw, OUTPUT_PATH)
    _require_equal(
        tracked.get("semantic_digest_sha256"),
        semantic_digest(tracked),
        "tracked output self semantic digest",
    )
    if canonical_json_bytes(tracked) != canonical_json_bytes(payload):
        raise ExtractionError("tracked output canonical semantics differ from regeneration")
    if tracked_raw != expected:
        raise ExtractionError("tracked output bytes are not the regenerated canonical bytes")
    print("paper1_witness_tables=OK")
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository_root", nargs="?", type=Path, default=Path.cwd())
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="read-only verification (default)")
    mode.add_argument("--write", action="store_true", help="atomically replace the tracked JSON")
    return parser


def main() -> None:
    arguments = _parser().parse_args()
    del arguments.check
    run(arguments.repository_root.resolve(), write=arguments.write)


if __name__ == "__main__":
    main()
