from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import shutil
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts/extract_v042_paper1_witness_tables.py"
OUTPUT_PATH = ROOT / "results/v0.4.2_paper1_witness_tables.json"
SOURCE_PATHS = (
    "results/v0.4_weak_d2_classification.json",
    "results/v0.4.2_sr2v_baseline_observability.json",
    "tests/final_theory/test_weak_d2_v04_oracle.py",
)
OUTPUT_RAW_SHA256 = "7608f8f987352fd297ae4e5911a65e018700a5c187b3d60e7a0677f72e3700f7"
OUTPUT_SEMANTIC_SHA256 = "6e3aff10dcf855617973b3b83bece809f00ef39f9568471475e58c1ab5fca542"
ORBIT_IDS_SHA256 = "5ad9b8dd52a8dd241ef67cd4d447ef586b8ce3eeda2654a12f9ac6e25a57aaa9"
FAMILY_DIGESTS = {
    "transition_occurrences": "3c7f8db54832419d4caf7ba900130c606b4718bf1f4abef031564f50567a2a47",
    "CPOBC": "6b3d9459f1b4ec6dd0f26851b86a13f0a9b26b995fd1000f08077f35834a7596",
    "CPOBC_inverse_rewrites": ("9a7a5bf6f8a0e6dc1b8d1f5ac036c938702be46766a138036972a2635f05d2b9"),
    "GC": "e91d479bf9b110f6f45858bc9314392a52b484ce8c55e9519218920923918f7c",
    "MSR": "c5f8cc98a8135574c54e759f5b98862b4310de176c7585373c301e82b7a6ce33",
    "Eq113_QN": "b28ed83c3cabefb879f5a960ad13caaaf727dfa2d0f28c697a4451ea49289d8f",
    "Eq113_QN_PLUS_1": ("e825676a97e6d93128d84b731b5a78da6f1d28058e405e69984096e28ab00a7f"),
    "Eq139_PRINTED_STRICT": ("884a5fe79b0c390de7d81c09da779ac0e5f9f6a3696d3b28a9d26511f95764ee"),
    "Eq139_EQ145_COMPLETED": ("ef017a3cfa9cb8959e0aa80d4ef987a69f59bee34ccdf9b053a454021470261b"),
    "Q_commutators": ("8cfb219610ef5eff61fd359ce41bd68e03b848deac2706ea32474150ab15b5cb"),
}
FAMILY_COUNTS = {
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


def _load_extractor() -> ModuleType:
    specification = importlib.util.spec_from_file_location(
        "test_extract_v042_paper1_witness_tables_module",
        SCRIPT_PATH,
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


EXTRACTOR = _load_extractor()


def _fixture_root(tmp_path: Path) -> Path:
    repository_root = tmp_path / "fixture-repository"
    for relative_path in SOURCE_PATHS:
        destination = repository_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative_path, destination)
    return repository_root


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _rebind_raw(
    monkeypatch: pytest.MonkeyPatch,
    repository_root: Path,
    relative_path: str,
) -> None:
    specifications = copy.deepcopy(EXTRACTOR.SOURCE_SPECS)
    specifications[relative_path]["raw_sha256"] = hashlib.sha256(
        (repository_root / relative_path).read_bytes()
    ).hexdigest()
    monkeypatch.setattr(EXTRACTOR, "SOURCE_SPECS", specifications)


def _rebind_mutated_weak_chain(
    monkeypatch: pytest.MonkeyPatch,
    repository_root: Path,
) -> None:
    """Simulate an explicit weak-ledger and dependent-audit authority rebind."""

    weak_path = repository_root / SOURCE_PATHS[0]
    weak_digest = hashlib.sha256(weak_path.read_bytes()).hexdigest()
    observability_path = repository_root / SOURCE_PATHS[1]
    observability = _read_json(observability_path)
    observability["input_artifacts"][SOURCE_PATHS[0]] = weak_digest
    observability["semantic_digest_sha256"] = EXTRACTOR.semantic_digest(observability)
    _write_json(observability_path, observability)

    specifications = copy.deepcopy(EXTRACTOR.SOURCE_SPECS)
    specifications[SOURCE_PATHS[0]]["raw_sha256"] = weak_digest
    specifications[SOURCE_PATHS[1]]["raw_sha256"] = hashlib.sha256(
        observability_path.read_bytes()
    ).hexdigest()
    specifications[SOURCE_PATHS[1]]["semantic_sha256"] = observability["semantic_digest_sha256"]
    monkeypatch.setattr(EXTRACTOR, "SOURCE_SPECS", specifications)


def _family_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    families = payload["family_census"]["families"]
    return {family["family"]: family for family in families}


def test_tracked_output_is_exact_regeneration_with_stable_order_and_digests() -> None:
    first = EXTRACTOR.build_payload(ROOT)
    second = EXTRACTOR.build_payload(ROOT)
    tracked_raw = OUTPUT_PATH.read_bytes()
    tracked = _read_json(OUTPUT_PATH)

    assert first == second == tracked
    assert tracked_raw == EXTRACTOR.output_bytes(first)
    assert hashlib.sha256(tracked_raw).hexdigest() == OUTPUT_RAW_SHA256
    assert first["semantic_digest_sha256"] == OUTPUT_SEMANTIC_SHA256
    assert EXTRACTOR.semantic_digest(first) == OUTPUT_SEMANTIC_SHA256

    transition_tables = first["transition_tables"]
    assert transition_tables["occurrence_count"] == 165
    assert transition_tables["orbit_count"] == 131
    assert transition_tables["orbit_ids_sha256"] == ORBIT_IDS_SHA256
    occurrences = transition_tables["occurrence_map"]
    orbits = transition_tables["orbit_table"]
    assert occurrences == sorted(occurrences, key=lambda record: record["occurrence_id"])
    assert orbits == sorted(orbits, key=lambda record: record["orbit_id"])
    assert all("precursor_code" in record for record in occurrences)
    assert all("precursor_code" not in record for record in orbits)
    assert len({record["occurrence_id"] for record in occurrences}) == 165
    assert len({record["orbit_id"] for record in orbits}) == 131

    family_map = _family_map(first)
    assert set(family_map) == set(FAMILY_COUNTS)
    all_ids: list[str] = []
    for family, expected_count in FAMILY_COUNTS.items():
        record = family_map[family]
        assert record["record_count"] == expected_count
        assert record["natural_ids"] == sorted(record["natural_ids"])
        assert len(set(record["natural_ids"])) == expected_count
        assert record["natural_ids_sha256"] == FAMILY_DIGESTS[family]
        assert (
            hashlib.sha256(EXTRACTOR.canonical_json_bytes(record["natural_ids"])).hexdigest()
            == FAMILY_DIGESTS[family]
        )
        all_ids.extend(record["natural_ids"])
    assert len(all_ids) == 3283
    assert len(set(all_ids)) == 3283
    assert first["family_census"]["derived_total_top_level_records"] == 3283
    assert first["family_census"]["expected_total_top_level_records"] == 3283


def test_exact_formulas_q_commutators_rank_and_representatives() -> None:
    payload = _read_json(OUTPUT_PATH)
    assert payload["formulas"] == {
        "transition_matrix": "A_e=[[2^(w_e-m_e)/2^n,b_e],[0,1]]",
        "diagonal_entry": "2^(w_e-m_e)/2^n",
        "b_e": "4/2^n if the precursor is empty; 0 otherwise",
        "gregarious_transition_definition": "precursor_code=0",
        "w_e": "precursor cardinality",
        "m_e": "number of maximal precursor elements",
        "Q_n": "[[2^-n,4*2^-n],[0,1]]",
        "source_transition_formula": (
            "A_e=[[2^(w_e-m_e)/2^n, (4/2^n if precursor is empty else 0)],[0,1]]"
        ),
    }
    assert payload["Q_inventory"] == [
        {
            "stage": 1,
            "matrix": [["1/2", "2"], ["0", "1"]],
            "determinant": "1/2",
            "nonsingular": True,
        },
        {
            "stage": 2,
            "matrix": [["1/4", "1"], ["0", "1"]],
            "determinant": "1/4",
            "nonsingular": True,
        },
        {
            "stage": 3,
            "matrix": [["1/8", "1/2"], ["0", "1"]],
            "determinant": "1/8",
            "nonsingular": True,
        },
        {
            "stage": 4,
            "matrix": [["1/16", "1/4"], ["0", "1"]],
            "determinant": "1/16",
            "nonsingular": True,
        },
        {
            "stage": 5,
            "matrix": [["1/32", "1/8"], ["0", "1"]],
            "determinant": "1/32",
            "nonsingular": True,
        },
    ]
    commutators = payload["commutators"]
    assert commutators["operator_nonzero_count"] == 6
    assert commutators["reachable_visible_count"] == 0
    assert [record["commutator"] for record in commutators["records"]] == [
        [["0", "1"], ["0", "0"]],
        [["0", "3/2"], ["0", "0"]],
        [["0", "7/4"], ["0", "0"]],
        [["0", "1/2"], ["0", "0"]],
        [["0", "3/4"], ["0", "0"]],
        [["0", "1/4"], ["0", "0"]],
    ]

    rank = payload["reachable_rank_one_evidence"]
    assert (rank["path_count"], rank["endpoint_count"], rank["reachable_span_rank"]) == (
        407,
        87,
        1,
    )
    assert rank["endpoint_stage_counts"] == {"1": 1, "2": 2, "3": 5, "4": 16, "5": 63}
    assert rank["rank_basis_endpoint"]["endpoint_causet_id"] == "p1-0"
    assert rank["rank_basis_endpoint"]["state"] == ["1", "0"]
    assert rank["all_states_are_rational_multiples_of_Omega"] is True
    assert rank["operator_noncommutative"] is True
    assert rank["reachable_visible"] is False

    representatives = payload["representative_residuals"]
    assert representatives["fixed_vector_GC"] == {
        "endpoint_causet_id": "p3-002",
        "left_path_id": "lgc-path-73192a6770fa82828f12",
        "right_path_id": "lgc-path-fc1eafd06aa0360d6535",
        "operator_residual": [["0", "-1/2"], ["0", "0"]],
        "action_on_Omega": ["0", "0"],
    }
    msr = representatives["reachable_state_MSR"]
    assert msr["constraint_id"] == "msr:p1-0"
    assert msr["source_state"] == ["1", "0"]
    assert msr["operator_residual"] == [["0", "2"], ["0", "1"]]
    assert msr["action_on_source_state"] == ["0", "0"]
    assert msr["reachable_state_residual_on_omega_ray"] == ["0", "0"]

    bindings = {binding["path"]: binding for binding in payload["source_bindings"]}
    assert "semantic_digest_sha256" not in bindings[SOURCE_PATHS[0]]
    assert "semantic_digest_sha256" in bindings[SOURCE_PATHS[1]]
    assert "semantic_digest_sha256" not in bindings[SOURCE_PATHS[2]]


@pytest.mark.parametrize("relative_path", SOURCE_PATHS)
def test_fail_closed_on_any_input_raw_drift(tmp_path: Path, relative_path: str) -> None:
    repository_root = _fixture_root(tmp_path)
    with (repository_root / relative_path).open("ab") as handle:
        handle.write(b" ")
    with pytest.raises(EXTRACTOR.ExtractionError, match="raw SHA-256 drift"):
        EXTRACTOR.build_payload(repository_root)


@pytest.mark.parametrize(
    ("field", "mutated"),
    [
        ("schema_version", "unexpected-schema"),
        ("passed", False),
        ("verdict", "UNAUTHORIZED_VERDICT"),
        ("gates", {}),
    ],
)
def test_fail_closed_on_schema_passed_verdict_or_gate_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    mutated: object,
) -> None:
    repository_root = _fixture_root(tmp_path)
    weak_path = repository_root / SOURCE_PATHS[0]
    weak = _read_json(weak_path)
    weak[field] = mutated
    _write_json(weak_path, weak)
    _rebind_raw(monkeypatch, repository_root, SOURCE_PATHS[0])
    with pytest.raises(EXTRACTOR.ExtractionError, match="mismatch"):
        EXTRACTOR.build_payload(repository_root)


