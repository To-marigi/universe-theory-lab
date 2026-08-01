"""Source-native provenance certificate for the three k=1 Eq. (120) instances.

The certificate deliberately starts from the raw Eq. (103) words in the
v0.3.1 CPOBC inventory.  The v0.3.2 occurrence ledger is used only to identify
the four antichain gregarious occurrences with ``Q_1,...,Q_4``.  In
particular, no stored reduction of a ``B`` occurrence is used: those
reductions contain Eq. (108), which is outside reachable-state MSR semantics.

For ``1=k<m<n<=4`` the selected raw relations are

    B_n Q_m = B_m Q_n,
    B_m Q_1 = B_1 Q_m,
    B_n Q_1 = B_1 Q_n.

Source nonsingularity permits the exact free-word cancellations that give

    Q_n Q_1^-1 Q_m = Q_m Q_1^-1 Q_n.

The proof is dimension-independent.  This artifact records the d=2 use made
by the R2--R4 chart cover, and it makes no ideal-membership claim for the 700
direct relations away from the source reconstruction image.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "final-theory-v042-eq120-source-provenance-certificate-v0.4.2"
VERDICT = "V042_EQ120_SOURCE_NATIVE_PROVENANCE_PROVED"

PRIMARY_PAPER_PATH = (
    "references/papers/2603.25503v1_srivastava-surya_quantum-bell-causality-qsg.pdf"
)
SOURCE_CPOBC_PATH = "results/v0.3.1_cpobc_relations_n4.json"
REDUCTION_PATH = "results/v0.3.2_cpobc_generator_reduction.json"
DIRECT_SYSTEM_PATH = "certificates/d2_saturation/v0.3.5_direct_operator_system.json"
RESULT_PATH = "results/v0.4.2_eq120_source_provenance.json"

DIRECT_BRANCH = "LITERAL_PRINTED_QN_PLUS_1_BRANCH"

Word = tuple[str, ...]
Equality = tuple[Word, Word]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"JSON artifact must be an object: {path}")
    return payload


def semantic_digest(payload: dict[str, Any]) -> str:
    """Return the canonical digest after removing the self-digest field."""

    semantic = {key: value for key, value in payload.items() if key != "semantic_digest_sha256"}
    return _stable_hash(semantic)


def _inverse_token(token: str) -> str:
    return token.removesuffix("^-1") if token.endswith("^-1") else f"{token}^-1"


def _free_reduce(word: Word) -> Word:
    reduced: list[str] = []
    for token in word:
        if reduced and reduced[-1] == _inverse_token(token):
            reduced.pop()
        else:
            reduced.append(token)
    return tuple(reduced)


def _multiply_equality(
    equality: Equality,
    *,
    left: Word = (),
    right: Word = (),
) -> Equality:
    return (
        _free_reduce(left + equality[0] + right),
        _free_reduce(left + equality[1] + right),
    )


def _replace_prefix(word: Word, old: Word, new: Word) -> Word:
    if word[: len(old)] != old:
        raise AssertionError(f"cannot replace non-prefix {old!r} in {word!r}")
    return _free_reduce(new + word[len(old) :])


def _semantic_word(word: list[str], n: int, m: int) -> Word:
    aliases = {
        "A_n": f"B_{n}",
        "A_prime_n": f"Q_{n}",
        "A_m": f"B_{m}",
        "A_prime_m": f"Q_{m}",
    }
    semantic: list[str] = []
    for token in word:
        inverse = token.endswith("^-1")
        base = token.removesuffix("^-1")
        if base not in aliases:
            raise AssertionError(f"unexpected raw CPOBC alias: {token}")
        mapped = aliases[base]
        semantic.append(f"{mapped}^-1" if inverse else mapped)
    return tuple(semantic)


def _is_antichain_source(source: dict[str, Any], stage: int) -> bool:
    rows = source.get("canonical_relation_rows")
    return source.get("id", "").startswith(f"p{stage}-") and rows == [0] * stage


def _raw_selection_key(record: dict[str, Any]) -> tuple[int, int] | None:
    stage = record.get("stage", {})
    n = stage.get("n")
    m = stage.get("m")
    if not isinstance(n, int) or not isinstance(m, int) or not (1 <= m < n <= 4):
        return None
    source = record.get("source_causet", {})
    if not (
        _is_antichain_source(source.get("stage_n", {}), n)
        and _is_antichain_source(source.get("stage_m", {}), m)
    ):
        return None
    expected_precursors = {
        "stage_n": {"A": [0], "A_prime": []},
        "stage_m": {"A": [0], "A_prime": []},
    }
    if record.get("full_precursor") != expected_precursors:
        return None
    if record.get("branch") != "GREATER":
        return None
    return n, m


def _validate_raw_record(record: dict[str, Any], n: int, m: int) -> None:
    relation_id = str(record.get("relation_id"))
    relation_hash = str(record.get("relation_hash"))
    if relation_id != f"cpobc-relation-{relation_hash[:20]}":
        raise AssertionError(f"relation ID/hash mismatch: {relation_id}")
    if record.get("Bell_family", {}).get("core_stage") != 1:
        raise AssertionError(f"unexpected Bell-family root: {relation_id}")
    raw = record.get("raw_noncommutative_relation")
    if not isinstance(raw, list) or len(raw) != 1:
        raise AssertionError(f"raw Eq. (103) record missing: {relation_id}")
    raw_eq = raw[0]
    if raw_eq.get("equation_id") != "eq103":
        raise AssertionError(f"wrong raw equation: {relation_id}")
    lhs = _semantic_word(raw_eq.get("lhs_word", []), n, m)
    rhs = _semantic_word(raw_eq.get("rhs_word", []), n, m)
    if (lhs, rhs) != ((f"B_{n}", f"Q_{m}"), (f"B_{m}", f"Q_{n}")):
        raise AssertionError(f"raw CPOBC word order changed: {relation_id}")

    forms = record.get("inverse_containing_form", {}).get("forms")
    if not isinstance(forms, list) or len(forms) != 1:
        raise AssertionError(f"Eq. (105) form missing: {relation_id}")
    form = forms[0]
    semantic_terms = [
        {
            "coefficient": int(term["coefficient"]),
            "word": list(_semantic_word(term["word"], n, m)),
        }
        for term in form.get("residual_terms", [])
    ]
    expected_terms = [
        {"coefficient": 1, "word": [f"B_{n}"]},
        {
            "coefficient": -1,
            "word": [f"B_{m}", f"Q_{n}", f"Q_{m}^-1"],
        },
    ]
    if form.get("equation_id") != "eq105" or semantic_terms != expected_terms:
        raise AssertionError(f"Eq. (105) word order changed: {relation_id}")

    transition_orbit = record.get("transition_orbit", {})
    operator_ids = raw_eq.get("operator_ids", {})
    for alias in ("A_n", "A_prime_n", "A_m", "A_prime_m"):
        if transition_orbit.get(alias, {}).get("occurrence_id") != operator_ids.get(alias):
            raise AssertionError(f"occurrence binding changed for {relation_id}:{alias}")
    if record.get("MSR_dependency", {}).get("used_to_generate_this_relation") is not False:
        raise AssertionError(f"raw relation unexpectedly depends on MSR: {relation_id}")
    if record.get("GC_dependency", {}).get("used_to_generate_this_relation") is not False:
        raise AssertionError(f"raw relation unexpectedly depends on GC: {relation_id}")
    correspondence = record.get("paper_equation_correspondence", {})
    if correspondence.get("paper") != "arXiv:2603.25503v1" or correspondence.get("equations") != [
        103,
        105,
    ]:
        raise AssertionError(f"paper-equation binding changed: {relation_id}")


def _select_raw_relations(source: dict[str, Any]) -> dict[tuple[int, int], dict[str, Any]]:
    selected: dict[tuple[int, int], dict[str, Any]] = {}
    for raw_record in source.get("relations", []):
        if not isinstance(raw_record, dict):
            continue
        key = _raw_selection_key(raw_record)
        if key is None:
            continue
        if key in selected:
            raise AssertionError(f"raw Eq. (115) candidate is not unique: {key}")
        _validate_raw_record(raw_record, *key)
        selected[key] = raw_record
    expected = {(n, m) for n in range(2, 5) for m in range(1, n)}
    if set(selected) != expected:
        raise AssertionError(
            f"raw Eq. (115) inventory changed: {sorted(selected)} != {sorted(expected)}"
        )
    return selected


def _occurrence_record(relation: dict[str, Any], alias: str, semantic_name: str) -> dict[str, Any]:
    occurrence = relation["transition_orbit"][alias]
    return {
        "semantic_name": semantic_name,
        "occurrence_id": occurrence["occurrence_id"],
        "orbit_id": occurrence["orbit_id"],
        "operator_variable": occurrence["operator_variable"],
    }


def _semantic_eq105(record: dict[str, Any], n: int, m: int) -> Equality:
    raw_eq = record["raw_noncommutative_relation"][0]
    raw_equality = (
        _semantic_word(raw_eq["lhs_word"], n, m),
        _semantic_word(raw_eq["rhs_word"], n, m),
    )
    derived = _multiply_equality(raw_equality, right=(f"Q_{m}^-1",))
    expected = ((f"B_{n}",), (f"B_{m}", f"Q_{n}", f"Q_{m}^-1"))
    if derived != expected:
        raise AssertionError(f"Eq. (103) -> Eq. (105) derivation failed for {(n, m)}")
    return derived


def _word_equality_record(label: str, equality: Equality) -> dict[str, Any]:
    return {"label": label, "lhs_word": list(equality[0]), "rhs_word": list(equality[1])}


def _derive_pair_certificate(
    selected: dict[tuple[int, int], dict[str, Any]], n: int, m: int
) -> dict[str, Any]:
    k = 1
    eq115_record = selected[(n, m)]
    eq116_record = selected[(m, k)]
    eq117_record = selected[(n, k)]
    eq115 = _semantic_eq105(eq115_record, n, m)
    eq116 = _semantic_eq105(eq116_record, m, k)
    eq117 = _semantic_eq105(eq117_record, n, k)

    # Eq. (118): equate the two descriptions of B_n, then replace the B_m
    # prefix on the Eq. (115) side by Eq. (116).
    eq118_lhs = eq117[1]
    eq118_rhs = _replace_prefix(eq115[1], eq116[0], eq116[1])
    eq118 = (eq118_lhs, eq118_rhs)
    expected_eq118 = (
        (f"B_{k}", f"Q_{n}", f"Q_{k}^-1"),
        (
            f"B_{k}",
            f"Q_{m}",
            f"Q_{k}^-1",
            f"Q_{n}",
            f"Q_{m}^-1",
        ),
    )
    if eq118 != expected_eq118:
        raise AssertionError(f"Eq. (118) derivation failed for {(n, m)}")

    # Left-cancel B_1 and right-multiply by Q_m.  Both operations are licensed
    # by the source nonsingularity assumption, not by MSR or GC.
    cancelled = _multiply_equality(eq118, left=(f"B_{k}^-1",))
    eq119 = _multiply_equality(cancelled, right=(f"Q_{m}",))
    expected_eq119 = (
        (f"Q_{n}", f"Q_{k}^-1", f"Q_{m}"),
        (f"Q_{m}", f"Q_{k}^-1", f"Q_{n}"),
    )
    if eq119 != expected_eq119:
        raise AssertionError(f"Eq. (119)/(120) derivation failed for {(n, m)}")

    relation_ids = [
        eq115_record["relation_id"],
        eq116_record["relation_id"],
        eq117_record["relation_id"],
    ]
    content = [eq115_record, eq116_record, eq117_record]
    target_residual = [
        {"coefficient": 1, "word": list(eq119[0])},
        {"coefficient": -1, "word": list(eq119[1])},
    ]
    return {
        "indices": [m, n],
        "orientation": {"k": k, "m": m, "n": n},
        "source_relation_ids": relation_ids,
        "source_relation_roles": {
            "paper_eq115_n_vs_m": relation_ids[0],
            "paper_eq116_m_vs_k": relation_ids[1],
            "paper_eq117_n_vs_k": relation_ids[2],
        },
        "source_relation_content_sha256": _stable_hash(content),
        "paper_premises": [
            _word_equality_record("Eq.(115)", eq115),
            _word_equality_record("Eq.(116)", eq116),
            _word_equality_record("Eq.(117)", eq117),
        ],
        "free_word_derivation": [
            _word_equality_record("Eq.(118)", eq118),
            _word_equality_record("left-cancel B_1", cancelled),
            _word_equality_record("Eq.(119)/(120)", eq119),
        ],
        "target_residual": target_residual,
        "target_residual_display": (f"Q_{n}*Q_1^-1*Q_{m} - Q_{m}*Q_1^-1*Q_{n}"),
        "verified": True,
    }


def _identify_q_occurrences(
    selected: dict[tuple[int, int], dict[str, Any]], reduction: dict[str, Any]
) -> list[dict[str, Any]]:
    expected_occurrences: dict[int, str] = {}
    expected_orbits: dict[int, str] = {}
    for (n, m), relation in selected.items():
        for stage, alias in ((n, "A_prime_n"), (m, "A_prime_m")):
            occurrence = relation["transition_orbit"][alias]
            occurrence_id = str(occurrence["occurrence_id"])
            orbit_id = str(occurrence["orbit_id"])
            if stage in expected_occurrences and expected_occurrences[stage] != occurrence_id:
                raise AssertionError(f"Q_{stage} occurrence is inconsistent across relations")
            if stage in expected_orbits and expected_orbits[stage] != orbit_id:
                raise AssertionError(f"Q_{stage} orbit is inconsistent across relations")
            expected_occurrences[stage] = occurrence_id
            expected_orbits[stage] = orbit_id

    reduction_by_occurrence = {
        str(record["occurrence_id"]): record for record in reduction.get("reduction_map", [])
    }
    records: list[dict[str, Any]] = []
    for stage in range(1, 5):
        occurrence_id = expected_occurrences[stage]
        item = reduction_by_occurrence.get(occurrence_id)
        if item is None:
            raise AssertionError(f"Q_{stage} occurrence is absent from the ON ledger")
        expected_expression = [{"coefficient": 1, "word": [f"Q_{stage}"]}]
        if not (
            item.get("stage") == stage
            and item.get("source_relation_rows") == [0] * stage
            and item.get("precursor") == []
            and item.get("transition_kind") == "GREGARIOUS"
            and item.get("derivation") == "definition of the source-causet gregarious transition"
            and item.get("reduced_expression") == expected_expression
            and item.get("generator_dependencies") == [f"Q_{stage}"]
            and item.get("exact") is True
        ):
            raise AssertionError(f"Q_{stage} identifier binding changed")
        records.append(
            {
                "stage": stage,
                "semantic_name": f"Q_{stage}",
                "occurrence_id": occurrence_id,
                "transition_hash": item["transition_hash"],
                "orbit_id": expected_orbits[stage],
                "source_id": item["source_id"],
                "operator_variable": item["operator_variable"],
                "identifier_rule": item["derivation"],
                "reduced_expression": expected_expression,
                "used_as_identifier_only": True,
            }
        )
    return records


def _raw_inventory_record(key: tuple[int, int], relation: dict[str, Any]) -> dict[str, Any]:
    n, m = key
    return {
        "stage_pair": [n, m],
        "relation_id": relation["relation_id"],
        "relation_hash": relation["relation_hash"],
        "relation_content_sha256": _stable_hash(relation),
        "source_ids": [
            relation["source_causet"]["stage_n"]["id"],
            relation["source_causet"]["stage_m"]["id"],
        ],
        "bell_family_id": relation["Bell_family"]["id"],
        "precursor_codes": {"B": 1, "Q": 0},
        "occurrences": {
            "B_n": _occurrence_record(relation, "A_n", f"B_{n}"),
            "Q_n": _occurrence_record(relation, "A_prime_n", f"Q_{n}"),
            "B_m": _occurrence_record(relation, "A_m", f"B_{m}"),
            "Q_m": _occurrence_record(relation, "A_prime_m", f"Q_{m}"),
        },
        "eq103": _word_equality_record("Eq.(103)", ((f"B_{n}", f"Q_{m}"), (f"B_{m}", f"Q_{n}"))),
        "eq105": _word_equality_record("Eq.(105)", _semantic_eq105(relation, n, m)),
        "dependency_flags": {
            "CPOBC_axiom_instance": True,
            "MSR_used": False,
            "GC_used": False,
            "Eq108_used": False,
            "Eq112_used": False,
        },
    }


def compile_eq120_source_provenance_v042(root: Path) -> dict[str, Any]:
    """Build and independently recheck the exact source-native certificate."""

    primary_path = root / PRIMARY_PAPER_PATH
    source_path = root / SOURCE_CPOBC_PATH
    reduction_path = root / REDUCTION_PATH
    direct_path = root / DIRECT_SYSTEM_PATH
    source = _load(source_path)
    reduction = _load(reduction_path)
    direct = _load(direct_path)

    if source.get("schema_version") != "final-theory-cpobc-relations-v0.3.1":
        raise AssertionError("unexpected source CPOBC schema")
    if "CPOBC transition operators are nonsingular" not in source.get("assumptions", []):
        raise AssertionError("source nonsingularity assumption is absent")
    primary_sha256 = _sha256(primary_path)
    paper_records = {str(record.get("id")): record for record in source.get("paper_versions", [])}
    if paper_records.get("arXiv:2603.25503v1", {}).get("sha256") != primary_sha256:
        raise AssertionError("primary-paper hash does not match the source inventory")

    selected = _select_raw_relations(source)
    q_occurrences = _identify_q_occurrences(selected, reduction)
    raw_inventory = [_raw_inventory_record(key, selected[key]) for key in sorted(selected)]
    pair_certificates = [
        _derive_pair_certificate(selected, n, m) for m, n in ((2, 3), (2, 4), (3, 4))
    ]

    direct_records = direct.get("relations", {}).get(DIRECT_BRANCH)
    if not isinstance(direct_records, list):
        raise AssertionError("literal direct branch is absent")
    selected_700 = [record for record in direct_records if record.get("family") == "CPOBC"]
    if len(selected_700) != 700:
        raise AssertionError("selected direct CPOBC count changed")
    selected_ids = sorted(str(record["relation_id"]) for record in selected_700)
    direct_by_id = {str(record["relation_id"]): record for record in selected_700}
    selected_pair_bindings: list[dict[str, Any]] = []
    for pair in pair_certificates:
        n = int(pair["orientation"]["n"])
        m = int(pair["orientation"]["m"])
        source_relation_id = str(pair["source_relation_ids"][0])
        direct_relation_id = f"{source_relation_id}:eq103"
        direct_record = direct_by_id.get(direct_relation_id)
        if direct_record is None:
            raise AssertionError(f"selected 700 lacks pair record {direct_relation_id}")
        selected_pair_bindings.append(
            {
                "indices": [m, n],
                "source_relation_id": source_relation_id,
                "selected_direct_relation_id": direct_relation_id,
                "selected_direct_relation_content_sha256": _stable_hash(direct_record),
                "direct_expression_used_as_source_proof": False,
            }
        )

    raw_dependency_flags = [item["dependency_flags"] for item in raw_inventory]
    dependency_passed = all(
        flags
        == {
            "CPOBC_axiom_instance": True,
            "MSR_used": False,
            "GC_used": False,
            "Eq108_used": False,
            "Eq112_used": False,
        }
        for flags in raw_dependency_flags
    ) and all(item["used_as_identifier_only"] is True for item in q_occurrences)
    if not dependency_passed:
        raise AssertionError("forbidden semantic dependency entered the Eq. (120) proof")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "scope": {
            "finite_stages": "n<=4",
            "target_dimension": 2,
            "algebraic_derivation_dimension": "dimension-independent",
            "profile_use": "strong_GC__reachable_state_MSR__ON_QUOTIENT_partial_slice",
        },
        "primary_source": {
            "paper": "arXiv:2603.25503v1",
            "path": PRIMARY_PAPER_PATH,
            "sha256": primary_sha256,
            "visually_checked_pdf_pages": [27, 28],
            "equations_checked": [103, 105, 115, 116, 117, 118, 119, 120],
        },
        "input_hashes": {
            "source_cpobc_relations": {
                "path": SOURCE_CPOBC_PATH,
                "sha256": _sha256(source_path),
            },
            "generator_reduction": {
                "path": REDUCTION_PATH,
                "sha256": _sha256(reduction_path),
            },
            "direct_system": {
                "path": DIRECT_SYSTEM_PATH,
                "sha256": _sha256(direct_path),
            },
        },
        "selected_700_relation_ids": {
            "branch": DIRECT_BRANCH,
            "family": "CPOBC",
            "count": len(selected_ids),
            "ordered_ids_sha256": _stable_hash(selected_ids),
        },
        "raw_selection_rule": {
            "stage_pairs": [[n, m] for n in range(2, 5) for m in range(1, n)],
            "both_sources": "canonical antichains",
            "precursor_pair_at_both_stages": {"B": [0], "Q": []},
            "branch": "GREATER",
            "paper_equations": [103, 105],
            "uniqueness_required": True,
        },
        "raw_relation_inventory": raw_inventory,
        "q_occurrence_identification": q_occurrences,
        "pair_certificates": pair_certificates,
        "selected_700_pair_bindings": selected_pair_bindings,
        "dependency_closure": {
            "axioms_used": [
                "six raw CPOBC Eq.(103) instances",
                "source transition nonsingularity",
            ],
            "definitions_used": [
                "Q_s is the empty-precursor gregarious occurrence from the s-antichain"
            ],
            "source_nonsingularity_operations": [
                "right multiplication by Q_m^-1 in Eq.(103)->Eq.(105)",
                "left cancellation of B_1",
                "right multiplication by Q_m",
            ],
            "occurrence_ledger_use": "identifier-only for the four Q occurrences",
            "B_reduced_expressions_used": False,
            "MSR_used": False,
            "GC_used": False,
            "Eq108_used": False,
            "Eq112_used": False,
            "dependency_closed": True,
        },
        "counts": {
            "unique_raw_relations": len(raw_inventory),
            "unique_Q_occurrences": len(q_occurrences),
            "unique_B_occurrences": len(
                {
                    occurrence["occurrence_id"]
                    for item in raw_inventory
                    for name, occurrence in item["occurrences"].items()
                    if name.startswith("B_")
                }
            ),
            "k1_Eq120_instances": len(pair_certificates),
            "selected_direct_pair_bindings": len(selected_pair_bindings),
        },
        "chart_cover_gate": {
            "partial_slice_955": "CLOSED_SOURCE_NATIVE_EQ120_PREMISES",
            "abstract_R2_R4_partition": "SOURCE_NATIVE_REUSABLE",
            "reason": (
                "Every source point satisfies the six raw CPOBC instances and source "
                "nonsingularity, hence all three k=1 Eq.(120) identities.  With det(Q_1)!=0, "
                "the independently checked adjugate identity makes R_2,R_3,R_4 commute."
            ),
            "future_slack_compilers": (
                "The same source-native derivation survives arbitrary reachable-MSR slack "
                "because it never substitutes a B occurrence through Eq.(108) or Eq.(112)."
            ),
            "selected_700_direct_ideal_membership_claimed": False,
            "claim_boundary": (
                "This proves Eq.(120) on the source-native nonsingular locus, including the "
                "audited source reconstruction slice.  It does not prove Eq.(120) on an "
                "arbitrary 700-relation direct point outside that source image."
            ),
        },
        "verdict": VERDICT,
        "passed": True,
    }
    payload["semantic_digest_sha256"] = semantic_digest(payload)
    return payload


def verify_eq120_source_provenance_v042(root: Path, payload: dict[str, Any]) -> bool:
    """Fail closed unless every source binding and derived word is current."""

    if payload.get("schema_version") != SCHEMA:
        return False
    if payload.get("semantic_digest_sha256") != semantic_digest(payload):
        return False
    return payload == compile_eq120_source_provenance_v042(root)
