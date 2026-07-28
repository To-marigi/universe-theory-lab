from universe_lab.final_theory.certification_v031 import (
    kraus_track_boundary,
    noncommutative_extension_boundary,
    noncommutative_qsg_certification,
)


def test_physical_phase_stops_without_full_representation() -> None:
    search = {
        "summary": {
            "noncommutative_representation_found": False,
            "full_compiled_relation_certificate_count": 0,
        }
    }
    result = noncommutative_qsg_certification(search)
    assert result["verdict"] == "NOT_EXECUTED_NO_REPRESENTATION"
    assert not result["kraus_channel_conversion_attempted"]
    assert not result["vector_measure_constructed"]


def test_extension_is_not_assessed_without_representation() -> None:
    qsg = noncommutative_qsg_certification({"summary": {}})
    result = noncommutative_extension_boundary(qsg)
    assert result["verdict"] == "NONCOMMUTATIVE_EXTENSION_NOT_ASSESSED"
    assert not result["finite_n_boundedness_is_infinite_proof"]
    assert result["prohibited_verdict"] == "INFINITE_EXTENSION_PASS"


def test_kraus_track_remains_a_formulation_mismatch() -> None:
    result = kraus_track_boundary()
    assert result["verdict"] == "FORMULATION_MISMATCH"
    assert not result["new_channel_bell_definition_introduced"]
    assert len(result["distinct_notions"]) == 4