def test_fail_closed_on_observability_semantic_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_root = _fixture_root(tmp_path)
    observability_path = repository_root / SOURCE_PATHS[1]
    observability = _read_json(observability_path)
    observability["semantic_digest_sha256"] = "0" * 64
    _write_json(observability_path, observability)
    _rebind_raw(monkeypatch, repository_root, SOURCE_PATHS[1])
    with pytest.raises(EXTRACTOR.ExtractionError, match="recorded semantic digest"):
        EXTRACTOR.build_payload(repository_root)


def test_fail_closed_on_count_drift_after_explicit_raw_rebinding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_root = _fixture_root(tmp_path)
    weak_path = repository_root / SOURCE_PATHS[0]
    weak = _read_json(weak_path)
    weak["direct_substitution"]["CPOBC"]["records"].pop()
    _write_json(weak_path, weak)
    _rebind_mutated_weak_chain(monkeypatch, repository_root)
    with pytest.raises(EXTRACTOR.ExtractionError, match="CPOBC record count mismatch"):
        EXTRACTOR.build_payload(repository_root)


def test_fail_closed_on_duplicate_natural_id_after_explicit_raw_rebinding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_root = _fixture_root(tmp_path)
    weak_path = repository_root / SOURCE_PATHS[0]
    weak = _read_json(weak_path)
    records = weak["direct_substitution"]["CPOBC"]["records"]
    records[1] = copy.deepcopy(records[0])
    _write_json(weak_path, weak)
    _rebind_mutated_weak_chain(monkeypatch, repository_root)
    with pytest.raises(EXTRACTOR.ExtractionError, match="duplicate or colliding CPOBC"):
        EXTRACTOR.build_payload(repository_root)


