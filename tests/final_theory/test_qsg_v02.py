from __future__ import annotations

from universe_lab.final_theory.qsg_algebra import (
    causal_past_pauli_reference_audit,
    non_time_ordered_reference_audit,
    qsg_algebra_benchmark,
    time_ordered_reference_audit,
)


def test_time_ordered_base_identity_is_exact() -> None:
    result = time_ordered_reference_audit()
    assert result["identity_exact"]
    assert result["noncommuting_probe_rejected"]


def test_non_time_ordered_n2_rejects_noncommuting_probe() -> None:
    result = non_time_ordered_reference_audit()
    assert result["noncommuting_probe_rejected"]
    assert result["commuting_probe_passes"]


def test_pauli_obstructions_are_exact() -> None:
    result = causal_past_pauli_reference_audit()
    assert result["three_distinct_pauli"]["necessary_relation_violated"]
    assert result["two_pauli_path_probe"]["rejected_exactly"]
    assert result["reproduction_status"] == "PARTIAL_EXACT_REPRODUCTION"


def test_bounded_search_is_not_promoted_to_no_go_or_discovery() -> None:
    result = qsg_algebra_benchmark()
    assert result["qsg_algebra_status"] == "QSG_SEARCH_INCONCLUSIVE"
    assert not result["new_search"]["noncommutative_representation_found"]
    assert "does not justify QSG_NO_REPRESENTATION" in result["prohibited_inference"]
