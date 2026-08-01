from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from universe_lab.final_theory import partial_slice_audit_v041 as audit_module

ROOT = Path(__file__).resolve().parents[2]


def _stable_hash(value: Any) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@pytest.fixture(scope="module")
def audit() -> dict[str, Any]:
    return audit_module.audit_partial_slice_v041(ROOT)


def test_source_relations_pull_back_exactly_to_the_955_core(
    audit: dict[str, Any],
) -> None:
    checks = audit["checks"]
    cpobc = checks["CPOBC_pullback"]
    gc = checks["strong_GC_pullback"]

    assert cpobc["passed"] is True
    assert (
        cpobc["source_equation_count"],
        cpobc["identically_zero_pullback_count"],
        cpobc["nonzero_direct_pullback_count"],
    ) == (783, 83, 700)
    assert gc["passed"] is True
    assert gc["source_same_endpoint_pair_count"] == 1529
    assert (
        gc["source_basis_relation_count"],
        gc["identically_zero_pullback_count"],
        gc["nonzero_direct_pullback_count"],
    ) == (320, 65, 255)


def test_every_localisation_factor_has_an_audited_source_origin(
    audit: dict[str, Any],
) -> None:
    check = audit["checks"]["inverse_and_nonsingularity"]

    assert check["passed"] is True
    assert check["reconstructed_transition_predicate_count"] == 165
    assert check["Q_inverse_site_count"] == 4
    assert check["B_inverse_site_count"] == 22
    assert check["inverse_site_source_occurrence_count"] == 26


def test_chart_commutators_and_all_21_QQ_certificates_are_independently_bound(
    audit: dict[str, Any],
) -> None:
    check = audit["checks"]["chart_cover_and_QQ_certificates"]

    assert check["passed"] is True
    assert (check["S1_chart_count"], check["S2_chart_count"]) == (12, 9)
    assert check["S3_structurally_commuting"] is True
    assert check["conditional_exhaustiveness_lemma"]["passed"] is True
    assert check["independently_recomputed_nonzero_commutator_component_count"] == 140
    assert check["all_omitted_commutator_components_independently_zero"] is True
    assert check["QQ_exact_empty_chart_count"] == 12
    assert check["QQ_exact_no_noncommutative_solution_chart_count"] == 9
    assert check["nonempty_charts_with_all_165_transition_predicates"] == 9
    assert check["independent_oracle_bound"] is True


def test_claim_direction_and_result_digest_are_fail_closed(
    audit: dict[str, Any],
) -> None:
    inclusion = audit["inclusion"]
    certificate_exists = (ROOT / audit_module.EQ120_PROVENANCE_PATH).is_file()

    assert certificate_exists
    assert inclusion["direction"] == "P intersection image(Phi_U) subset Phi_U(D_955)"
    assert inclusion["relation_locus_inclusion_proved"] is True
    assert inclusion["commutativity_consequence_proved"] is True
    assert inclusion["reverse_inclusion_claimed"] is False
    assert inclusion["full_profile_coverage_claimed"] is False
    assert audit["verdict"] == audit_module.VERDICT_PROVED
    assert audit["passed"] is True

    expected_digest = _stable_hash(
        {key: value for key, value in audit.items() if key != "semantic_digest_sha256"}
    )
    assert audit["semantic_digest_sha256"] == expected_digest


def test_source_native_eq120_certificate_is_recomputed_not_trusted(
    audit: dict[str, Any],
) -> None:
    check = audit["checks"]["Eq120_premise_binding"]
    ledger = check["independent_source_ledger"]
    validation = check["source_native_certificate_validation"]

    assert check["passed"] is True
    assert check["status"] == "EQ120_PREMISES_PROVED_ON_SOURCE_SLICE"
    assert ledger["raw_relation_count"] == 6
    assert len(ledger["pair_derivations"]) == 3
    assert ledger["dependency_closure"] == {
        "CPOBC": True,
        "source_nonsingularity": True,
        "MSR": False,
        "GC": False,
        "occurrence_identification": True,
    }
    assert all(record["verified"] is True for record in ledger["pair_derivations"])
    assert validation["passed"] is True
    assert validation["semantic_digest_sha256"] == (
        "77d11eff7d14d84182abbf1eb30732fe2b94855507f1826747ba878fadb8d6ca"
    )
    assert validation["independent_free_word_recomputation_passed"] is True
    assert validation["forbidden_semantic_dependencies_absent"] is True
    assert validation["selected_700_direct_ideal_membership_claimed"] is False


def test_missing_source_native_eq120_certificate_is_the_only_open_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    absent = "results/__test_absent_eq120_source_provenance.json"
    monkeypatch.setattr(audit_module, "EQ120_PROVENANCE_PATH", absent)

    payload = audit_module.audit_partial_slice_v041(ROOT)
    checks = payload["checks"]
    eq120 = checks["Eq120_premise_binding"]

    assert payload["verdict"] == audit_module.VERDICT_UNRESOLVED
    assert payload["passed"] is False
    assert eq120["passed"] is False
    assert eq120["Eq120_to_ratio_commutation_identity_verified"] is True
    assert eq120["literal_binding_passed"] is False
    assert eq120["literal_selected_700_matches"] == {
        "R2_R3": [],
        "R2_R4": [],
        "R3_R4": [],
    }
    assert eq120["source_native_certificate_hook"]["path"] == absent
    assert eq120["source_native_certificate_hook"]["required_raw_source_relation_count"] == 6
    assert all(
        checks[name]["passed"] is True
        for name in (
            "artifact_integrity",
            "CPOBC_pullback",
            "strong_GC_pullback",
            "inverse_and_nonsingularity",
            "chart_cover_and_QQ_certificates",
        )
    )


def test_tampered_source_native_certificate_is_invalid_not_proved(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    certificate = json.loads(
        (ROOT / audit_module.EQ120_PROVENANCE_PATH).read_text(encoding="utf-8")
    )
    certificate["pair_certificates"][0]["verified"] = False
    tampered = tmp_path / "tampered_eq120.json"
    tampered.write_text(json.dumps(certificate), encoding="utf-8")
    monkeypatch.setattr(audit_module, "EQ120_PROVENANCE_PATH", str(tampered))

    payload = audit_module.audit_partial_slice_v041(ROOT)

    assert payload["verdict"] == audit_module.VERDICT_INVALID
    assert payload["passed"] is False
    assert "semantic digest mismatch" in payload["failure"]