def test_fail_closed_on_orbit_invariant_drift_after_explicit_raw_rebinding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_root = _fixture_root(tmp_path)
    weak_path = repository_root / SOURCE_PATHS[0]
    weak = _read_json(weak_path)
    records = weak["transition_assignment"]["records"]
    assert records[0]["stage"] != records[-1]["stage"]
    records[0]["orbit_id"] = records[-1]["orbit_id"]
    _write_json(weak_path, weak)
    _rebind_mutated_weak_chain(monkeypatch, repository_root)
    with pytest.raises(EXTRACTOR.ExtractionError, match="orbit invariant drift"):
        EXTRACTOR.build_payload(repository_root)


def test_fail_closed_on_representative_residual_drift_after_raw_rebinding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_root = _fixture_root(tmp_path)
    weak_path = repository_root / SOURCE_PATHS[0]
    weak = _read_json(weak_path)
    records = weak["direct_substitution"]["GC"]["records"]
    representative = next(
        record
        for record in records
        if record["endpoint_causet_id"] == "p3-002"
        and record["left_path_id"] == "lgc-path-73192a6770fa82828f12"
        and record["right_path_id"] == "lgc-path-fc1eafd06aa0360d6535"
    )
    representative["operator_residual"][0][1] = "-3/4"
    _write_json(weak_path, weak)
    _rebind_mutated_weak_chain(monkeypatch, repository_root)
    with pytest.raises(EXTRACTOR.ExtractionError, match="weak/observable GC"):
        EXTRACTOR.build_payload(repository_root)


@pytest.mark.parametrize("mutation", ["formula", "Q", "commutator"])
def test_fail_closed_on_formula_q_or_commutator_drift_after_raw_rebinding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    repository_root = _fixture_root(tmp_path)
    weak_path = repository_root / SOURCE_PATHS[0]
    weak = _read_json(weak_path)
    if mutation == "formula":
        weak["witness_definition"]["transition_formula"] = "drifted formula"
    elif mutation == "Q":
        weak["Q_inventory"][0]["matrix"][0][1] = "3"
    else:
        weak["noncommutativity"]["records"][0]["commutator"][0][1] = "2"
    _write_json(weak_path, weak)
    _rebind_mutated_weak_chain(monkeypatch, repository_root)
    with pytest.raises(EXTRACTOR.ExtractionError, match="mismatch|formula"):
        EXTRACTOR.build_payload(repository_root)


def test_write_is_atomic_idempotent_and_confined_to_a_temp_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_authority_before = OUTPUT_PATH.read_bytes()
    repository_root = _fixture_root(tmp_path)
    destination = repository_root / EXTRACTOR.OUTPUT_PATH
    replace_calls: list[tuple[Path, Path]] = []
    real_replace = os.replace

    def replace(
        source: str | bytes | os.PathLike[str], target: str | bytes | os.PathLike[str]
    ) -> None:
        source_path = Path(os.fsdecode(source))
        target_path = Path(os.fsdecode(target))
        replace_calls.append((source_path, target_path))
        real_replace(source, target)

    monkeypatch.setattr(EXTRACTOR.os, "replace", replace)
    first = EXTRACTOR.run(repository_root, write=True)
    first_raw = destination.read_bytes()
    second = EXTRACTOR.run(repository_root, write=True)
    assert first == second
    assert destination.read_bytes() == first_raw == EXTRACTOR.output_bytes(first)
    assert len(replace_calls) == 2
    assert all(source.parent == destination.parent for source, _target in replace_calls)
    assert all(target == destination for _source, target in replace_calls)
    assert not list(destination.parent.glob(f".{destination.name}.*.tmp"))

    EXTRACTOR.run(repository_root, write=False)
    assert OUTPUT_PATH.read_bytes() == repository_authority_before


def test_check_rejects_semantically_equal_but_noncanonical_tracked_bytes(tmp_path: Path) -> None:
    repository_root = _fixture_root(tmp_path)
    payload = EXTRACTOR.run(repository_root, write=True)
    destination = repository_root / EXTRACTOR.OUTPUT_PATH
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(EXTRACTOR.ExtractionError, match="bytes are not"):
        EXTRACTOR.run(repository_root, write=False)
